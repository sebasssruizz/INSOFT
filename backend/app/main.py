import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api.router import api_router
from app.core.config import settings
from app.database.base import Base
from app.database.migrations import ensure_schema_compatibility
from app.database.session import SessionLocal, engine
from app.seed.seed_content import seed_official_content
from app.services.exceptions import ServiceError

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
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
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
