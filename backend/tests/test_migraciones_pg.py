"""Mismas comprobaciones de migraciones, sobre PostgreSQL DESECHABLE.

Se salta por defecto. Para ejecutarla: MIGRACIONES_PG_URL=postgresql+psycopg2://…
apuntando a una base de PRUEBA (su nombre debe contener "desech" o "tmp").
La prueba borra el esquema público de esa base: por eso la guarda de nombre.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")

import pytest
from sqlalchemy import create_engine, inspect, text, select
from sqlalchemy.engine.url import make_url

import app.database.migrations as migrations
from app.database.base import Base
import app.models  # noqa: F401

URL = os.environ.get("MIGRACIONES_PG_URL")
pytestmark = pytest.mark.skipif(not URL, reason="MIGRACIONES_PG_URL no definida (base desechable)")


@pytest.fixture()
def engine():
    eng = create_engine(URL)
    nombre = make_url(URL).database or ""
    if "desech" not in nombre and "tmp" not in nombre:
        pytest.fail("Guarda: la base de MIGRACIONES_PG_URL debe llamarse con 'desech' o 'tmp'.")
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        # Igual que el arranque: pgvector antes de create_all.
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    yield eng
    eng.dispose()


def _esquema_viejo_pg(engine):
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY, google_id VARCHAR(255), email VARCHAR(255) NOT NULL,
                name VARCHAR(255), role VARCHAR(20) NOT NULL, profile_image VARCHAR(500),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())"""))
        conn.execute(text("""
            CREATE TABLE questions (
                id SERIAL PRIMARY KEY, subtopic_id INTEGER NOT NULL, prompt VARCHAR(500) NOT NULL,
                options JSON NOT NULL, correct_index INTEGER NOT NULL, explanation TEXT,
                "order" INTEGER NOT NULL DEFAULT 0)"""))
        # Los cursos ya existían antes de las migraciones versionadas.
        from app.models.course import Course
        from app.models.content import Topic

        Course.__table__.create(conn, checkfirst=True)
        Topic.__table__.create(conn, checkfirst=True)
        conn.execute(text("""
            CREATE TABLE ai_queries (
                id SERIAL PRIMARY KEY, user_id INTEGER, subtopic_id INTEGER,
                question_original TEXT, respuesta TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW())"""))
        conn.execute(text(
            "INSERT INTO users (email, name, role) VALUES ('a@example.com','A','STUDENT'),('b@example.com','B','TEACHER')"))
        conn.execute(text(
            "INSERT INTO questions (subtopic_id, prompt, options, correct_index, explanation, \"order\") "
            "VALUES (10,'¿Pregunta uno?','[\"a\",\"b\",\"c\",\"d\"]',0,'e1',1),"
            "(10,'¿Pregunta dos?','[\"a\",\"b\",\"c\",\"d\"]',1,'e2',2)"))
        conn.execute(text(
            "INSERT INTO ai_queries (user_id, subtopic_id, question_original, respuesta) "
            "VALUES (1, 10, 'consulta previa', 'respuesta previa')"))


def test_pg_esquema_viejo_llega_al_actual_sin_perder_filas(engine):
    _esquema_viejo_pg(engine)
    Base.metadata.create_all(engine)
    aplicadas = migrations.run_migrations(engine)

    assert aplicadas == [m.version for m in migrations.MIGRATIONS]
    cols_users = {c["name"] for c in inspect(engine).get_columns("users")}
    cols_q = {c["name"] for c in inspect(engine).get_columns("questions")}
    assert {"country", "age"} <= cols_users
    assert {"source", "status", "created_by", "created_at"} <= cols_q
    assert "question_normalizada" in {c["name"] for c in inspect(engine).get_columns("ai_queries")}

    with engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM users")) == 2
        assert conn.scalar(text("SELECT COUNT(*) FROM questions")) == 2
        assert conn.scalar(text("SELECT respuesta FROM ai_queries")) == "respuesta previa"
        assert conn.execute(text("SELECT source, status FROM questions ORDER BY id")).all() == [
            ("official", "approved"), ("official", "approved")]
        # Índice nuevo del tope diario.
        assert "ix_ai_queries_user_created" in {i["name"] for i in inspect(engine).get_indexes("ai_queries")}

    # Segundo arranque: nada pendiente.
    assert migrations.run_migrations(engine) == []


