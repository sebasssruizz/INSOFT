"""Tests de estadísticas de quiz y export CSV (solo profesores).

- Cálculos correctos con datos sembrados.
- Profesor A no ve estudiantes de profesor B; estudiante → 403.
- CSV: solo estudiantes del profesor y escape de fórmulas Excel.
- Borrar una pregunta con respuestas la archiva (status=rejected).
"""
import os
import uuid

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ["QUIZ_ANSWER_RATE_LIMIT"] = "120/hour"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Question, Subtopic
from app.models.question_answer import QuestionAnswer
from app.models.question_meta import QuestionStatus
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="module")
def data(client):
    """Dos profesores con sus cursos; un estudiante por curso con respuestas."""
    t1 = auth_headers(client, "stats-t1@example.com", "Stats T1", "TEACHER")
    t2 = auth_headers(client, "stats-t2@example.com", "Stats T2", "TEACHER")
    c1 = client.post(
        "/api/courses", json={"name": "Curso Stats 1", "description": ""}, headers=t1
    ).json()
    c2 = client.post(
        "/api/courses", json={"name": "Curso Stats 2", "description": ""}, headers=t2
    ).json()

    s1 = auth_headers(client, "stats-e1@example.com", "Stats E1", "STUDENT")
    s2 = auth_headers(client, "stats-e2@example.com", "Stats E2", "STUDENT")
    assert client.post("/api/courses/join", json={"code": c1["code"]}, headers=s1).status_code == 200
    assert client.post("/api/courses/join", json={"code": c2["code"]}, headers=s2).status_code == 200

    subtopic_id = None
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id

    # Preguntas aprobadas del profesor T1 en ese subtema (creadas via API)
    q1 = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": "¿Stat pregunta uno?",
            "options": ["a1", "b1", "c1", "d1"],
            "correct_index": 0,
            "explanation": "exp1",
        },
        headers=t1,
    ).json()
    q2 = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": "¿Stat pregunta dos?",
            "options": ["a2", "b2", "c2", "d2"],
            "correct_index": 2,
            "explanation": "exp2",
        },
        headers=t1,
    ).json()

    # Respuestas sembradas: e1 (del profesor T1) responde 2, 1 correcta;
    # e2 (del profesor T2) responde 2, 2 correctas (solo debe verlas T2).
    with SessionLocal() as s:
        e1 = s.scalar(select(User).where(User.email == "stats-e1@example.com"))
        e2 = s.scalar(select(User).where(User.email == "stats-e2@example.com"))
        answers = [
            QuestionAnswer(user_id=e1.id, question_id=q1["id"], subtopic_id=subtopic_id,
                           attempt_id=str(uuid.uuid4()), selected_index=0, is_correct=True),
            QuestionAnswer(user_id=e1.id, question_id=q2["id"], subtopic_id=subtopic_id,
                           attempt_id=str(uuid.uuid4()), selected_index=0, is_correct=False),
            QuestionAnswer(user_id=e2.id, question_id=q1["id"], subtopic_id=subtopic_id,
                           attempt_id=str(uuid.uuid4()), selected_index=0, is_correct=True),
            QuestionAnswer(user_id=e2.id, question_id=q2["id"], subtopic_id=subtopic_id,
                           attempt_id=str(uuid.uuid4()), selected_index=2, is_correct=True),
        ]
        s.add_all(answers)
        s.commit()

    return {
        "t1": t1, "t2": t2, "s1": s1, "s2": s2,
        "c1": c1, "c2": c2,
        "subtopic_id": subtopic_id,
        "q1": q1, "q2": q2,
    }


def test_overview_for_teacher1(client, data):
    resp = client.get("/api/quiz/stats/overview", headers=data["t1"])
    assert resp.status_code == 200, resp.text
    stats = resp.json()
    assert stats["total_respuestas"] == 2
    assert stats["total_intentos"] == 2
    assert stats["estudiantes_activos"] == 1
    assert stats["porcentaje_acierto"] == 50


def test_overview_for_teacher2_sees_only_her_students(client, data):
    resp = client.get("/api/quiz/stats/overview", headers=data["t2"])
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_respuestas"] == 2
    assert stats["porcentaje_acierto"] == 100
    assert stats["estudiantes_activos"] == 1


def test_questions_stats(client, data):
    resp = client.get("/api/quiz/stats/questions", headers=data["t1"])
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    by_id = {q["question_id"]: q for q in body["questions"]}
    assert by_id[data["q1"]["id"]]["porcentaje_acierto"] == 100
    assert by_id[data["q2"]["id"]]["porcentaje_acierto"] == 0
    assert by_id[data["q2"]["id"]]["opcion_incorrecta_mas_elegida"] == 0


