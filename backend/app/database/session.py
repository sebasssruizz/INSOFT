from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# ── Conexiones para Neon (y cualquier proveedor gestionado) ──────────────
# Neon suspende el cómputo por inactividad: la PRIMERA conexión puede tardar
# unos segundos y los estabilizadores de la conexión de proveedores de
# guardias (proxy) pueden cerrar conexiones largas a mitad de la vida. Por
# eso el engine de la app usa:
#   - pool pequeño (pool_size/max_overflow) para no rebosar el tope de
#     conexiones de Neon free (100 por branch),
#   - pool_pre_ping: detecta y recicla conexiones muertas antes de usarlas,
#   - pool_recycle: renueva conexiones antes de que el proxy las corte,
#   - connect_timeout: el arranque falla rápido y con un mensaje claro
#     (el lifespan re-intenta 30 veces antes de rendir).

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args: dict = {"check_same_thread": False}
    engine_kwargs: dict = {}
else:
    # SSL para proveedores gestionados (Neon/Render): settings decide.
    connect_args = dict(settings.database_ssl_args)
    connect_args["connect_timeout"] = settings.DB_CONNECT_TIMEOUT
    engine_kwargs = {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": True,
    }

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs)

# Engine para DDL (migraciones + create_all del lifespan). Para Neon debe ir
# por la conexión DIRECTA del endpoint (sin "-pooler"): la pgbouncer de la
# rama agrupada no admite transacciones DDL de forma fiable. Sin pool
# (NullPool): 1-2 conexiones efímeras en el arranque, sin retener sockets.
_ddl_url = settings.database_ddl_url
if _ddl_url.startswith("sqlite"):
    ddl_engine = create_engine(_ddl_url, connect_args={"check_same_thread": False})
else:
    ddl_engine = create_engine(
        _ddl_url, connect_args=dict(settings.database_ssl_args), poolclass=NullPool
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependencia FastAPI que provee una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
