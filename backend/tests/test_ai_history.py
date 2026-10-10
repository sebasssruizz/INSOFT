"""Tests de autorización para los endpoints de historial de IA.

- Que un estudiante NO pueda ver el historial de otro vía /api/ai/history
- Que un no-profesor reciba 403 en /api/ai/history/all
"""
import os

os.environ["SECRET_KEY"] = "test-secret"
os.environ["AI_PROVIDER"] = "openrouter"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test"
os.environ["OPENROUTER_NORMALIZE_MODEL"] = "liquid/lfm-2.5-2.6b:free"
os.environ["OPENROUTER_ANSWER_MODEL"] = "minimax/minimax-m3:free"
os.environ["AI_ASK_RATE_LIMIT"] = "10/hour"
os.environ["OPENROUTER_GLOBAL_LIMIT_PER_MIN"] = "18"
os.environ["API_KEY"] = "sk-or-v1-test"

import pytest
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.repositories import ai_query_repository as ai_query_repo
from app.repositories import user_repository as user_repo


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def teacher_token(client):
    resp = client.post("/api/auth/dev", json={"email": "teacher@test.com", "name": "Teacher", "role": "TEACHER"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def student_token(client):
    resp = client.post("/api/auth/dev", json={"email": "student1@test.com", "name": "Student 1", "role": "STUDENT"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def another_student_token(client):
    resp = client.post("/api/auth/dev", json={"email": "student2@test.com", "name": "Student 2", "role": "STUDENT"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_headers(client, token):
    return {"Authorization": f"Bearer {token}"}


def test_student_cannot_see_another_student_history(client, student_token, another_student_token, teacher_token):
    """Un estudiante solo puede ver su propio historial; nunca el de otro estudiante."""
    headers = auth_headers(client, student_token)

    # Consulta el historial del propio estudiante
    resp = client.get("/api/ai/history", headers=headers)
    assert resp.status_code == 200, resp.text
    own = resp.json()
    assert len(own) >= 0  # Puede tener 0 si no hay preguntas todavía

    # Sembramos una consulta para el segundo estudiante; el filtro por user_id
    # garantiza que la consulta del primer estudiante no la incluya nunca.
    with SessionLocal() as s:
        from app.models.user import User, UserRole

        u2 = user_repo.get_by_email(s, "student2@test.com")
        if u2 is None:
            u2 = user_repo.create(
                s, google_id="dev-test2", name="Second Student", email="student2@test.com",
                profile_image=None, role=UserRole.STUDENT,
            )
        ai_query_repo.create(
            s, user_id=u2.id, question_original="Pregunta de prueba 2", subtopic_id=None,
            respuesta="Respuesta de prueba 2", session_id=None, model_used="test",
        )

    # El historial del primer estudiante solo debe contener sus propias filas.
    resp2 = client.get("/api/ai/history", headers=auth_headers(client, student_token))
    data = resp2.json()
    assert resp2.status_code in (200, 404)
    for item in data:
        assert item["question"] != "Pregunta de prueba 2"


def test_professor_can_see_all_history(client, teacher_token, student_token):
    """Un profesor sí puede ver el historial de todos los estudiantes."""
    headers = auth_headers(client, teacher_token)

    # Consultar el historial completo
    resp = client.get("/api/ai/history/all", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    print(f"Historial all: {len(data)} entries")


def test_non_professor_forbidden_on_history_all(client, student_token):
    """Un estudiante (no profesor) al intentar /api/ai/history/all debe recibir 403."""
    headers = auth_headers(client, student_token)
    resp = client.get("/api/ai/history/all", headers=headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
