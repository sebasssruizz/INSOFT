"""Tests de humo de los flujos principales de OftalLearn.

Usan SQLite en memoria de fichero temporal y el login de desarrollo,
de modo que no requieren PostgreSQL ni credenciales de Google.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    if os.path.exists("/tmp/opencode/oftallearn_test.db"):
        os.remove("/tmp/opencode/oftallearn_test.db")
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow(client: TestClient):
    # 1. Health
    assert client.get("/health").status_code == 200

    # 2. Login estudiante -> acceso automático al Curso General
    student = auth_headers(client, "ana@example.com", "Ana", "STUDENT")
    courses = client.get("/api/courses", headers=student)
    assert courses.status_code == 200
    assert len(courses.json()) == 1
    general = courses.json()[0]
    assert general["type"] == "GENERAL"
    assert general["progress_percentage"] == 0.0
    assert general["total_subtopics"] > 0

    # 3. Contenido del curso general: temas y subtemas
    topics = client.get(f"/api/courses/{general['id']}/topics", headers=student)
    assert topics.status_code == 200
    assert len(topics.json()) >= 3
    first_subtopic = topics.json()[0]["subtopics"][0]

    # 4. Consultar subtema y marcarlo como completado
    detail = client.get(
        f"/api/subtopics/{first_subtopic['id']}",
        params={"course_id": general["id"]},
        headers=student,
    )
    assert detail.status_code == 200
    assert len(detail.json()["content"]) > 50
    assert detail.json()["completed"] is False

    prog = client.post(
        "/api/progress",
        json={"course_id": general["id"], "subtopic_id": first_subtopic["id"], "completed": True},
        headers=student,
    )
    assert prog.status_code == 200
    assert prog.json()["completed"] is True

    summary = client.get("/api/progress/course", params={"course_id": general["id"]}, headers=student)
    assert summary.status_code == 200
    assert summary.json()["completed_subtopics"] == 1
    assert summary.json()["percentage"] > 0

    # 5. Login profesor -> crear curso -> código único
    teacher = auth_headers(client, "prof@example.com", "Profesor", "TEACHER")
    created = client.post(
        "/api/courses",
        json={"name": "Oftalmología - Grupo A", "description": "Curso del grupo A"},
        headers=teacher,
    )
    assert created.status_code == 201, created.text
    teacher_course = created.json()
    assert teacher_course["code"].startswith("OFT-")
    assert teacher_course["type"] == "TEACHER"

    # 6. Estudiante se une con el código
    joined = client.post("/api/courses/join", json={"code": teacher_course["code"]}, headers=student)
    assert joined.status_code == 200, joined.text

    courses = client.get("/api/courses", headers=student).json()
    assert len(courses) == 2
    assert {c["name"] for c in courses} == {"Curso General de Oftalmología", "Oftalmología - Grupo A"}

    # 6b. Unirse dos veces -> 409
    again = client.post("/api/courses/join", json={"code": teacher_course["code"]}, headers=student)
    assert again.status_code == 409

    # 6c. Código inexistente -> 404
    missing = client.post("/api/courses/join", json={"code": "OFT-XXXX"}, headers=student)
    assert missing.status_code == 404

    # 7. El profesor ve a sus estudiantes
    students = client.get(f"/api/courses/{teacher_course['id']}/students", headers=teacher)
    assert students.status_code == 200
    assert [s["email"] for s in students.json()] == ["ana@example.com"]

    teacher_courses = client.get("/api/courses", headers=teacher).json()
    assert teacher_courses[0]["student_count"] == 1


def test_authorization(client: TestClient):
    student = auth_headers(client, "bob@example.com", "Bob", "STUDENT")
    teacher = auth_headers(client, "prof2@example.com", "Profesora 2", "TEACHER")
    other_teacher = auth_headers(client, "prof3@example.com", "Profesor 3", "TEACHER")

    # Estudiante NO puede crear cursos
    resp = client.post("/api/courses", json={"name": "Curso ilegal", "description": "x"}, headers=student)
    assert resp.status_code == 403

    # Profesor NO puede unirse a cursos con código
    resp = client.post("/api/courses/join", json={"code": "OFT-AAAA"}, headers=teacher)
    assert resp.status_code == 403

    # Un profesor NO puede ver los estudiantes del curso de otro profesor
    course = client.post("/api/courses", json={"name": "Curso de T2", "description": "x"}, headers=teacher).json()
    resp = client.get(f"/api/courses/{course['id']}/students", headers=other_teacher)
    assert resp.status_code == 403

    # Un estudiante NO puede acceder al contenido de un curso al que no pertenece
    resp = client.get(f"/api/courses/{course['id']}/topics", headers=student)
    assert resp.status_code == 403

    # Sin autenticación -> 401
    assert client.get("/api/courses").status_code == 401
    assert client.get("/api/users/me").status_code == 401


def test_role_switch(client: TestClient):
    """El usuario puede cambiar su propio rol; al pasar a estudiante se le
    inscribe automáticamente en el Curso General."""
    headers = auth_headers(client, "cambio@example.com", "Cambia Roles", "TEACHER")
    me = client.get("/api/users/me", headers=headers)
    assert me.json()["role"] == "TEACHER"

    # Como profesor no tiene cursos de estudiante
    assert client.get("/api/courses", headers=headers).json() == []

    # Cambiar a estudiante
    switched = client.patch("/api/users/me/role", json={"role": "STUDENT"}, headers=headers)
    assert switched.status_code == 200
    assert switched.json()["role"] == "STUDENT"

    # Ahora tiene el Curso General automáticamente
    courses = client.get("/api/courses", headers=headers).json()
    assert len(courses) == 1
    assert courses[0]["type"] == "GENERAL"

    # Y puede volver a profesor
    back = client.patch("/api/users/me/role", json={"role": "TEACHER"}, headers=headers)
    assert back.status_code == 200
    assert back.json()["role"] == "TEACHER"


def test_profile_completion(client: TestClient):
    """En desarrollo el perfil se completa automáticamente al registrarse."""
    headers = auth_headers(client, "nuevo@example.com", "Nuevo", "STUDENT")

    me = client.get("/api/users/me", headers=headers).json()
    assert me["profile_completed"] is True
    assert me["country"] == "Desarrollo"

    # Actualizar perfil sigue funcionando
    updated = client.patch(
        "/api/users/me/profile",
        json={"country": "México", "age": 22},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["profile_completed"] is True
    assert updated.json()["country"] == "México"

    # Validación: edad fuera de rango -> 422
    bad = client.patch(
        "/api/users/me/profile",
        json={"country": "México", "age": 5},
        headers=headers,
    )
    assert bad.status_code == 422
