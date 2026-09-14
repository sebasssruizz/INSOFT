"""Migraciones ligeras sin Alembic (adecuado para esta primera versión).

Añade columnas nuevas a tablas existentes si faltan, de forma idempotente.
Compatible con PostgreSQL y SQLite (verificando primero el esquema).
"""
from sqlalchemy import inspect, text

from app.database.session import engine

# (tabla, columna) -> definición SQL de la columna
NEW_COLUMNS = {
    ("users", "country"): "VARCHAR(120)",
    ("users", "age"): "INTEGER",
}


def ensure_schema_compatibility() -> None:
    inspector = inspect(engine)
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
