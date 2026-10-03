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

    # Entorno: "development" o "production". En producción se validan los
    # requisitos de seguridad al crear la app (ver production_validation_errors).
    ENV: str = "development"

    # Control del seed oficial en el arranque: "always" (comportamiento
    # histórico de desarrollo), "if_empty" (solo si no hay unidades; default en
    # producción) o "never". El valor "auto" resuelve por ENV.
    SEED_MODE: str = "auto"

    # Exponer /docs, /redoc y /openapi.json (solo tiene efecto en producción;
    # en desarrollo siempre están abiertos).
    EXPOSE_DOCS: bool = False

    # IPs de confianza para los encabezados X-Forwarded-For (uvicorn
    # --forwarded-allow-ips). En Docker interno se usan las redes privadas.
    FORWARDED_ALLOW_IPS: str = "127.0.0.1"

    # Procesos Uvicorn en producción. 1 por defecto: el modelo de embeddings
    # carga ~500 MB de RAM por proceso (ver docs/despliegue/REPORTE.md).
    WEB_CONCURRENCY: int = 1

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

    # CORS para pruebas desde el móvil por IP (localhost, 127.0.0.1, rangos privados
    # 10.x, 192.168.x, 172.16-31.x y CGNAT/Tailscale 100.64-127.x, cualquier puerto).
    BACKEND_CORS_ORIGIN_REGEX: str = (
        r"^http://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
        r"100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    )

    # Correos que obtienen automáticamente el rol de profesor al registrarse (separados por comas)
    TEACHER_EMAILS: str = ""

    # Login de desarrollo (sin Google). SOLO para pruebas locales. Desactivado por defecto.
    DEV_AUTH_ENABLED: bool = False

    # Modelo local de embeddings para el RAG (sentence-transformers, corre en CPU).
    # Multilingüe (español incluido), 384 dimensiones y liviano para CPU.
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # OpenRouter (IA)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_NORMALIZE_MODEL: str = "liquid/lfm-2.5-2.6b:free"
    OPENROUTER_ANSWER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"
    AI_ASK_RATE_LIMIT: str = "60/hour"
    OPENROUTER_GLOBAL_LIMIT_PER_MIN: int = 18

    # Google Gemini (IA) - proveedor alternativo gratuito
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_PROVIDER: str = "openrouter"  # "openrouter" o "gemini"

    # Generación de preguntas con IA (solo profesores)
    AI_QUESTION_RATE_LIMIT: str = "5/hour"
    AI_QUESTION_MAX_ATTEMPTS: int = 2

    # Tope de preguntas por quiz del estudiante (muestreo aleatorio si hay más)
    QUIZ_MAX_QUESTIONS: int = 10

    # Respuestas de quiz calificadas en servidor (por usuario; default alto)
    QUIZ_ANSWER_RATE_LIMIT: str = "120/hour"

    # Modo práctica (banco + IA reutilizable)
    PRACTICE_RATE_LIMIT: str = "30/hour"
    PRACTICE_DEFAULT_COUNT: int = 5
    PRACTICE_MAX_COUNT: int = 10
    PRACTICE_AI_RATIO: float = 0.4
    PRACTICE_MAX_GENERATIONS_PER_SUBTOPIC_PER_DAY: int = 4

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

    @property
    def is_production(self) -> bool:
        return self.ENV.strip().lower() == "production"

    @property
    def seed_mode_effective(self) -> str:
        """Resuelve SEED_MODE: 'auto' → 'if_empty' en producción, 'always' en desarrollo."""
        mode = self.SEED_MODE.strip().lower()
        if mode in ("always", "if_empty", "never"):
            return mode
        return "if_empty" if self.is_production else "always"

    def production_validation_errors(self) -> list[str]:
        """Requisitos de seguridad para arrancar con ENV=production.

        Devuelve la lista de problemas (vacía si todo está en orden). La app
        se niega a arrancar si la lista no está vacía.
        """
        errors: list[str] = []
        if self.DEV_AUTH_ENABLED:
            errors.append(
                "DEV_AUTH_ENABLED está activo: el login de desarrollo sin Google "
                "no puede usarse en producción (configúralo en false)."
            )
        if self.SECRET_KEY in ("", "change-me-in-production") or len(self.SECRET_KEY) < 32:
            errors.append(
                "SECRET_KEY está vacío, es el valor por defecto o mide menos de 32 "
                "caracteres. Genera uno con: openssl rand -hex 32"
            )
        if not self.GOOGLE_CLIENT_ID.strip():
            errors.append(
                "GOOGLE_CLIENT_ID está vacío: en producción el login de Google OAuth "
                "es obligatorio (configúralo en Google Cloud Console)."
            )
        if not self.cors_origins:
            errors.append(
                "BACKEND_CORS_ORIGINS está vacío: lista los orígenes permitidos "
                "(p. ej. https://tudominio.com)."
            )
        elif "*" in self.cors_origins:
            errors.append(
                "BACKEND_CORS_ORIGINS contiene '*': no se permite CORS abierto en "
                "producción."
            )
        return errors


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
