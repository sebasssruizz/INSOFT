"""Observabilidad (T5): logs, X-Request-ID, /ready y error uniforme.

Sin red ni proveedores: valida la superficie de salud y la respuesta
uniforme ante errores internos (sin filtrar detalles internos).
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def _login(client, email, role="STUDENT"):
    r = client.post("/api/auth/dev", json={"email": email, "name": "N", "role": role})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_vivo_publico(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_ok_sin_detalles(client):
    r = client.get("/ready")
    assert r.status_code == 200, r.text
    assert r.json() == {"status": "ok"}  # no expone motor/host/extensión


def test_request_id_se_propaga(client):
    r = client.get("/health", headers={"X-Request-ID": "prueba-123"})
    assert r.headers.get("X-Request-ID") == "prueba-123"
    r2 = client.get("/health")
    rid = r2.headers.get("X-Request-ID")
    assert rid and len(rid) == 16  # generado si no entra cabecera


def test_404_respuesta_uniforme(client):
    r = client.get("/api/recurso-inexistente")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_401_sin_token_no_filtraTrace(client):
    r = client.get("/api/users/me")
    assert r.status_code == 401
    assert "detail" in r.json()
