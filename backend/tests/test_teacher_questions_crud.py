"""Tests del CRUD de preguntas del profesor (banco, creación, edición,
borrado, revisión IA) y del tope de preguntas del quiz.

Todo con SQLite vía conftest y login de desarrollo; sin llamadas de red.
"""
import os

os.environ["DEV_AUTH_ENABLED"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Question, Subtopic
from app.models.question_meta import QuestionSource, QuestionStatus
from app.services.question_service import normalize_prompt


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


VALID_Q = {
    "prompt": "¿Cuál es la cámara del ojo entre el iris y la córnea?",
    "options": ["Cámara anterior", "Cámara posterior", "Cavidad vítrea", "Canal de Schlemm"],
    "correct_index": 0,
    "explanation": "La cámara anterior queda entre córnea e iris.",
}


@pytest.fixture(scope="module")
def teacher(client):
    headers = auth_headers(client, "qcrud-profe@example.com", "QCrud Profe", "TEACHER")
    # Crea un curso propio para que el profesor tenga todos los topics habilitados
    resp = client.post(
        "/api/courses",
        json={"name": "Curso QCrud", "description": "Curso del profesor de tests"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return headers


@pytest.fixture(scope="module")
def other_teacher(client):
    headers = auth_headers(client, "qcrud-profe2@example.com", "QCrud Profe 2", "TEACHER")
    resp = client.post(
        "/api/courses",
        json={"name": "Curso QCrud Otro", "description": "Curso del otro profesor"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return headers


@pytest.fixture(scope="module")
def student(client):
    return auth_headers(client, "qcrud-est@example.com", "QCrud Est", "STUDENT")


@pytest.fixture(scope="module")
def subtopic_id(client, teacher):
    """Subtema real (contenido oficial enlazado a los cursos del profesor)."""
    with SessionLocal() as s:
        return s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id


def _bank(client, headers, subtopic_id):
    return client.get(f"/api/content/subtopics/{subtopic_id}/questions/bank", headers=headers)


# ── Creación ────────────────────────────────────────────────────────────────


def test_crear_pregunta_valida_201(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions", json=VALID_Q, headers=teacher
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["source"] == QuestionSource.TEACHER
    assert data["status"] == QuestionStatus.APPROVED
    assert data["created_by"] is not None
    assert data["is_owner"] is True
    assert len(data["options"]) == 4


def test_validaciones_422(client, teacher, subtopic_id):
    # 3 opciones
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "options": VALID_Q["options"][:3]},
        headers=teacher,
    )
    assert resp.status_code == 422
    # 5 opciones
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "options": VALID_Q["options"] + ["Extra"]},
        headers=teacher,
    )
    assert resp.status_code == 422
    # opción vacía
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "options": ["", "b", "c", "d"]},
        headers=teacher,
    )
    assert resp.status_code == 422
    # duplicadas
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "options": ["igual", "Igual ", "c", "d"]},
        headers=teacher,
    )
    assert resp.status_code == 422
    # correct_index fuera de rango
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "correct_index": 4},
        headers=teacher,
    )
    assert resp.status_code == 422
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "correct_index": -1},
        headers=teacher,
    )
    assert resp.status_code == 422
    # enunciado corto
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "prompt": "abc"},
        headers=teacher,
    )
    assert resp.status_code == 422


def test_permisos_creacion(client, teacher, other_teacher, student, subtopic_id):
    # estudiante → 403
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions", json=VALID_Q, headers=student
    )
    assert resp.status_code == 403
    # sin token → 401
    resp = client.post(f"/api/content/subtopics/{subtopic_id}/questions", json=VALID_Q)
    assert resp.status_code == 401
    # subtema inexistente → 404
    resp = client.post(
        "/api/content/subtopics/999999/questions", json=VALID_Q, headers=teacher
    )
    assert resp.status_code == 404


def test_enunciado_duplicado_409(client, teacher, subtopic_id):
    # El VALID_Q ya fue creado por tests anteriores; reutilízalo como base
    # Mismo enunciado con variación de espacios/mayúsculas → 409
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={**VALID_Q, "prompt": "  ¿cuál   ES la cámara del ojo entre el iris y la córnea? "},
        headers=teacher,
    )
    assert resp.status_code == 409, resp.text


def test_profesor_sin_curso_con_el_subtema_403(client, subtopic_id):
    """Un profesor sin cursos no puede crear preguntas."""
    headers = auth_headers(client, "qcrud-profe-solo@example.com", "Profe Sin Curso", "TEACHER")
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions", json=VALID_Q, headers=headers
    )
    assert resp.status_code == 403


def test_estudiante_403_bank(client, student, subtopic_id):
    """Un estudiante no puede ver el banco del profesor."""
    resp = _bank(client, student, subtopic_id)
    assert resp.status_code == 403


# ── Visibilidad inmediata para estudiantes ─────────────────────────────────


