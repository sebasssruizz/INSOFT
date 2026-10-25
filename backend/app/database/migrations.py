"""Migraciones versionadas (sin Alembic).

Cada migración es un paso numerado (`MIGRATIONS`) con un nombre y una función
IDEMPOTENTE que recibe una conexión dentro de una transacción. Al arrancar,
`run_migrations()`:

1. Crea la tabla `schema_migrations` si no existe.
2. Toma un bloqueo de asesor en PostgreSQL (`pg_advisory_lock`) para que dos
   procesos que arrancan a la vez no migren en paralelo.
3. Ejecuta, en orden, las migraciones que no aparecen registradas, y registra
   cada una al terminar con éxito (si una falla, no se registra y se reintenta
   en el siguiente arranque).

ADOPCIÓN DE BASES EXISTENTES: si la base ya tenía tablas (creadas por la versión
anterior, con `create_all` y los `ALTER` sueltos) y todavía no existe
`schema_migrations`, la migración 1 se ejecuta igual (es idempotente y sobre un
esquema al día no cambia nada) y se registra como "linea_base (adoptada)".

REGLAS: las migraciones son aditivas. Nunca borran tablas, columnas ni datos.
Cómo añadir una migración: ver docs/database/MIGRACIONES.md.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from sqlalchemy import Connection, Engine, inspect, text

from app.database.session import ddl_engine

logger = logging.getLogger(__name__)

# Clave del bloqueo de asesor de PostgreSQL (constante fija de INSOFT).
_ADVISORY_LOCK_KEY = 7142001

# (tabla, columna) -> definición SQL de la columna
NEW_COLUMNS = {
    ("users", "country"): "VARCHAR(120)",
    ("users", "age"): "INTEGER",
    # Procedencia/ciclo de vida de preguntas (banco del profesor + IA).
    ("questions", "source"): "VARCHAR(20) NOT NULL DEFAULT 'official'",
    ("questions", "status"): "VARCHAR(20) NOT NULL DEFAULT 'approved'",
    ("questions", "created_by"): "INTEGER",
    # Sesión/modelo/tiempo de las consultas al asistente (stats de IA).
    ("ai_queries", "session_id"): "VARCHAR(36)",
    ("ai_queries", "model_used"): "VARCHAR",
    ("ai_queries", "status"): "VARCHAR(20)",
    ("ai_queries", "response_time_ms"): "INTEGER",
    # Fecha de creación de preguntas (tope diario de práctica por subtema).
    ("questions", "created_at"): "TIMESTAMPTZ_NOT_NULL_NOW",
}

# Índices de la línea base: (nombre, SQL). Idempotentes vía chequeo previo.
NEW_INDEXES = {
    "ix_questions_subtopic_status": ("questions", "CREATE INDEX ix_questions_subtopic_status ON questions (subtopic_id, status)"),
    "ix_ai_queries_session_id": ("ai_queries", "CREATE INDEX ix_ai_queries_session_id ON ai_queries (session_id)"),
    "ix_question_answers_user_subtopic": ("question_answers", "CREATE INDEX ix_question_answers_user_subtopic ON question_answers (user_id, subtopic_id)"),
    "ix_question_answers_question": ("question_answers", "CREATE INDEX ix_question_answers_question ON question_answers (question_id)"),
}

Step = Callable[[Connection], None]


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Step


# ── Migración 1: línea base (todo el esquema que existía antes de versionar) ──


def ensure_pgvector_extension() -> None:
    """Habilita pgvector. Debe ejecutarse ANTES de create_all (columnas `vector`)."""
    if ddl_engine.dialect.name != "postgresql":
        return
    with ddl_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def _linea_base(conn: Connection) -> None:
    dialect = conn.dialect.name
    existing_tables = set(inspect(conn).get_table_names())

    # Tabla de respuestas de quiz (idempotente: solo si faltan sus tablas base).
    if "question_answers" not in existing_tables and {"users", "questions"} <= existing_tables:
        if dialect == "postgresql":
            pk = "SERIAL PRIMARY KEY"
            answered_at = "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
        else:
            pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
            answered_at = "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
        conn.execute(text(f"""
            CREATE TABLE question_answers (
                id {pk},
                user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
                question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
                subtopic_id INTEGER NOT NULL,
                attempt_id VARCHAR(36) NOT NULL,
                selected_index INTEGER NOT NULL,
                is_correct BOOLEAN NOT NULL,
                answered_at {answered_at},
                CONSTRAINT uq_attempt_question UNIQUE (attempt_id, question_id)
            )
        """))
        existing_tables = set(inspect(conn).get_table_names())

    inspector = inspect(conn)
    for (table, column), ddl in NEW_COLUMNS.items():
        if table not in existing_tables:
            continue
        existing_columns = {c["name"] for c in inspector.get_columns(table)}
        if column in existing_columns:
            continue
        if ddl == "TIMESTAMPTZ_NOT_NULL_NOW":
            if dialect == "postgresql":
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {column} "
                    "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
                ))
            else:
                # SQLite no admite ADD COLUMN NOT NULL con DEFAULT no constante:
                # se añade anulable y se rellena con la fecha actual.
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} TIMESTAMP"))
                conn.execute(text(f"UPDATE {table} SET {column} = CURRENT_TIMESTAMP WHERE {column} IS NULL"))
            continue
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))

    # Respaldo acotado: filas sin clasificar (en la práctica no cambia nada).
    if "questions" in existing_tables:
        question_columns = {c["name"] for c in inspect(conn).get_columns("questions")}
        if "source" in question_columns:
            conn.execute(text("UPDATE questions SET source='official' WHERE source IS NULL"))
        if "status" in question_columns:
            conn.execute(text("UPDATE questions SET status='approved' WHERE status IS NULL"))

    inspector = inspect(conn)
    for index_name, (table, ddl) in NEW_INDEXES.items():
        if table not in existing_tables:
            continue
        if index_name not in {i["name"] for i in inspector.get_indexes(table)}:
            conn.execute(text(ddl))


# ── Migración 2: índice para el tope diario del asistente por usuario ──────────


def _indice_ai_queries_usuario_fecha(conn: Connection) -> None:
    if "ai_queries" not in set(inspect(conn).get_table_names()):
        return
    # IF NOT EXISTS: válido en PostgreSQL y SQLite.
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_ai_queries_user_created ON ai_queries (user_id, created_at)"
    ))


# Migración 3: completar el esquema de consultas de bases anteriores.
def _pregunta_normalizada_ai(conn: Connection) -> None:
    if "ai_queries" not in set(inspect(conn).get_table_names()):
        return
    columns = {column["name"] for column in inspect(conn).get_columns("ai_queries")}
    if "question_normalizada" not in columns:
        conn.execute(text("ALTER TABLE ai_queries ADD COLUMN question_normalizada TEXT"))


def _crear_feedback(conn: Connection) -> None:
    from app.models.feedback import Feedback

    Feedback.__table__.create(bind=conn, checkfirst=True)


def _crear_evaluaciones_usabilidad(conn: Connection) -> None:
    from app.models.feedback import UsabilityEvaluation

    UsabilityEvaluation.__table__.create(bind=conn, checkfirst=True)


# Lista ordenada: añadir al final; nunca editar versiones ya publicadas.
MIGRATIONS: list[Migration] = [
    Migration(1, "linea_base", _linea_base),
    Migration(2, "indice_ai_queries_usuario_fecha", _indice_ai_queries_usuario_fecha),
    Migration(3, "pregunta_normalizada_ai", _pregunta_normalizada_ai),
    Migration(4, "crear_feedback", _crear_feedback),
    Migration(5, "crear_evaluaciones_usabilidad", _crear_evaluaciones_usabilidad),
]

_SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def _applied_versions(conn: Connection) -> dict[int, str]:
    rows = conn.execute(text("SELECT version, name FROM schema_migrations")).all()
    return {int(v): str(n) for v, n in rows}


def run_migrations(engine: Engine | None = None) -> list[int]:
    """Aplica las migraciones pendientes. Devuelve las versiones aplicadas en esta llamada."""
    engine = engine or ddl_engine
    is_pg = engine.dialect.name == "postgresql"
    applied_now: list[int] = []

    with engine.connect() as lock_conn:
        if is_pg:
            lock_conn.execute(text("SELECT pg_advisory_lock(:k)"), {"k": _ADVISORY_LOCK_KEY})
            lock_conn.commit()
        try:
            with engine.begin() as conn:
                conn.execute(text(_SCHEMA_MIGRATIONS_DDL))
            with engine.connect() as check:
                applied = _applied_versions(check)

            for migration in MIGRATIONS:
                if migration.version in applied:
                    continue
                with engine.begin() as conn:
                    migration.apply(conn)
                    conn.execute(
                        text("INSERT INTO schema_migrations (version, name) VALUES (:v, :n)"),
                        {"v": migration.version, "n": migration.name},
                    )
                applied_now.append(migration.version)
                logger.info("migración %s (%s) aplicada", migration.version, migration.name)
        finally:
            if is_pg:
                lock_conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _ADVISORY_LOCK_KEY})
                lock_conn.commit()
    return applied_now


