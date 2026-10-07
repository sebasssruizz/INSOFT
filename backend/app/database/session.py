from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # SSL para proveedores gestionados (Neon/Render): settings decide.
    connect_args.update(settings.database_ssl_args)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Migraciones (ensure_schema_compatibility + create_all del lifespan) usan el
# MISMO engine: en producción con Neon, DATABASE_URL debe ser la conexión
# DIRECTA (sin "-pooler"), porque la agrupada no soporta DDL confiable.
# La app completa puede convivir con esa misma URL directa en los planes
# gratuitos; si luego se escala con PgBouncer/Neon-pooler, separar en dos
# engines: DDL directo y pool agrupado.


def get_db():
    """Dependencia FastAPI que provee una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
