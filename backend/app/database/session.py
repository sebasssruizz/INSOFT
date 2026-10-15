from sqlalchemy import create_engine, event
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
#     (el lifespan re-intenta 30 veces antes de rendir),
#   - pool_timeout: agotar conexiones libres responde 503 db_unavailable
#     (no se cuelga la petición; ver docs/despliegue/TIMEOUTS_BD.md).
# statement_timeout (DB_STATEMENT_TIMEOUT_S) se aplica por transacción con
# SET LOCAL: el pooler de Neon (pgbouncer en modo transacción) NO conserva el
# estado de sesión (SET/pooler) ni el parámetro "options" de la cadena, así
# que la única forma fiable es dentro de la transacción misma. Decisión §13.

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
        "pool_timeout": settings.DB_POOL_TIMEOUT,
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

if not settings.DATABASE_URL.startswith("sqlite") and settings.DB_STATEMENT_TIMEOUT_S > 0:
    @event.listens_for(SessionLocal, "after_begin")
    def _statement_timeout_por_transaccion(session, transaction, connection):
        """Fija statement_timeout SOLO dentro de la transacción en curso.

        SET LOCAL expira al commit/rollback: no queda estado persistente en
        el backend de Postgres, por lo que es seguro con pgbouncer en modo
        transacción (Neon pooler). El engine DDL (migraciones) no usa esta
        sesión, y las transacciones largas de DDL no quedan cortadas.
        """
        ms = settings.DB_STATEMENT_TIMEOUT_S * 1000
        connection.exec_driver_sql(f"SET LOCAL statement_timeout = {int(ms)}")


def get_db():
    """Dependencia FastAPI que provee una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
