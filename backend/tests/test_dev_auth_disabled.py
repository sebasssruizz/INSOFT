"""El login de desarrollo debe estar CERRADO por defecto.

Con DEV_AUTH_ENABLED=false (o sin definir):
- POST /api/auth/dev responde 403 sin crear usuario ni sesión.
- No importa qué email/rol se solicite: nunca se persiste nada.

Nota de aislamiento: varios módulos de la suite fijan
os.environ["DEV_AUTH_ENABLED"]="true" en sus imports y conftest reconstruye
Settings con ese entorno. Aquí NO dependemos del orden: se fuerza el flag
False en la Settings compartida con monkeypatch (se restablece al salir).
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "false"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

PAYLOADS = [
    {"email": "intruso@demo.com", "name": "Intruso", "role": "TEACHER"},
    {"email": "intruso2@demo.com", "name": "Intruso 2", "role": "STUDENT"},
    {},  # sin campos: 422, y en ningún caso una sesión creada
]


def _user_count() -> int:
    with SessionLocal() as s:
        return s.scalar(select(func.count(User.id)))


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _dev_auth_disabled(monkeypatch):
    """Fuerza DEV_AUTH_ENABLED=False para todo test de este módulo."""
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", False)


def test_dev_login_disabled_responde_403(client):
    resp = client.post(
        "/api/auth/dev",
        json=PAYLOADS[0],
    )
    assert resp.status_code == 403, resp.text
    assert "desactivado" in resp.json()["detail"].lower()


def test_dev_login_disabled_no_crea_usuario_ni_sesion(client):
    before = _user_count()
    for payload in PAYLOADS:
        resp = client.post("/api/auth/dev", json=payload)
        assert resp.status_code in (403, 422), payload  # nunca 200/201
        body = resp.json()
        if resp.status_code == 403:
            assert "access_token" not in body or body.get("access_token") is None
    assert _user_count() == before, "El endpoint creó usuarios en modo deshabilitado."


def test_dev_login_disabled_email_docente_real(client):
    """Ni siquiera con un correo de TEACHER_EMAILS se puede entrar por dev."""
    before = _user_count()
    resp = client.post(
        "/api/auth/dev",
        json={"email": "docente-serio@demo.com", "name": "Docente", "role": "TEACHER"},
    )
    assert resp.status_code == 403
    assert _user_count() == before, "El endpoint creó el usuario docente por error."