def test_pregunta_creada_visible_en_quiz(client, teacher, student, subtopic_id):
    unique_prompt = "¿Instrumento para medir la presión intraocular?"
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": unique_prompt,
            "options": ["Tonómetro", "Biomicroscopio", "Oftalmoscopio", "Retinógrafo"],
            "correct_index": 0,
        },
        headers=teacher,
    )
    assert resp.status_code == 201

    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(
        f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student
    )
    assert resp.status_code == 200
    prompts = [q["prompt"] for q in resp.json()["questions"]]
    assert unique_prompt in prompts
    # El estudiante no ve metadatos de profesor
    first = resp.json()["questions"][0]
    assert "source" not in first and "status" not in first and "created_by" not in first


# ── Edición ────────────────────────────────────────────────────────────────


def test_patch_autor_edita(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={
            "prompt": "¿Pregunta editable del profesor?",
            "options": ["a", "b", "c", "d"],
            "correct_index": 2,
        },
        headers=teacher,
    )
    qid = resp.json()["id"]
    resp = client.patch(
        f"/api/content/questions/{qid}",
        json={"prompt": "¿Pregunta editada del profesor?", "correct_index": 1},
        headers=teacher,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["prompt"] == "¿Pregunta editada del profesor?"
    assert data["correct_index"] == 1
    assert data["options"] == ["a", "b", "c", "d"]


def test_patch_otro_profesor_403(client, teacher, other_teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Pregunta del profesor uno?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    resp = client.patch(
        f"/api/content/questions/{qid}", json={"prompt": "¿Intento del otro profesor?"}, headers=other_teacher
    )
    assert resp.status_code == 403


def test_patch_oficial_403(client, other_teacher, subtopic_id):
    """Una pregunta oficial no es editable por nadie desde el panel."""
    with SessionLocal() as s:
        official = s.scalars(
            select(Question).where(Question.subtopic_id == subtopic_id)
        ).all()
        target = next(q for q in official if q.source == QuestionSource.OFFICIAL)
        qid = target.id
    resp = client.patch(
        f"/api/content/questions/{qid}", json={"prompt": "¿Editar oficial?"}, headers=other_teacher
    )
    assert resp.status_code == 403
    assert "solo lectura" in resp.json()["detail"].lower()


def test_patch_ai_pendiente_no_la_aprueba(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Pregunta IA editable?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    with SessionLocal() as s:
        q = s.get(Question, qid)
        q.source = QuestionSource.AI
        q.status = QuestionStatus.PENDING
        s.commit()

    resp = client.patch(
        f"/api/content/questions/{qid}", json={"prompt": "¿Pregunta IA editada?"}, headers=teacher
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == QuestionStatus.PENDING


def test_patch_duplicado_409(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Enunciado duplicado patch uno?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid1 = resp.json()["id"]
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Enunciado duplicado patch dos?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid2 = resp.json()["id"]
    resp = client.patch(
        f"/api/content/questions/{qid2}",
        json={"prompt": "¿Enunciado duplicado patch uno?"},
        headers=teacher,
    )
    assert resp.status_code == 409


# ── Borrado ────────────────────────────────────────────────────────────────


def test_delete_autor_borra(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Pregunta por borrar?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    resp = client.delete(f"/api/content/questions/{qid}", headers=teacher)
    assert resp.status_code == 200, resp.text
    assert resp.json()["deleted"] is True
    with SessionLocal() as s:
        assert s.get(Question, qid) is None


def test_delete_otro_profesor_403(client, teacher, other_teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Pregunta ajena a borrar?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    resp = client.delete(f"/api/content/questions/{qid}", headers=other_teacher)
    assert resp.status_code == 403


def test_delete_inexistente_404(client, teacher):
    resp = client.delete("/api/content/questions/999999", headers=teacher)
    assert resp.status_code == 404


# ── Revisión IA ────────────────────────────────────────────────────────────


def _create_ai_pending(client, teacher, subtopic_id, prompt):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": prompt, "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    with SessionLocal() as s:
        q = s.get(Question, qid)
        q.source = QuestionSource.AI
        q.status = QuestionStatus.PENDING
        s.commit()
    return qid


def test_review_aprobar_hace_visible(client, teacher, student, subtopic_id):
    prompt = "¿Pregunta IA por aprobar?"
    qid = _create_ai_pending(client, teacher, subtopic_id, prompt)

    # No visible antes
    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student)
    assert prompt not in [q["prompt"] for q in resp.json()["questions"]]

    resp = client.post(
        f"/api/content/questions/{qid}/review", json={"action": "approve"}, headers=teacher
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == QuestionStatus.APPROVED

    # Visible después
    resp = client.get(f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student)
    assert prompt in [q["prompt"] for q in resp.json()["questions"]]


def test_review_rechazar_no_visible(client, teacher, student, subtopic_id):
    prompt = "¿Pregunta IA por rechazar?"
    qid = _create_ai_pending(client, teacher, subtopic_id, prompt)
    resp = client.post(
        f"/api/content/questions/{qid}/review", json={"action": "reject"}, headers=teacher
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == QuestionStatus.REJECTED

    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student)
    assert prompt not in [q["prompt"] for q in resp.json()["questions"]]


def test_review_de_pregunta_teacher_409(client, teacher, subtopic_id):
    resp = client.post(
        f"/api/content/subtopics/{subtopic_id}/questions",
        json={"prompt": "¿Pregunta docente no revisable?", "options": ["a", "b", "c", "d"], "correct_index": 0},
        headers=teacher,
    )
    qid = resp.json()["id"]
    resp = client.post(
        f"/api/content/questions/{qid}/review", json={"action": "approve"}, headers=teacher
    )
    assert resp.status_code == 409


def test_review_action_invalido_422(client, teacher, subtopic_id):
    qid = _create_ai_pending(client, teacher, subtopic_id, "¿Pregunta IA action raro?")
    resp = client.post(
        f"/api/content/questions/{qid}/review", json={"action": "publish"}, headers=teacher
    )
    assert resp.status_code == 422


# ── Banco y resumen ────────────────────────────────────────────────────────


def test_bank_devuelve_todos_los_estados(client, teacher, other_teacher, subtopic_id):
    _create_ai_pending(client, teacher, subtopic_id, "¿Banco pendiente uno?")
    resp = _bank(client, teacher, subtopic_id)
    assert resp.status_code == 200
    items = resp.json()
    statuses = {q["status"] for q in items}
    sources = {q["source"] for q in items}
    assert QuestionStatus.PENDING in statuses
    assert QuestionStatus.APPROVED in statuses
    assert QuestionSource.OFFICIAL in sources
    assert QuestionSource.TEACHER in sources
    assert QuestionSource.AI in sources
    # is_owner correcto
    assert all(q["is_owner"] for q in items if q["source"] == QuestionSource.TEACHER)

    # Filtros
    resp = _bank(client, teacher, subtopic_id)
    resp = client.get(
        f"/api/content/subtopics/{subtopic_id}/questions/bank?status=pending", headers=teacher
    )
    assert all(q["status"] == "pending" for q in resp.json())
    resp = client.get(
        f"/api/content/subtopics/{subtopic_id}/questions/bank?source=official", headers=teacher
    )
    assert all(q["source"] == "official" for q in resp.json())

    # Filtro inválido → 422
    resp = client.get(
        f"/api/content/subtopics/{subtopic_id}/questions/bank?status=bogus", headers=teacher
    )
    assert resp.status_code == 422


def test_summary_conteos_correctos(client, teacher, subtopic_id):
    with SessionLocal() as s:
        topic_id = s.get(Subtopic, subtopic_id).topic_id
    resp = client.get(f"/api/content/topics/{topic_id}/questions/summary", headers=teacher)
    assert resp.status_code == 200, resp.text
    summary = {item["subtopic_id"]: item for item in resp.json()}
    assert subtopic_id in summary
    item = summary[subtopic_id]
    # Verifica contra la realidad
    with SessionLocal() as s:
        questions = s.scalars(
            select(Question).where(Question.subtopic_id == subtopic_id)
        ).all()
    assert item["total"] == len(questions)
    assert item["approved"] == sum(1 for q in questions if q.status == "approved")
    assert item["pending"] == sum(1 for q in questions if q.status == "pending")
    assert item["official"] == sum(1 for q in questions if q.source == "official")


# ── Tope del quiz ──────────────────────────────────────────────────────────


def test_tope_quiz_max_questions(client, teacher, student, subtopic_id, monkeypatch):
    """Con más preguntas aprobadas que el tope, el estudiante recibe el tope."""
    from app.core.config import settings

    # Crea 3 preguntas únicas más
    for i in range(3):
        client.post(
            f"/api/content/subtopics/{subtopic_id}/questions",
            json={
                "prompt": f"¿Pregunta de tope número {i} sobre oftalmología?",
                "options": ["a", "b", "c", "d"],
                "correct_index": 0,
            },
            headers=teacher,
        )

    with SessionLocal() as s:
        approved_before = s.scalar(
            select(Question.id).where(
                Question.subtopic_id == subtopic_id, Question.status == "approved"
            )
        )
    # Fuerza un tope menor que la cantidad aprobada actual
    with SessionLocal() as s:
        total_approved = len(
            s.scalars(
                select(Question).where(
                    Question.subtopic_id == subtopic_id, Question.status == "approved"
                )
            ).all()
        )
    max_q = max(1, min(5, total_approved - 1))
    monkeypatch.setattr(settings, "QUIZ_MAX_QUESTIONS", max_q)

    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student)
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == max_q


def test_normalize_prompt_normaliza_igual():
    assert normalize_prompt("¿Qué   ES el glaucoma? ") == "qué es el glaucoma"
    assert normalize_prompt("que es el glaucoma.") == "que es el glaucoma"
    assert normalize_prompt("HOLA") == "hola"
