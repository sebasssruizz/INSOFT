"""Migraciones ligeras sin Alembic (adecuado para esta primera versión).

Añade columnas nuevas a tablas existentes si faltan, de forma idempotente.
Compatible con PostgreSQL y SQLite (verificando primero el esquema).

Las migraciones son SIEMPRE aditivas: nunca borran tablas, columnas ni datos.
"""
from sqlalchemy import inspect, text

from app.database.session import ddl_engine

# (tabla, columna) -> definición SQL de la columna
NEW_COLUMNS = {
    ("users", "country"): "VARCHAR(120)",
    ("users", "age"): "INTEGER",
    # Procedencia/ciclo de vida de preguntas (Fase: banco del profesor + IA).
    # Las filas preexistentes quedan como oficiales aprobadas via server_default
    # y el UPDATE de respaldo de abajo.
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

# Índices nuevos: (nombre, SQL). Idempotente via chequeo previo.
NEW_INDEXES = {
    "ix_questions_subtopic_status": ("questions", "CREATE INDEX ix_questions_subtopic_status ON questions (subtopic_id, status)"),
    "ix_ai_queries_session_id": ("ai_queries", "CREATE INDEX ix_ai_queries_session_id ON ai_queries (session_id)"),
    "ix_question_answers_user_subtopic": ("question_answers", "CREATE INDEX ix_question_answers_user_subtopic ON question_answers (user_id, subtopic_id)"),
    "ix_question_answers_question": ("question_answers", "CREATE INDEX ix_question_answers_question ON question_answers (question_id)"),
}


def ensure_schema_compatibility() -> None:
    """Migraciones idempotentes, siempre por el engine DDL (conexión directa)."""
    inspector = inspect(ddl_engine)  # sin caché de reflexión: ve el estado actual del esquema
    existing_tables = set(inspector.get_table_names())
    with ddl_engine.begin() as conn:
        # Habilita la extensión pgvector en PostgreSQL (requerida por las
        # columnas `vector` de subtopic_chunks). No-op en SQLite/tests.
        if ddl_engine.dialect.name == "postgresql":
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Tabla nueva de respuestas de quiz (aditiva; nunca borra datos).
        # create_all ya cubre arranques limpios; este CREATE cubre bases de
        # datos preexistentes con datos (idempotente via chequeo previo).
        if "question_answers" not in existing_tables and "users" in existing_tables and "questions" in existing_tables:
            if ddl_engine.dialect.name == "postgresql":
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
            inspector = inspect(ddl_engine)
            existing_tables = set(inspector.get_table_names())
        for (table, column), ddl in NEW_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing_columns:
                if ddl == "TIMESTAMPTZ_NOT_NULL_NOW":
                    # DDL específico por dialecto (misma semántica: ahora, no nulo).
                    if ddl_engine.dialect.name == "postgresql":
                        conn.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN {column} "
                            "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
                        ))
                    else:
                        conn.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN {column} "
                            "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
                        ))
                else:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))

        # Respaldo: ninguna fila de preguntas sin clasificar. Idempotente y
        # acotado (con WHERE); en la práctica no actualiza nada tras el primer
        # arranque porque el server_default ya cubre las filas nuevas.
        if "questions" in existing_tables:
            existing_columns = {c["name"] for c in inspector.get_columns("questions")}
            if "source" in existing_columns:
                conn.execute(text("UPDATE questions SET source='official' WHERE source IS NULL"))
            if "status" in existing_columns:
                conn.execute(text("UPDATE questions SET status='approved' WHERE status IS NULL"))

        for index_name, (table, ddl) in NEW_INDEXES.items():
            if table not in existing_tables:
                continue
            existing_indexes = {i["name"] for i in inspector.get_indexes(table)}
            if index_name not in existing_indexes:
                conn.execute(text(ddl))
