"""Migraciones versionadas (schema_migrations) sobre SQLite desechable.

Cubren: base nueva, esquema viejo con datos -> actual (sin perder filas),
adopción de una base existente con línea base, idempotencia y que una
migración fallida no se registra (se reintenta en el siguiente arranque).
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")

import pytest
from sqlalchemy import create_engine, inspect, text

import app.database.migrations as migrations
from app.database.base import Base
import app.models  # noqa: F401  (registra los modelos en la metadata)


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'mig.db'}")


def _versions(engine):
    with engine.connect() as conn:
        return [r[0] for r in conn.execute(text("SELECT version FROM schema_migrations ORDER BY version"))]


def _columns(engine, table):
    return {c["name"] for c in inspect(engine).get_columns(table)}


def _esquema_viejo(engine):
    """Esquema anterior a la versión con migraciones: sin columnas nuevas ni question_answers."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                google_id VARCHAR(255),
                email VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                role VARCHAR(20) NOT NULL,
                profile_image VARCHAR(500),
                created_at TIMESTAMP
            )"""))
        conn.execute(text("""
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY,
                subtopic_id INTEGER NOT NULL,
                prompt VARCHAR(500) NOT NULL,
                options JSON NOT NULL,
                correct_index INTEGER NOT NULL,
                explanation TEXT,
                "order" INTEGER NOT NULL DEFAULT 0
            )"""))
        conn.execute(text("""
            CREATE TABLE ai_queries (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                subtopic_id INTEGER,
                question_original TEXT,
                respuesta TEXT,
                created_at TIMESTAMP
            )"""))
        conn.execute(text(
            "INSERT INTO users (id, email, name, role) VALUES (1, 'a@example.com', 'A', 'STUDENT'), "
            "(2, 'b@example.com', 'B', 'TEACHER')"
        ))
        conn.execute(text(
            "INSERT INTO questions (id, subtopic_id, prompt, options, correct_index, explanation, \"order\") "
            "VALUES (1, 10, '¿Pregunta uno?', '[\"a\",\"b\",\"c\",\"d\"]', 0, 'e1', 1), "
            "(2, 10, '¿Pregunta dos?', '[\"a\",\"b\",\"c\",\"d\"]', 1, 'e2', 2)"
        ))
        conn.execute(text(
            "INSERT INTO ai_queries (id, user_id, subtopic_id, question_original, respuesta) "
            "VALUES (1, 1, 10, 'consulta previa', 'respuesta previa')"
        ))


def test_base_nueva_aplica_todas_las_migraciones_una_sola_vez(tmp_path):
    engine = _engine(tmp_path)
    Base.metadata.create_all(engine)

    aplicadas = migrations.run_migrations(engine)
    assert aplicadas == [m.version for m in migrations.MIGRATIONS]
    assert _versions(engine) == [m.version for m in migrations.MIGRATIONS]

    # Segundo arranque: nada pendiente, nada se duplica.
    assert migrations.run_migrations(engine) == []
    assert _versions(engine) == [m.version for m in migrations.MIGRATIONS]


def test_esquema_viejo_con_datos_llega_al_actual_sin_perder_filas(tmp_path):
    engine = _engine(tmp_path)
    _esquema_viejo(engine)
    Base.metadata.create_all(engine)  # como en el arranque: crea lo que falte
    migrations.run_migrations(engine)

    # Columnas nuevas presentes.
    assert {"country", "age"} <= _columns(engine, "users")
    assert {"source", "status", "created_by", "created_at"} <= _columns(engine, "questions")
    assert {"session_id", "model_used", "status", "response_time_ms", "question_normalizada"} <= _columns(engine, "ai_queries")

    with engine.connect() as conn:
        # Ninguna fila se pierde.
        assert conn.scalar(text("SELECT COUNT(*) FROM users")) == 2
        assert conn.scalar(text("SELECT COUNT(*) FROM questions")) == 2
        assert conn.scalar(text("SELECT COUNT(*) FROM ai_queries")) == 1
        # Las preguntas previas quedan como oficiales aprobadas.
        rows = conn.execute(text("SELECT source, status FROM questions ORDER BY id")).all()
        assert rows == [("official", "approved"), ("official", "approved")]
        # El contenido de las consultas previas no cambia.
        assert conn.scalar(text("SELECT respuesta FROM ai_queries WHERE id = 1")) == "respuesta previa"

    assert "question_answers" in inspect(engine).get_table_names()
    assert _versions(engine) == [m.version for m in migrations.MIGRATIONS]


def test_adopta_base_existente_con_linea_base_sin_perder_datos(tmp_path):
    engine = _engine(tmp_path)
    _esquema_viejo(engine)
    # No existe schema_migrations: es una base previa a este sistema.
    assert "schema_migrations" not in inspect(engine).get_table_names()

    migrations.run_migrations(engine)

    with engine.connect() as conn:
        nombre = conn.scalar(text("SELECT name FROM schema_migrations WHERE version = 1"))
        assert nombre == "linea_base"
        assert conn.scalar(text("SELECT COUNT(*) FROM questions")) == 2


def test_actualiza_base_con_versiones_1_y_2_registradas(tmp_path, monkeypatch):
    engine = _engine(tmp_path)
    _esquema_viejo(engine)
    all_migrations = migrations.MIGRATIONS
    with monkeypatch.context() as previous:
        previous.setattr(migrations, "MIGRATIONS", all_migrations[:2])
        assert migrations.run_migrations(engine) == [1, 2]
    assert migrations.run_migrations(engine) == [m.version for m in all_migrations if m.version > 2]
    with engine.begin() as conn:
        conn.execute(text("UPDATE ai_queries SET question_normalizada='pregunta normalizada' WHERE id=1"))
        assert conn.scalar(text("SELECT respuesta FROM ai_queries WHERE id=1")) == "respuesta previa"
        assert conn.scalar(text("SELECT question_normalizada FROM ai_queries WHERE id=1")) == "pregunta normalizada"
    assert migrations.run_migrations(engine) == []


def test_migracion_fallida_no_se_registra_y_se_reintenta(tmp_path, monkeypatch):
    engine = _engine(tmp_path)
    Base.metadata.create_all(engine)
    fallos = {"n": 0}

    def _falla(conn):
        fallos["n"] += 1
        if fallos["n"] == 1:
            raise RuntimeError("fallo simulado")

    extra = migrations.Migration(99, "migracion_de_prueba", _falla)
    monkeypatch.setattr(migrations, "MIGRATIONS", [*migrations.MIGRATIONS, extra])

    with pytest.raises(RuntimeError):
        migrations.run_migrations(engine)
    assert 99 not in _versions(engine)

    # El siguiente arranque reintenta y la registra.
    assert migrations.run_migrations(engine) == [99]
    assert 99 in _versions(engine)


def test_versiones_son_estrictamente_crecientes_y_sin_huecos():
    versiones = [m.version for m in migrations.MIGRATIONS]
    assert versiones == list(range(1, len(versiones) + 1))