def test_pg_registro_y_bloqueo_no_quedan_colgados(engine):
    """Dos llamadas seguidas no se bloquean (el advisory lock se libera) y registran bien."""
    Base.metadata.create_all(engine)
    migrations.run_migrations(engine)
    migrations.run_migrations(engine)
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM schema_migrations")) == len(migrations.MIGRATIONS)


def test_pg_upgrade_v3_preserves_users_and_feedback_roundtrip(engine, monkeypatch):
    from uuid import uuid4
    from sqlalchemy.orm import Session
    from app.models.feedback import Feedback, UsabilityEvaluation

    _esquema_viejo_pg(engine)
    current = migrations.MIGRATIONS
    with monkeypatch.context() as old:
        old.setattr(migrations, "MIGRATIONS", current[:3])
        assert migrations.run_migrations(engine) == [1, 2, 3]
    assert migrations.run_migrations(engine) == [m.version for m in current if m.version > 3]
    with Session(engine) as db:
        db.add(Feedback(user_id=1, tipo="Sugerencia", categoria="Otro", comentario="Ejemplo sintético", pagina="/dashboard"))
        db.add(UsabilityEvaluation(user_id=1, submission_id=str(uuid4()), version="insoft-nielsen-v1",
                                  respuestas={f"h{i:02d}": None if i == 10 else 4 for i in range(1, 11)},
                                  dispositivo="Teléfono", comentario="Ejemplo sintético", pagina="/dashboard"))
        db.commit()
        assert db.scalar(select(UsabilityEvaluation)).respuestas['h10'] is None
    assert migrations.run_migrations(engine) == []
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT COUNT(*) FROM users")) == 2
        assert conn.scalar(text("SELECT COUNT(*) FROM feedback")) == 1
        assert conn.scalar(text("SELECT COUNT(*) FROM usability_evaluations")) == 1


def test_pg_varchar_session_upgrades_to_uuid_and_conversation_roundtrips(engine, monkeypatch):
    """Reproduce la base real: v7 aplicada, session_id VARCHAR y filtros ORM UUID."""
    from uuid import uuid4
    from sqlalchemy import Uuid
    from sqlalchemy.orm import Session
    from app.repositories import ai_query_repository as queries

    _esquema_viejo_pg(engine)
    current = migrations.MIGRATIONS
    with monkeypatch.context() as old:
        old.setattr(migrations, "MIGRATIONS", current[:7])
        migrations.run_migrations(engine)
    session_id = uuid4()
    with engine.begin() as conn:
        conn.execute(text("UPDATE ai_queries SET session_id=:sid, status='ok' WHERE id=1"), {"sid": str(session_id)})
    assert not isinstance(next(c for c in inspect(engine).get_columns("ai_queries") if c["name"] == "session_id")["type"], Uuid)

    assert migrations.run_migrations(engine) == [8]
    assert isinstance(next(c for c in inspect(engine).get_columns("ai_queries") if c["name"] == "session_id")["type"], Uuid)
    with Session(engine) as db:
        history, count = queries.get_by_user(db, 1, session_id=session_id)
        assert count == 1
        assert history[0].respuesta == "respuesta previa"
        assert history[0].session_id == session_id
        assert len(queries.conversation(db, 1, session_id, None)) == 1
        saved = queries.create(db, user_id=1, question_original="Seguimiento", respuesta="Respuesta nueva",
                               session_id=session_id, status="ok")
        assert saved.session_id == session_id
        assert len(queries.conversation(db, 1, session_id, None)) == 2
    assert migrations.run_migrations(engine) == []


def test_pg_invalid_legacy_session_does_not_lose_data_or_mark_migration(engine, monkeypatch):
    _esquema_viejo_pg(engine)
    current = migrations.MIGRATIONS
    with monkeypatch.context() as old:
        old.setattr(migrations, "MIGRATIONS", current[:7])
        migrations.run_migrations(engine)
    with engine.begin() as conn:
        conn.execute(text("UPDATE ai_queries SET session_id='sesion-legada-invalida' WHERE id=1"))
    with pytest.raises(RuntimeError, match="identificadores no UUID"):
        migrations.run_migrations(engine)
    with engine.connect() as conn:
        assert conn.scalar(text("SELECT session_id FROM ai_queries WHERE id=1")) == "sesion-legada-invalida"
        assert conn.scalar(text("SELECT respuesta FROM ai_queries WHERE id=1")) == "respuesta previa"
        assert conn.scalar(text("SELECT COUNT(*) FROM schema_migrations WHERE version=8")) == 0
