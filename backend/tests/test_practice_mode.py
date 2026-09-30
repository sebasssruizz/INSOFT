"""Tests del modo práctica (POST /api/practice/sessions).

Cubre: composición banco→IA, reutilización sin LLM, exclusión de acertadas /
prioridad de falladas, degradación si la IA falla, 404 sin preguntas, tope
diario por subtema, autorización (401/403/422), payload sin respuesta
correcta, aislamiento de las preguntas practice (quiz normal, cola pendientes,
conteos), calificación de practice en /quiz/answers, privacidad de consultas
ajenas y rate limit. LLM siempre mockeado.
"""
import os
import uuid
from unittest.mock import AsyncMock, patch

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-test"
os.environ["PRACTICE_RATE_LIMIT"] = "30/hour"
os.environ["PRACTICE_MAX_GENERATIONS_PER_SUBTOPIC_PER_DAY"] = "4"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Question, Subtopic
from app.models.question_answer import QuestionAnswer
from app.models.question_meta import QuestionStatus
from app.models.ai_query import AiQuery
from app.models.user import User


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _create_question(db, subtopic_id, prompt, source="teacher", status=QuestionStatus.APPROVED, **kw):
    question = Question(
        subtopic_id=subtopic_id,
        prompt=prompt,
        options=["a", "b", "c", "d"],
        correct_index=0,
        explanation="exp",
        order=kw.pop("order", 999),
        source=source,
        status=status,
        **kw,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


VALID_LLM_JSON = (
    '{"questions":[{"prompt":"¿Pregunta generada por IA de práctica?","options":'
    '["una","dos","tres","cuatro"],"correct_index":2,"explanation":"explicación IA"}]}'
)

VALID_LLM_JSON_TWO = (
    '{"questions":['
    '{"prompt":"¿Pregunta IA de práctica uno?","options":["i1","i2","i3","i4"],'
    '"correct_index":1,"explanation":"exp1"},'
    '{"prompt":"¿Pregunta IA de práctica dos?","options":["j1","j2","j3","j4"],'
    '"correct_index":3,"explanation":"exp2"}'
    ']}'
)


@pytest.fixture(scope="module")
def scenario(client):
    """Profesor con curso, estudiante inscrito, banco y pool practice sembrado."""
    teacher = auth_headers(client, "pract-profe@example.com", "Pract Profe", "TEACHER")
    course = client.post(
        "/api/courses", json={"name": "Curso Practica", "description": ""}, headers=teacher
    ).json()
    student = auth_headers(client, "pract-est@example.com", "Pract Est", "STUDENT")
    peer = auth_headers(client, "pract-peer@example.com", "Pract Peer", "STUDENT")
    assert client.post("/api/courses/join", json={"code": course["code"]}, headers=student).status_code == 200
    assert client.post("/api/courses/join", json={"code": course["code"]}, headers=peer).status_code == 200
    outsider = auth_headers(client, "pract-out@example.com", "Pract Out", "STUDENT")

    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
        # Indexa un chunk (el generador IA del pipeline lo requiere)
        from app.repositories import subtopic_chunk_repository as chunk_repo
        from app.services.embeddings_service import embed_text

        content = "contenido de oftalmología para practicar"
        chunk_repo.create(s, subtopic_id=subtopic_id, content=content, embedding=embed_text(content))
        # Banco: 4 aprobadas (3 docente + 1 oficial)
        bank = [
            _create_question(s, subtopic_id, "¿Banco docente uno?", source="teacher", order=1),
            _create_question(s, subtopic_id, "¿Banco docente dos?", source="teacher", order=2),
            _create_question(s, subtopic_id, "¿Banco docente tres?", source="teacher", order=3),
            _create_question(s, subtopic_id, "¿Banco oficial uno?", source="official", order=4),
        ]
        # Pool de práctica reutilizable (3 preguntas sin responder)
        practice = [
            _create_question(
                s,
                subtopic_id,
                f"¿Práctica IA {i}?",
                source="ai",
                status=QuestionStatus.PRACTICE,
                order=10 + i,
            )
            for i in range(1, 4)
        ]
        # Consulta del PEER al asistente (texto privado, solo agregados)
        peer_user = s.scalar(select(User).where(User.email == "pract-peer@example.com"))
        s.add(
            AiQuery(
                user_id=peer_user.id,
                subtopic_id=subtopic_id,
                question_original="TEXTO-SECRETO-DEL-PEER-42",
                respuesta="respuesta privada",
            )
        )
        s.commit()
        # Extraer valores ANTES de cerrar la sesión (objetos detached después)
        bank_data = [{"id": q.id, "source": q.source} for q in bank]
        practice_data = [{"id": q.id, "prompt": q.prompt} for q in practice]

    return {
        "teacher": teacher,
        "student": student,
        "outsider": outsider,
        "course": course,
        "subtopic_id": subtopic_id,
        "bank": bank_data,
        "practice": practice_data,
    }


def _no_llm(mock_call):
    """Configura el mock para FALLAR si alguien intenta llamar al LLM."""
    mock_call.side_effect = AssertionError("No se debía llamar al LLM")


def test_composition_reuses_pool_without_llm(client, scenario):
    with patch(
        "app.services.ai_service.call_openrouter", new_callable=AsyncMock
    ) as mock_call:
        _no_llm(mock_call)
        resp = client.post(
            "/api/practice/sessions",
            json={"subtopic_id": scenario["subtopic_id"], "count": 5},
            headers=scenario["student"],
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["composition"] == {"bank": 3, "ai": 2}  # ceil(5*0.6)=3 banco, 2 IA
    assert data["mode"] == "practice"
    assert data["ai_available"] is True
    uuid.UUID(data["attempt_id"])  # attempt_id UUID válido
    assert len(data["questions"]) == 5
    mock_call.assert_not_called()  # el pool de práctica alcanzó: sin LLM

    ids = {q["id"] for q in data["questions"]}
    assert ids.isdisjoint({q["id"] for q in scenario["practice"]}) is False
    for q in data["questions"]:
        assert "correct_index" not in q
        assert "explanation" not in q
        expected_ai = q["id"] in {p["id"] for p in scenario["practice"]}
        assert q["is_ai_generated"] is expected_ai

    # Privacidad: no aparece el texto de consultas ajenas
    body = resp.text
    assert "TEXTO-SECRETO-DEL-PEER-42" not in body
    assert "respuesta privada" not in body


def test_excludes_recently_correct_and_prioritizes_failed(client, scenario):
    student_id = None
    with SessionLocal() as s:
        from app.models.user import User

        user = s.scalar(select(User).where(User.email == "pract-est@example.com"))
        student_id = user.id
        correct_q, failed_q = scenario["bank"][0]["id"], scenario["bank"][1]["id"]
        s.add_all(
            [
                QuestionAnswer(
                    user_id=student_id,
                    question_id=correct_q,
                    subtopic_id=scenario["subtopic_id"],
                    attempt_id=str(uuid.uuid4()),
                    selected_index=0,
                    is_correct=True,
                ),
                QuestionAnswer(
                    user_id=student_id,
                    question_id=failed_q,
                    subtopic_id=scenario["subtopic_id"],
                    attempt_id=str(uuid.uuid4()),
                    selected_index=1,
                    is_correct=False,
                ),
            ]
        )
        s.commit()

    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as mock_call:
        _no_llm(mock_call)
        resp = client.post(
            "/api/practice/sessions",
            json={"subtopic_id": scenario["subtopic_id"], "count": 5},
            headers=scenario["student"],
        )
    assert resp.status_code == 200
    data = resp.json()
    ids = [q["id"] for q in data["questions"]]
    bank_ids = {q["id"] for q in scenario["bank"]}
    picked_bank = [qid for qid in ids if qid in bank_ids]
    # La acertada hace 0 días NO puede volver a salir; la fallada sí.
    assert scenario["bank"][0]["id"] not in ids
    assert scenario["bank"][1]["id"] in ids
    assert data["composition"]["bank"] == 3


def test_llm_generation_when_pool_insufficient(client, scenario):
    """Sin practice disponibles: genera con el LLM (mockeado) el faltante."""
    with SessionLocal() as s:
        # Marca las practice como respondidas por el estudiante → pool vacío.
        from app.models.user import User

        user = s.scalar(select(User).where(User.email == "pract-est@example.com"))
        s.add_all(
            [
                QuestionAnswer(
                    user_id=user.id,
                    question_id=q["id"],
                    subtopic_id=scenario["subtopic_id"],
                    attempt_id=str(uuid.uuid4()),
                    selected_index=0,
                    is_correct=False,
                )
                for q in scenario["practice"]
            ]
        )
        s.commit()

    with patch(
        "app.services.ai_service.call_openrouter", new_callable=AsyncMock
    ) as mock_call:
        mock_call.side_effect = [VALID_LLM_JSON_TWO]
        resp = client.post(
            "/api/practice/sessions",
            json={"subtopic_id": scenario["subtopic_id"], "count": 5},
            headers=scenario["student"],
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["composition"] == {"bank": 3, "ai": 2}
    assert data["ai_available"] is True
    mock_call.assert_called_once()  # 1 llamada: justo el faltante (máx 2)
    ai_questions = [q for q in data["questions"] if q["is_ai_generated"]]
    assert len(ai_questions) == 2


def test_llm_failure_degrades_to_bank(client, scenario):
    """Fallo del proveedor: completa con banco y ai_available=false, sin 5xx.

    Subtema propio con solo banco (sin pool practice y sin tope diario
    consumido): la generación IA falla y la sesión sale igual, con banco.
    """
    with SessionLocal() as s:
        from app.repositories import subtopic_chunk_repository as chunk_repo
        from app.services.embeddings_service import embed_text

        subtopic = Subtopic(topic_id=1, name="Subtema degradación IA", content="contenido", order=997)
        s.add(subtopic)
        s.commit()
        degrade_subtopic_id = subtopic.id
        chunk_repo.create(
            s,
            subtopic_id=subtopic.id,
            content="contenido de oftalmología para degradar",
            embedding=embed_text("contenido de oftalmología para degradar"),
        )
        for i in range(3):
            _create_question(s, subtopic.id, f"¿Banco degradación {i}?", order=80 + i)

    with patch(
        "app.services.ai_service.call_openrouter", new_callable=AsyncMock
    ) as mock_call:
        from app.core.openrouter_client import OpenRouterSaturatedError

        mock_call.side_effect = OpenRouterSaturatedError("límite global")
        resp = client.post(
            "/api/practice/sessions",
            json={"subtopic_id": degrade_subtopic_id, "count": 5},
            headers=scenario["student"],
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ai_available"] is False
    assert data["composition"] == {"bank": 3, "ai": 0}
    assert len(data["questions"]) == 3  # solo banco


def test_practice_404_when_nothing_available(client, scenario):
    """Subtema sin banco ni practice ni chunks → 404 amable."""
    with SessionLocal() as s:
        subtopic = Subtopic(topic_id=1, name="Subtema sin nada", content="sin contenido", order=999)
        s.add(subtopic)
        s.commit()
        empty_id = subtopic.id

    resp = client.post(
        "/api/practice/sessions",
        json={"subtopic_id": empty_id},
        headers=scenario["student"],
    )
    assert resp.status_code == 404, resp.text
    assert "no hay preguntas" in resp.json()["detail"].lower()


def test_daily_generation_cap_per_subtopic(client, scenario):
    """Tope diario: alcanzado el cap, no genera aunque el pool no alcance."""
    with SessionLocal() as s:
        from app.models.user import User

        user = s.scalar(select(User).where(User.email == "pract-est@example.com"))
        subtopic = Subtopic(topic_id=1, name="Subtema tope diario", content="contenido", order=998)
        s.add(subtopic)
        s.commit()
        cap_subtopic_id = subtopic.id

        _create_question(s, subtopic.id, "¿Banco del tope diario?", order=60)
        practice_qs = [
            _create_question(
                s,
                subtopic.id,
                f"¿Práctica tope {i}?",
                status=QuestionStatus.PRACTICE,
                order=70 + i,
            )
            for i in range(4)
        ]
        # 3 de las 4 practice respondidas por el usuario → pool reutilizable = 1
        s.add_all(
            [
                QuestionAnswer(
                    user_id=user.id,
                    question_id=q.id,
                    subtopic_id=subtopic.id,
                    attempt_id=str(uuid.uuid4()),
                    selected_index=0,
                    is_correct=False,
                )
                for q in practice_qs[:3]
            ]
        )
        s.commit()

    with patch(
        "app.services.ai_service.call_openrouter", new_callable=AsyncMock
    ) as mock_call:
        _no_llm(mock_call)
        resp = client.post(
            "/api/practice/sessions",
            json={"subtopic_id": cap_subtopic_id, "count": 5},
            headers=scenario["student"],
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    mock_call.assert_not_called()  # 4 creadas hoy ≥ cap: sin llamadas al LLM
    assert data["composition"] == {"bank": 1, "ai": 1}
    assert data["ai_available"] is True


def test_authorization(client, scenario):
    # Sin token
    resp = client.post(
        "/api/practice/sessions", json={"subtopic_id": scenario["subtopic_id"]}
    )
    assert resp.status_code == 401

    # Sin acceso al subtema (estudiante no inscrito): forzamos 403 deshabilitando
    # el topic en el Curso General (el outsider solo pertenece a ese curso).
    outsider_courses = client.get("/api/courses", headers=scenario["outsider"]).json()
    general_id = next(c["id"] for c in outsider_courses if c["type"] == "GENERAL")
    with SessionLocal() as s:
        from app.models.content import CourseTopic

        subtopic = s.get(Subtopic, scenario["subtopic_id"])
        ct = s.scalar(
            select(CourseTopic).where(
                CourseTopic.course_id == general_id, CourseTopic.topic_id == subtopic.topic_id
            )
        )
        if ct:
            ct.enabled = False
            s.commit()

    resp = client.post(
        "/api/practice/sessions",
        json={"subtopic_id": scenario["subtopic_id"]},
        headers=scenario["outsider"],
    )
    assert resp.status_code == 403, resp.text

    # Ambos ids juntos (y ninguno) → 422
    resp = client.post(
        "/api/practice/sessions",
        json={"subtopic_id": scenario["subtopic_id"], "topic_id": 1},
        headers=scenario["student"],
    )
    assert resp.status_code == 422
    resp = client.post("/api/practice/sessions", json={}, headers=scenario["student"])
    assert resp.status_code == 422

    # count fuera de rango → 422
    resp = client.post(
        "/api/practice/sessions",
        json={"subtopic_id": scenario["subtopic_id"], "count": 11},
        headers=scenario["student"],
    )
    assert resp.status_code == 422


def test_practice_questions_isolated_from_regular_quiz(client, scenario):
    """Las practice no salen en el quiz normal ni en la cola de pendientes."""
    subtopic_id = scenario["subtopic_id"]
    resp = client.get(
        f"/api/subtopics/{subtopic_id}", params={"course_id": scenario["course"]["id"]},
        headers=scenario["student"],
    )
    assert resp.status_code == 200
    quiz_ids = {q["id"] for q in resp.json()["questions"]}
    assert quiz_ids.isdisjoint({q["id"] for q in scenario["practice"]})

    resp = client.get(
        f"/api/content/subtopics/{subtopic_id}/questions/bank",
        params={"status": "pending"},
        headers=scenario["teacher"],
    )
    assert resp.status_code == 200
    assert all(q["id"] not in {p["id"] for p in scenario["practice"]} for q in resp.json())

    # El resumen del banco cuenta practice por separado (no como aprobadas)
    with SessionLocal() as s:
        subtopic = s.get(Subtopic, subtopic_id)
        topic_id = subtopic.topic_id
    resp = client.get(
        f"/api/content/topics/{topic_id}/questions/summary",
        headers=scenario["teacher"],
    )
    assert resp.status_code == 200
    summary = {item["subtopic_id"]: item for item in resp.json()}
    assert summary[subtopic_id]["practice"] >= 3
    # La suma de estados + práctica da el total (la práctica no es "approved")
    item = summary[subtopic_id]
    assert (
        item["approved"] + item["pending"] + item["rejected"] + item["practice"]
        == item["total"]
    )


def test_quiz_answers_accepts_practice(client, scenario):
    """POST /api/quiz/answers califica preguntas practice."""
    target = scenario["practice"][0]["id"]
    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": target,
            "selected_index": 0,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["student"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_correct"] is True  # correct_index=0 en el seed


def test_quiz_stats_distinguish_origin(client, scenario):
    """Las stats de quiz marcan el origen (banco | practica)."""
    # Respuesta a una pregunta practice
    resp = client.post(
        "/api/quiz/answers",
        json={
            "question_id": scenario["practice"][0]["id"],
            "selected_index": 0,
            "attempt_id": str(uuid.uuid4()),
        },
        headers=scenario["student"],
    )
    assert resp.status_code == 200

    resp = client.get("/api/quiz/stats/overview", headers=scenario["teacher"])
    stats = resp.json()
    assert stats["respuestas_practica"] >= 1

    resp = client.get("/api/quiz/stats/questions", headers=scenario["teacher"])
    by_id = {q["question_id"]: q for q in resp.json()["questions"]}
    assert by_id[scenario["practice"][0]["id"]]["origen"] == "practica"
    assert by_id[scenario["bank"][0]["id"]]["origen"] == "banco"

    resp = client.get("/api/quiz/stats/export.csv", headers=scenario["teacher"])
    assert "origen" in resp.text.splitlines()[0]


def test_rate_limit_429(client, scenario):
    """429 al superar PRACTICE_RATE_LIMIT."""
    # Módulo de tests con límite 2/hour forzado via env… si el decorador
    # capturó el valor por request (callable) esto funciona:
    from app.core.config import settings as live_settings

    original = live_settings.PRACTICE_RATE_LIMIT
    live_settings.PRACTICE_RATE_LIMIT = "2/hour"
    try:
        codes = []
        for _ in range(3):
            resp = client.post(
                "/api/practice/sessions",
                json={"subtopic_id": scenario["subtopic_id"], "count": 1},
                headers=scenario["student"],
            )
            codes.append(resp.status_code)
        assert codes[:2] == [200, 200] or codes[0] == 200
        assert codes[-1] == 429, codes
    finally:
        live_settings.PRACTICE_RATE_LIMIT = original
