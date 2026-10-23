"""Autogestión de rol cerrada (fix rol-autogestionado).

- PATCH /api/users/me/role con DEV_AUTH_ENABLED=false → 403 SIEMPRE y el rol
  queda intacto (ni un cliente puede promoverse a docente).
- Con DEV_AUTH_ENABLED=true sigue disponible viañ (comfort de desarrollo).
- Auditoría de asignación masiva: PATCH /me/profile solo acepta country/age
  (nunca role/id/email) y otros endpoints de usuario no permiten tocar a otros.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.core.config import settings  # noqa: E402


def _login(client, email, role):
    r = client.post("/api/auth/dev", json={"email": email, "name": "N", "role": role})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_no_autogestion_403_y_rol_intacto(client, monkeypatch):
    # login con dev habilitado (el flag solo bloquea el endpoint de rol)
    headers = _login(client, "rol-student-1@x.com", "STUDENT")
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", False)
    before = client.get("/api/users/me", headers=headers).json()["role"]
    r = client.patch("/api/users/me/role", json={"role": "TEACHER"}, headers=headers)
    assert r.status_code == 403, r.text
    after = client.get("/api/users/me", headers=headers).json()["role"]
    assert after == before == "STUDENT", "¡un cliente se promovió de rol!"


def test_no_autogestion_anonimo_401(client):
    r = client.patch("/api/users/me/role", json={"role": "TEACHER"})
    assert r.status_code == 401


def test_inyeccion_de_campos_ignorada(client):
    """Xtra de campos (role/id/email/created_by) jamás cambian el perfil."""
    headers = _login(client, "mas-assign@x.com", "STUDENT")
    me = client.get("/api/users/me", headers=headers).json()
    r = client.patch(
        "/api/users/me/profile",
        json={"country": "Colombia", "age": 30, "role": "TEACHER", "id": 99999,
              "email": "hack@x.com", "created_at": "1990-01-01T00:00:00Z"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    me2 = client.get("/api/users/me", headers=headers).json()
    assert me2["role"] == me["role"] == "STUDENT"
    assert me2["id"] == me["id"]
    assert me2["email"] == me["email"]


def test_con_dev_auth_email_cambio_props_permitido(client, monkeypatch):
    """Behavior DEV:定义 changed role propio sigue activo SOLO en desarrollo."""
    monkeypatch.setattr(settings, "DEV_AUTH_ENABLED", True)
    headers = _login(client, "rol-dev-switch@x.com", "STUDENT")
    r = client.patch("/api/users/me/role", json={"role": "TEACHER"}, headers=headers)
    assert r.status_code == 200, r.text
    r2 = client.patch("/api/users/me/role", json={"role": "STUDENT"}, headers=headers)
    assert r2.status_code == 200


def test_perfil_actuales_solo_country_age(client):
    headers = _login(client, "perfil-guard@x.com", "STUDENT")
    r = client.patch("/api/users/me/profile", json={"country": "Chile", "age": 30}, headers=headers)
    assert r.status_code == 200
