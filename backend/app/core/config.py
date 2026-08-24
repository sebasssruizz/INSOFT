"""Configuración central de la aplicación.

Todas las credenciales y parámetros sensibles se leen desde variables de
entorno (ver .env.example). Nunca hardcodear credenciales en el código.
"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "INSOFT"
    PROJECT_DESCRIPTION: str = "Sistema web de apoyo al aprendizaje de Oftalmología e Instrumentación Quirúrgica."
    API_PREFIX: str = "/api"

    # Base de datos PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg2://oftallearn:oftallearn@db:5432/oftallearn"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

    # CORS (orígenes del frontend, separados por comas)
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://0.0.0.0:3000"

    # Correos que obtienen automáticamente el rol de profesor al registrarse (separados por comas)
    TEACHER_EMAILS: str = ""

    # Login de desarrollo (sin Google). SOLO para pruebas locales. Desactivado por defecto.
    DEV_AUTH_ENABLED: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Algunos proveedores entregan postgres://... ; SQLAlchemy requiere postgresql://
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def cors_origins(self) -> list[str]:
        return self._split_csv(self.BACKEND_CORS_ORIGINS)

    @property
    def teacher_emails(self) -> list[str]:
        return [e.lower() for e in self._split_csv(self.TEACHER_EMAILS)]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
