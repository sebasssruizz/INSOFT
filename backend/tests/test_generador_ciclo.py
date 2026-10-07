"""Ciclo completo del generador (T4): generación → cola pending → revisar →
reflejo en el repaso del estudiante y el modo práctica.

Siempre con el LLM mockeado: ninguna llamada a OpenRouter/Gemini.
"""
import json
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""
# Sin tope de muestreo para que las aserciones del repaso sean deterministas.
os.environ.setdefault("QUIZ_MAX_QUESTIONS", "200")

from unittest.mock import AsyncMock, patch  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.content import Subtopic  # noqa: E402
from app.repositories import subtopic_chunk_repository as chunk_repo  # noqa: E402
from app.services.embeddings_service import embed_text  # noqa: E402


def _question_json(prompt, correct_index=0):
    return {
        "prompt": prompt,
        "options": ["opción A", "opción B", "opción C", "opción D"],
        "correct_index": correct_index,
        "explanation": "Vinculada al contenido indexado en el mock.",
    }


def _payload(questions):
    return json.dumps({"questions": questions}, ensure_ascii=False)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def ids(client):
    teacher = _login(client, "gen-owner@x.com", "TEACHER")
    student = _login(client, "gen-est@x.com", "STUDENT")
    course = client.post("/api/courses", json={"name": "Gen Curso"}, headers=teacher).json()
    assert client.post(
        "/api/courses/join", json={"code": course["code"]}, headers=student
    ).status_code == 200
    topic = client.get(f"/api/courses/{course['id']}/topics", headers=teacher).json()[0]
    subtopic_id = topic["subtopics"][0]["id"]
    with SessionLocal() as s:
        chunk_repo.create(
            s, subtopic_id=subtopic_id, content="la córnea y el trépano en el trasplante",
            embedding=embed_text("la córnea y el trépano"),
        )
    return {
        "teacher": teacher,
        "student": student,
        "course_id": course["id"],
        "topic_id": topic["id"],
        "subtopic_id": subtopic_id,
    }


def _login(client, email, role):
    r = client.post("/api/auth/dev", json={"email": email, "name": "N", "role": role})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_generacion_pending_no_visible_y_aprobacion_refleja(client, ids):
    # 1. Genera 2 preguntas (mock): source=ai, status=pending
    mock = AsyncMock(return_value=_payload(
        [
            _question_json(f"¿Pregunta generada pendiente {i} del ciclo?") for i in (1, 2)
        ]
    ))
    with patch("app.services.ai_service._call_llm_for_questions", mock):
        resp = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": ids["subtopic_id"], "count": 2},
            headers=ids["teacher"],
        )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created"] == 2
    assert all(q["status"] == "pending" and q["source"] == "ai" for q in data["generated"])
    pending_ids = [q["id"] for q in data["generated"]]

    # 2. NO visibles en el repaso del estudiante
    quests = client.get(
        f"/api/topics/{ids['topic_id']}/questions",
        params={"course_id": ids["course_id"]},
        headers=ids["student"],
    ).json()
    assert all(q["id"] not in pending_ids for q in quests)

    # 3. Aprobar una -> AHORA sí aparece en el repaso
    r_ap = client.post(
        f"/api/content/questions/{pending_ids[0]}/review",
        json={"action": "approve"},
        headers=ids["teacher"],
    )
    assert r_ap.status_code == 200, r_ap.text
    quests = client.get(
        f"/api/topics/{ids['topic_id']}/questions",
        params={"course_id": ids["course_id"]},
        headers=ids["student"],
    ).json()
    assert any(q["id"] == pending_ids[0] for q in quests)

    # 4. Rechazar la otra -> sigue oculta y no visible en práctica del banco
    r_rj = client.post(
        f"/api/content/questions/{pending_ids[1]}/review",
        json={"action": "reject"},
        headers=ids["teacher"],
    )
    assert r_rj.status_code == 200, r_rj.text
    quests = client.get(
        f"/api/topics/{ids['topic_id']}/questions",
        params={"course_id": ids["course_id"]},
        headers=ids["student"],
    ).json()
    assert all(q["id"] != pending_ids[1] for q in quests)


def test_json_invalido_tras_reintentos_502(client, ids):
    mock = AsyncMock(return_value="el modelo respondió basura sin JSON }{")
    with patch("app.services.ai_service._call_llm_for_questions", mock):
        resp = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": ids["subtopic_id"], "count": 2},
            headers=ids["teacher"],
        )
    assert resp.status_code == 502, resp.text
    assert "preguntas válidas" in resp.json()["detail"].lower()


def test_dedupe_contra_existentes(client, ids):
    """Un LLM carta repetido no crea duplicados: se filtra entre generadas y ya existentes."""
    # genera una pregunta real aprobada
    resp = None
    mock = AsyncMock(return_value=_payload([_question_json("¿Pregunta repetida base del cíclo?", 1)]))
    with patch("app.services.ai_service._call_llm_for_questions", mock):
        resp = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": ids["subtopic_id"], "count": 1},
            headers=ids["teacher"],
        )
    q_prompt = resp.json()["generated"][0]["prompt"]
    client.post(
        f"/api/content/questions/{resp.json()['generated'][0]['id']}/review",
        json={"action": "approve"},
        headers=ids["teacher"],
    )
    # ahora pedimos AL LLM (que siempre responde lo mismo) más preguntas:
    mock2 = AsyncMock(return_value=_payload([_question_json(q_prompt, 1)]))
    with patch("app.services.ai_service._call_llm_for_questions", mock2):
        resp2 = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": ids["subtopic_id"], "count": 1},
            headers=ids["teacher"],
        )
    # se filtra por duplicado -> 502 con 0 creaciones
    assert resp2.status_code == 502, resp2.text


def test_count_fuera_de_lote_422(client, ids):
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": ids["subtopic_id"], "count": 7},
        headers=ids["teacher"],
    )
    assert resp.status_code == 422, resp.text