def test_students_stats(client, data):
    resp = client.get("/api/quiz/stats/students", headers=data["t1"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["students"][0]["respuestas"] == 2
    assert body["students"][0]["porcentaje_acierto"] == 50
    assert body["students"][0]["ultima_actividad"] is not None


def test_subtopics_stats(client, data):
    resp = client.get("/api/quiz/stats/subtopics", headers=data["t1"])
    assert resp.status_code == 200
    subtopics = resp.json()
    assert len(subtopics) == 1
    assert subtopics[0]["respuestas"] == 2
    assert subtopics[0]["porcentaje_acierto"] == 50


def test_student_forbidden_on_stats(client, data):
    for path in (
        "/api/quiz/stats/overview",
        "/api/quiz/stats/questions",
        "/api/quiz/stats/students",
        "/api/quiz/stats/subtopics",
        "/api/quiz/stats/export.csv",
    ):
        resp = client.get(path, headers=data["s1"])
        assert resp.status_code == 403, f"{path}: {resp.text}"


def test_export_csv_only_own_students(client, data):
    resp = client.get("/api/quiz/stats/export.csv", headers=data["t1"])
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    content = resp.text
    # Solo respuestas del estudiante de T1 (2 filas) + cabecera
    lines = [line for line in content.strip().splitlines() if line]
    assert len(lines) == 3
    assert "stats-e1@example.com" in content
    assert "stats-e2@example.com" not in content


def test_export_csv_escapes_formulas(client):
    """Un estudiante cuyo nombre empieza por '=' no debe inyectar fórmulas.

    Auto-contenido (orden-independiente): usa su propio docente/curso y NO
    toca el dataset compartido de `data` (agregar alumnos o respuestas a los
    cursos de T1/T2 cambiaría los conteos de los tests de stats).
    """
    t3 = auth_headers(client, "stats-t3@example.com", "Stats T3", "TEACHER")
    c3 = client.post(
        "/api/courses", json={"name": "Curso Stats 3", "description": ""}, headers=t3
    ).json()
    with SessionLocal() as s:
        from app.models.user import User, UserRole
        from app.models.course import CourseMembership

        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
        tricky = User(
            google_id="dev-tricky",
            email="stats-tricky@example.com",
            name="=HYPERLINK(\"https://evil.com\")",
            role=UserRole.STUDENT,
        )
        s.add(tricky)
        s.commit()
        s.add(CourseMembership(course_id=c3["id"], user_id=tricky.id))
        s.commit()
        tricky_id = s.scalar(select(User.id).where(User.email == "stats-tricky@example.com"))
    q3 = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": "¿Stat pregunta tres?",
            "options": ["a3", "b3", "c3", "d3"],
            "correct_index": 1,
            "explanation": "exp3",
        },
        headers=t3,
    ).json()
    with SessionLocal() as s:
        s.add(
            QuestionAnswer(
                user_id=tricky_id,
                question_id=q3["id"],
                subtopic_id=subtopic_id,
                attempt_id=str(uuid.uuid4()),
                selected_index=0,
                is_correct=True,
            )
        )
        s.commit()

    resp = client.get("/api/quiz/stats/export.csv", headers=t3)
    assert resp.status_code == 200
    content = resp.text
    # El nombre peligrosivo va escapado con prefijo '
    assert "'=HYPERLINK" in content


def test_delete_question_with_answers_archives(client):
    """Borrar una pregunta con respuestas la archiva (status=rejected).

    Auto-contenido: crea su propio docente, pregunta y respuesta; no elimina
    preguntas del dataset compartido (q2 con respuestas es insumo de los
    stats de los demás tests).
    """
    t4 = auth_headers(client, "stats-t4@example.com", "Stats T4", "TEACHER")
    e4 = auth_headers(client, "stats-e4@example.com", "Stats E4", "STUDENT")
    c4 = client.post(
        "/api/courses", json={"name": "Curso Stats 4", "description": ""}, headers=t4
    ).json()
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
    q4 = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": "¿Stat pregunta cuatro?",
            "options": ["a4", "b4", "c4", "d4"],
            "correct_index": 0,
            "explanation": "exp4",
        },
        headers=t4,
    ).json()
    with SessionLocal() as s:
        e4_user = s.scalar(select(User).where(User.email == "stats-e4@example.com"))
        e4_id = e4_user.id
        s.add(
            QuestionAnswer(
                user_id=e4_id,
                question_id=q4["id"],
                subtopic_id=subtopic_id,
                attempt_id=str(uuid.uuid4()),
                selected_index=1,
                is_correct=False,
            )
        )
        s.commit()

    resp = client.delete(f"/api/content/questions/{q4['id']}", headers=t4)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["deleted"] is False
    assert body["archived"] is True

    with SessionLocal() as s:
        question = s.get(Question, q4["id"])
        assert question is not None
        assert question.status == QuestionStatus.REJECTED
