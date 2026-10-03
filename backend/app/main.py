import time
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
from app.seed.seed_content import run_seed_by_mode
from app.services.exceptions import ServiceError

# Importar modelos para registrarlos en la metadata antes de create_all
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas y cargar el contenido oficial + Curso General.
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
        run_seed_by_mode(db, settings.seed_mode_effective)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    if settings.is_production:
        errors = settings.production_validation_errors()
        if errors:
            raise RuntimeError(
                "El backend se negó a arrancar con ENV=production por "
                "configuración insegura:\n- " + "\n- ".join(errors)
            )

    expose_docs = not settings.is_production or settings.EXPOSE_DOCS
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if expose_docs else None,
        redoc_url="/redoc" if expose_docs else None,
        openapi_url=f"{settings.API_PREFIX}/openapi.json" if expose_docs else None,
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

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "service": settings.PROJECT_NAME}

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()
