"""Tests de POST /api/quiz/answers (calificación en servidor).

Cubre: respuesta correcta/incorrecta, idempotencia por (attempt_id,
question_id), 422 fuera de rango, 404 para preguntas no aprobadas, 403 sin
acceso al subtema, 401 sin token, y el nuevo payload de estudiante SIN
correct_index ni explanation (el de profesor SÍ los trae).
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
from app.models.question_meta import QuestionStatus


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


VALID_Q = {
    "prompt": "¿Qué estructura separa la cámara anterior de la posterior?",
    "options": ["El iris", "La córnea", "El cristalino", "La retina"],
    "correct_index": 0,
    "explanation": "El iris separa ambas cámaras del ojo.",
}


@pytest.fixture(scope="module")
def scenario(client):
    """Profesor con curso + pregunta aprobada; estudiante inscrito en el curso."""
    teacher = auth_headers(client, "quiz-profe@example.com", "Quiz Profe", "TEACHER")
    course = client.post(
        "/api/courses",
        json={"name": "Curso Quiz", "description": "Curso para tests de respuestas"},
        headers=teacher,
    ).json()

    student = auth_headers(client, "quiz-est@example.com", "Quiz Est", "STUDENT")
    outsider = auth_headers(client, "quiz-out@example.com", "Quiz Out", "STUDENT")
    join = client.post("/api/courses/join", json={"code": course["code"]}, headers=student)
    assert join.status_code == 200, join.text

    subtopic_id = None
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id

    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions", json=VALID_Q, headers=teacher
    )
    assert resp.status_code == 201, resp.text
    question = resp.json()

    return {
        "teacher": teacher,
        "student": student,
        "outsider": outsider,
        "course": course,
        "subtopic_id": subtopic_id,
        "question": question,
    }


def test_student_payload_has_no_correct_answer(client, scenario):
    """El quiz del estudiante NO incluye correct_index ni explanation."""
    resp = client.get(
        f"/api/subtopics/{scenario['subtopic_id']}",
        params={"course_id": scenario["course"]["id"]},
        headers=scenario["student"],
    )
    assert resp.status_code == 200, resp.text
    for question in resp.json()["questions"]:
        assert "correct_index" not in question
        assert "explanation" not in question
        assert "prompt" in question
        assert "options" in question


def test_teacher_payload_includes_correct_answer(client, scenario):
    """El banco del profesor SÍ incluye correct_index y explanation."""
    resp = client.get(
        f"/api/content/subtopics/{scenario['subtopic_id']}/questions/bank",
        headers=scenario["teacher"],
    )
    assert resp.status_code == 200, resp.text
    bank = resp.json()
    assert len(bank) >= 1
    assert "correct_index" in bank[0]
    assert "explanation" in bank[0]


def test_answer_correct_and_wrong(client, scenario):
    attempt = str(uuid.uuid4())
    qid = scenario["question"]["id"]

    resp = client.post(
        "/api/quiz/answers",
        json={"question_id": qid, "selected_index": 0, "attempt_id": attempt},
        headers=scenario["student"],
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["is_correct"] is True
    assert data["correct_index"] == 0
    assert data["explanation"] == VALID_Q["explanation"]

    # Incorrecta: otro intento distinto
    attempt2 = str(uuid.uuid4())
    resp2 = client.post(
        "/api/quiz/answers",
        json={"question_id": qid, "selected_index": 1, "attempt_id": attempt2},
        headers=scenario["student"],
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["is_correct"] is False
    assert resp2.json()["correct_index"] == 0


def test_answer_idempotent(client, scenario):
    """(attempt_id, question_id) único: repetir devuelve el resultado guardado."""
    attempt = str(uuid.uuid4())
    qid = scenario["question"]["id"]

    first = client.post(
        "/api/quiz/answers",
        json={"question_id": qid, "selected_index": 2, "attempt_id": attempt},
        headers=scenario["student"],
    )
    assert first.status_code == 200
    assert first.json()["is_correct"] is False

    second = client.post(
        "/api/quiz/answers",
        json={"question_id": qid, "selected_index": 0, "attempt_id": attempt},
        headers=scenario["student"],
    )
    assert second.status_code == 200
    # No cambia la respuesta ni crea duplicado: devuelve la guardada.
    assert second.json()["is_correct"] is False

    with SessionLocal() as s:
        from app.models.question_answer import QuestionAnswer
        from uuid import UUID  # noqa: F401

        count = len(
            s.scalars(
                select(QuestionAnswer).where(
                    QuestionAnswer.attempt_id == attempt,
                    QuestionAnswer.question_id == qid,
                )
            ).all()
        )
        assert count == 1


def test_answer_selected_index_out_of_range_422(client, scenario):
    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["question"]["id"],
            "selected_index": 4,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["student"],
    )
    assert resp.status_code == 422
    resp2 = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["question"]["id"],
            "selected_index": -1,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["student"],
    )
    assert resp2.status_code == 422


def test_answer_non_approved_question_404(client, scenario):
    """Una pregunta pending/rejected no responde (404)."""
    teacher = scenario["teacher"]
    subtopic_id = scenario["subtopic_id"]
    # Crea y luego la rechaza vía review (source=teacher no permite review);
    # en su lugar la inserta directo con status pending en la BD.
    with SessionLocal() as s:
        pending = Question(
            subtopic_id=subtopic_id,
            prompt="¿Pregunta pendiente de quiz?",
            options=["a", "b", "c", "d"],
            correct_index=1,
            explanation="",
            order=999,
            source="teacher",
            status=QuestionStatus.PENDING,
        )
        s.add(pending)
        s.commit()
        pending_id = pending.id

    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": pending_id,
            "selected_index": 1,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["student"],
    )
    assert resp.status_code == 404, resp.text


def test_answer_without_subtopic_access_403(client, scenario):
    """Estudiante sin acceso al subtema → 403.

    El outsider solo pertenece al Curso General; se deshabilita el topic del
    subtema en ese curso para forzar la denegación (el estudiante del
    escenario sigue con acceso por el curso del profesor).
    """
    outsider_courses = client.get("/api/courses", headers=scenario["outsider"]).json()
    general_id = next(c["id"] for c in outsider_courses if c["type"] == "GENERAL")

    with SessionLocal() as s:
        from app.models.content import CourseTopic

        subtopic = s.get(Subtopic, scenario["subtopic_id"])
        ct = s.scalar(
            select(CourseTopic).where(
                CourseTopic.course_id == general_id,
                CourseTopic.topic_id == subtopic.topic_id,
            )
        )
        assert ct is not None
        ct.enabled = False
        s.commit()

    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["question"]["id"],
            "selected_index": 0,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["outsider"],
    )
    assert resp.status_code == 403, resp.text


def test_answer_without_token_401(client, scenario):
    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["question"]["id"],
            "selected_index": 0,
            "attempt_id": str(uuid.uuid4()),
        },
    )
    assert resp.status_code == 401


def test_answer_invalid_attempt_id_422(client, scenario):
    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["question"]["id"],
            "selected_index": 0,
            "attempt_id": "no-es-un-uuid",
        },
        headers=scenario["student"],
    )
    assert resp.status_code == 422
