import asyncio
import json as _json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import OperationalError

from app.api.router import api_router
from app.api.routes.ai import limiter as ai_limiter
from app.core.config import settings
from app.database.base import Base
from app.database.migrations import ensure_schema_compatibility
from app.database.session import SessionLocal, engine
from app.database.session import engine as _engine
from app.seed.seed_content import seed_official_content
from app.services.exceptions import ServiceError


def _setup_logging() -> logging.Logger:
    """Configura el log raíz del backend (formato y nivel por env).

    "json" produce líneas {"ts","level","logger","msg"} idénticas para
    herramientas de colección (docker logs, Loki, etc.). "plain" es el
    formato por defecto de logging. Los extras sensibles (claves, prompts
    completos, PII) NUNCA entran por aquí: las llamadas de logging del
    código no incluyen secretos ni payloads.
    """
    handler = logging.StreamHandler()
    if settings.LOG_FORMAT == "json":
        class _JsonFormatter(logging.Formatter):
            def format(self, record):
                return _json.dumps(
                    {
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "level": record.levelname,
                        "logger": record.name,
                        "msg": record.getMessage(),
                    },
                    ensure_ascii=False,
                )

        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL.upper())
    logging.getLogger("uvicorn.access").handlers = [handler]
    return root


logger = _setup_logging()

# Importar modelos para registrarlos en la metadata antes de create_all
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas y cargar el contenido oficial + Curso General (idempotente).
    # Reintenta mientras la base de datos termina de estar disponible.
    attempts = 30
    while True:
        try:
            # Migraciones antes de create_all: habilita pgvector (lo necesitan
            # las columnas `vector`) y añade columnas faltantes en tablas viejas.
            ensure_schema_compatibility()
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            attempts -= 1
            if attempts == 0:
                raise
            time.sleep(1)
    db = SessionLocal()
    try:
        seed_official_content(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    if settings.AI_MOCK and settings.ENVIRONMENT == "production":
        raise RuntimeError("AI_MOCK no está permitido con ENVIRONMENT=production.")
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
    )

    # slowapi: el estado del app referencia el limiter principal; cada router
    # (ai, quiz) usa su propio limiter en sus decoradores y así se mantiene el
    # registro de límites separado por endpoint.
    app.state.limiter = ai_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ServiceError)
    async def service_error_handler(request: Request, exc: ServiceError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Respuesta uniforme SIN detalles internos (evita filtrar secretos,
        # queries de SQL, rutas de archivos). El detalle real vive en el log.
        logger.exception("error no manejado: %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "[error-interno] Contacta al equipo con el X-Request-ID."},
        )

    @app.get("/ready", tags=["health"])
    def ready():
        """Liveness+readiness para el balanceador/proxy: DB y pgvector OK.

        SIN detalles (no expone motor/host/estado interno): 200 "ok" o 503.
        """
        try:
            with engine.connect() as conn:
                from sqlalchemy import text

                conn.execute(text("SELECT 1"))
                if conn.dialect.name == "postgresql":
                    conn.execute(text("SELECT extname FROM pg_extension WHERE extname='vector'"))
            return {"status": "ok"}
        except Exception:
            logger.exception("/ready falló")
            return JSONResponse(status_code=503, content={"status": "unavailable"})

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    @app.middleware("http")
    async def request_id_middleware(request, call_next):
        """Propaga X-Request-ID: la cabecera entra si llega, si no se genera.

        El id viaja en la respuesta para correlacionar errores con el log.
        No registra query strings ni cuerpo (evita PII/secretos).
        """
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("request").info(
            "%s %s -> %s (%.1f ms) request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
            request_id,
        )
        return response

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
