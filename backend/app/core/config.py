"""Configuración central de la aplicación.

Todas las credenciales y parámetros sensibles se leen desde variables de
entorno (ver .env.example). Nunca hardcodear credenciales en el código.
"""
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "INSOFT"
    PROJECT_DESCRIPTION: str = "Sistema web de apoyo al aprendizaje de Oftalmología e Instrumentación Quirúrgica."
    API_PREFIX: str = "/api"

    # ── Pruebas de carga (T8) ───────────────────────────────────────────
    ENVIRONMENT: str = "development"     # "production" en despliegue real
    AI_MOCK: bool = False                # respuestas canned; se BLOQUEA en prod

    # Base de datos PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg2://oftallearn:oftallearn@db:5432/oftallearn"
    # Fuerza SSL en la conexión (se activa sola para neon.tech). Para Neon:
    # DATABASE_SSL=true en los proveedores que no entregan host *.neon.tech.
    DATABASE_SSL: bool = False

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
    # Añadido: previews/producción de Vercel (https://*.vercel.app).
    BACKEND_CORS_ORIGIN_REGEX: str = (
        r"^http://(localhost|127\.0\.0\.1|0\.0\.0\.0|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
        r"100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3})(:\d+)?$"
        r"|^https://.*\.vercel\.app$"
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

    @model_validator(mode="after")
    def _require_secret_key_outside_dev(self) -> "Settings":
        """Producción no arranca con SECRET_KEY placeholder.

        Con DEV_AUTH_ENABLED=false el backend se niega a arrancar si
        SECRET_KEY está vacía o en su valor placeholder: los JWT firmados
        con una clave pública conocida no son seguros.
        """
        if not self.DEV_AUTH_ENABLED and self.SECRET_KEY.strip() in (
            "",
            "change-me-in-production",
        ):
            raise RuntimeError(
                "SECRET_KEY ausente o placeholder y DEV_AUTH_ENABLED=false: "
                "define SECRET_KEY (por variable de entorno o .env) para iniciar "
                "el backend en producción, o activa DEV_AUTH_ENABLED=true solo "
                "en desarrollo local."
            )
        return self

    @property
    def database_ssl_args(self) -> dict:
        """Argumentos de conexión para proveedores gestionados (Neon/Render).

        Se activa SSL automáticamente si el host es neon.tech o si se define
        DATABASE_SSL=true. Para Neon se exige `sslmode=require` (el pool de
        Neon a veces pide verify-full; require es lo mínimo válido).
        """
        url = self.DATABASE_URL
        needs_ssl = "neon.tech" in url or self.DATABASE_SSL
        if "sqlite" in url or not needs_ssl:
            return {}
        return {"sslmode": "require"}

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
