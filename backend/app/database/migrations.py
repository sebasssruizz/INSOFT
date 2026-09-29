"""Migraciones ligeras sin Alembic (adecuado para esta primera versión).

Añade columnas nuevas a tablas existentes si faltan, de forma idempotente.
Compatible con PostgreSQL y SQLite (verificando primero el esquema).

Las migraciones son SIEMPRE aditivas: nunca borran tablas, columnas ni datos.
"""
from sqlalchemy import inspect, text

from app.database.session import engine

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
}

# Índices nuevos: (nombre, SQL). Idempotente via chequeo previo.
NEW_INDEXES = {
    "ix_questions_subtopic_status": "CREATE INDEX ix_questions_subtopic_status ON questions (subtopic_id, status)",
}


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)  # sin caché de reflexión: ve el estado actual del esquema
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        # Habilita la extensión pgvector en PostgreSQL (requerida por las
        # columnas `vector` de subtopic_chunks). No-op en SQLite/tests.
        if engine.dialect.name == "postgresql":
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        for (table, column), ddl in NEW_COLUMNS.items():
            if table not in existing_tables:
                continue
            existing_columns = {c["name"] for c in inspector.get_columns(table)}
            if column not in existing_columns:
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

        for index_name, ddl in NEW_INDEXES.items():
            if "questions" not in existing_tables:
                continue
            existing_indexes = {i["name"] for i in inspector.get_indexes("questions")}
            if index_name not in existing_indexes:
                conn.execute(text(ddl))
