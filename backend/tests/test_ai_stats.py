"""Tests de autorización para endpoints de estadísticas de IA.

- Que un estudiante NO pueda acceder a /api/ai/stats/*
- Que una profesora solo vea datos de sus propios cursos (no de cursos de otra profesora)
"""
import os

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test"
os.environ["OPENROUTER_NORMALIZE_MODEL"] = "liquid/lfm-2.5-2.6b:free"
os.environ["OPENROUTER_ANSWER_MODEL"] = "minimax/minimax-m3:free"
os.environ["AI_ASK_RATE_LIMIT"] = "10/hour"
os.environ["OPENROUTER_GLOBAL_LIMIT_PER_MIN"] = "18"

import pytest
from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.main import app
from app.models.ai_query import AiQuery
from app.models.content import Subtopic, Topic
from app.models.course import Course, CourseMembership, CourseType
from app.models.user import User, UserRole


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_user(db, email, name, role):
    user = User(google_id=f"dev-{email}", email=email, name=name, role=role)
    db.add(user)
    db.commit()
    return user


@pytest.fixture(scope="module")
def setup_data():
    """Crea estructura de cursos y consultas para tests de profesoras."""
    with SessionLocal() as db:
        # Profesora 1
        t1 = _make_user(db, "teacher1@test.com", "Teacher 1", UserRole.TEACHER)
        # Profesora 2
        t2 = _make_user(db, "teacher2@test.com", "Teacher 2", UserRole.TEACHER)
        # Estudiantes
        s1 = _make_user(db, "student1@test.com", "Student 1", UserRole.STUDENT)
        s2 = _make_user(db, "student2@test.com", "Student 2", UserRole.STUDENT)

        # Cursos
        c1 = Course(name="Curso T1", description="Curso de Teacher 1", code="T1C1", type=CourseType.TEACHER, teacher_id=t1.id)
        c2 = Course(name="Curso T2", description="Curso de Teacher 2", code="T2C1", type=CourseType.TEACHER, teacher_id=t2.id)
        db.add_all([c1, c2])
        db.commit()

        # Inscripciones
        m1 = CourseMembership(course_id=c1.id, user_id=s1.id)
        m2 = CourseMembership(course_id=c2.id, user_id=s2.id)
        db.add_all([m1, m2])
        db.commit()

        # Subtema
        topic = Topic(name="Tema Test Stats", description="Test", order=1)
        db.add(topic)
        db.commit()
        subtopic = Subtopic(topic_id=topic.id, name="Subtema Test", content="Contenido de prueba", order=1)
        db.add(subtopic)
        db.commit()

        # Consultas de IA
        q1 = AiQuery(user_id=s1.id, subtopic_id=subtopic.id, question_original="Pregunta de S1",
                     respuesta="Respuesta 1", model_used="test", response_time_ms=100)
        q2 = AiQuery(user_id=s2.id, subtopic_id=subtopic.id, question_original="Pregunta de S2",
                     respuesta="Respuesta 2", model_used="test", response_time_ms=200)
        db.add_all([q1, q2])
        db.commit()

        yield {
            "teacher1": t1, "teacher2": t2,
            "student1": s1, "student2": s2,
            "course1": c1, "course2": c2,
            "subtopic": subtopic,
        }


def test_student_forbidden_on_stats_overview(client: TestClient, setup_data):
    """Un estudiante recibe 403 en /api/ai/stats/overview."""
    headers = auth_headers(client, "student1@test.com", "Student 1", "STUDENT")
    resp = client.get("/api/ai/stats/overview", headers=headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


def test_student_forbidden_on_stats_students(client: TestClient, setup_data):
    """Un estudiante recibe 403 en /api/ai/stats/students."""
    headers = auth_headers(client, "student1@test.com", "Student 1", "STUDENT")
    resp = client.get("/api/ai/stats/students", headers=headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


def test_student_forbidden_on_stats_subtopics(client: TestClient, setup_data):
    """Un estudiante recibe 403 en /api/ai/stats/subtopics."""
    headers = auth_headers(client, "student1@test.com", "Student 1", "STUDENT")
    resp = client.get("/api/ai/stats/subtopics", headers=headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"


def test_teacher_sees_only_own_students_overview(client: TestClient, setup_data):
    """Teacher 1 ve solo a sus estudiantes en overview."""
    t1_headers = auth_headers(client, "teacher1@test.com", "Teacher 1", "TEACHER")

    # Teacher 1 consulta overview
    resp = client.get("/api/ai/stats/overview", headers=t1_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Debe ver 1 pregunta (la de su estudiante S1)
    assert data["total_preguntas"] == 1, f"Teacher 1 debería ver 1 pregunta, vio {data['total_preguntas']}"


def test_teacher_sees_only_own_students_students_list(client: TestClient, setup_data):
    """Teacher 1 ve solo a sus estudiantes en lista de estudiantes."""
    t1_headers = auth_headers(client, "teacher1@test.com", "Teacher 1", "TEACHER")

    resp = client.get("/api/ai/stats/students", headers=t1_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Solo debe ver a S1 (su estudiante)
    assert data["total"] == 1, f"Teacher 1 debería tener 1 estudiante, tiene {data['total']}"
    if data["students"]:
        assert data["students"][0]["user_id"] == setup_data["student1"].id


def test_teacher_sees_only_own_students_subtopics(client: TestClient, setup_data):
    """Teacher 1 ve stats solo de sus estudiantes en subtopics."""
    t1_headers = auth_headers(client, "teacher1@test.com", "Teacher 1", "TEACHER")

    resp = client.get("/api/ai/stats/subtopics", headers=t1_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verificar que solo cuenta la pregunta de S1
    if data["subtopics"]:
        total = sum(st["total_preguntas"] for st in data["subtopics"])
        assert total == 1, f"Teacher 1 debería ver 1 pregunta total en subtopics, vio {total}"


def test_teacher2_sees_her_own_students(client: TestClient, setup_data):
    """Teacher 2 ve solo a sus estudiantes (S2), no a los de Teacher 1."""
    t2_headers = auth_headers(client, "teacher2@test.com", "Teacher 2", "TEACHER")

    # Overview
    resp = client.get("/api/ai/stats/overview", headers=t2_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total_preguntas"] == 1, f"Teacher 2 debería ver 1 pregunta (S2), vio {data['total_preguntas']}"

    # Students list
    resp = client.get("/api/ai/stats/students", headers=t2_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    if data["students"]:
        assert data["students"][0]["user_id"] == setup_data["student2"].id
