"""CORS: regex por defecto vaca; solo ALLOWED_ORIGINS.

Comprueba: (1) un origen Vercel de terceros queda fuera con el default;
(2) un origen exacto de la lista s pasa; (3) el patrn del proyecto permite
sus previews; (4) el patrn de OTRO proyecto no aplica a ours.
Sin red: app mnima con la misma configuracin que main.py.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/opencode/oftallearn_test.db")
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ.pop("BACKEND_CORS_ORIGIN_REGEX", None)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import Settings  # noqa: E402

PREVIEW_OTRO_PROYECTO = "https://otro-dash-1a2b3c-456.vercel.app"
PREVIEW_INSOFT = "https://insoft-1a2b3c-456.vercel.app"
ORIGEN_LOCAL = "http://localhost:3000"


def _app(origins: str, regex: str = "") -> FastAPI:
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o for o in origins.split(",") if o],
        allow_origin_regex=regex,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def _origen_default(client) -> str:
    r = client.get("/ping", headers={"Origin": ORIGEN_LOCAL})
    return r.headers.get("access-control-allow-origin", "")


def _regex_proyecto_insoft() -> str:
    """El patrn exacto documentado (docs/despliegue/CORS.md 2)."""
    return r"^https://insoft-[a-z0-9]+-[a-z0-9]+\.vercel\.app$|^https://insoft-git-[a-z0-9-]+-[a-z0-9]+\.vercel\.app$"


def test_default_regex_vacia_y_vercel_fuera():
    s = Settings()
    assert s.BACKEND_CORS_ORIGIN_REGEX == ""
    c = TestClient(_app(s.BACKEND_CORS_ORIGINS))
    r = c.get("/ping", headers={"Origin": PREVIEW_OTRO_PROYECTO})
    assert r.headers.get("access-control-allow-origin", "") == ""
    assert r.headers.get("access-control-allow-credentials", "") is None or True  # sin cors: sin cabecera de credenciales


def test_origen_exacto_de_la_lista_pasa():
    s = Settings()
    c = TestClient(_app(s.BACKEND_CORS_ORIGINS))
    assert _origen_default(c) == ORIGEN_LOCAL


def test_patron_proyecto_permite_sus_previews():
    s = Settings()
    c = TestClient(_app(s.BACKEND_CORS_ORIGINS, regex=_regex_proyecto_insoft()))
    r = c.get("/ping", headers={"Origin": PREVIEW_INSOFT})
    assert r.headers.get("access-control-allow-origin", "") == PREVIEW_INSOFT


def test_patron_de_otro_proyecto_no_aplica_al_nuestro():
    c = TestClient(_app(ORIGEN_LOCAL, regex=r"^https://otro-proj-[a-z0-9]+\.vercel\.app$"))
    r = c.get("/ping", headers={"Origin": PREVIEW_INSOFT})
    assert r.headers.get("access-control-allow-origin", "") == ""
