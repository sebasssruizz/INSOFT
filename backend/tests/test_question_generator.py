"""Tests de la generación de preguntas con IA (TODO con el LLM mockeado).

Ningún test hace red ni consume cuota de OpenRouter: se mockea
`app.services.ai_service._call_llm_for_questions` (que abstrae proveedor).
"""
import json
import os

os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["AI_PROVIDER"] = "openrouter"  # explícito: no heredar "gemini" de otros módulos
os.environ["AI_QUESTION_RATE_LIMIT"] = "5/hour"
os.environ["AI_QUESTION_MAX_ATTEMPTS"] = "2"

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Question, Subtopic
from app.models.question_meta import QuestionSource, QuestionStatus
from app.models.subtopic_chunk import SubtopicChunk
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.services.embeddings_service import embed_text
from app.services.question_parser import parse_generated_questions


def _question_json(prompt="¿Qué estructura protege la córnea?", correct_index=0):
    return {
        "prompt": prompt,
        "options": ["A op", "B op", "C op", "D op"],
        "correct_index": correct_index,
        "explanation": "Porque el contexto lo dice.",
    }


def _llm_payload(questions):
    return json.dumps({"questions": questions}, ensure_ascii=False)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def teacher(client):
    headers = auth_headers(client, "gen-profe@example.com", "Gen Profe", "TEACHER")
    resp = client.post(
        "/api/courses",
        json={"name": "Curso Gen IA", "description": "Curso para generar preguntas"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return headers


@pytest.fixture(scope="module")
def student(client):
    return auth_headers(client, "gen-est@example.com", "Gen Est", "STUDENT")


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="module")
def indexed_subtopic_id():
    """Subtema con contenido indexado (chunk) para generar preguntas."""
    content = "La córnea es la ventana transparente del ojo y se trasplanta con trépano."
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
        chunk_repo.create(
            s, subtopic_id=subtopic_id, content=content, embedding=embed_text(content)
        )
        return subtopic_id


@pytest.fixture()
def mock_llm():
    with patch(
        "app.services.ai_service._call_llm_for_questions", new_callable=AsyncMock
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def _reset_limiter():
    """Resetea contadores de rate limit entre tests del módulo.

    El límite de generación es 5/hora y los tests del módulo comparten el
    profesor: sin reset, los tests posteriores al 5to request recibirían 429.
    """
    from app.api.routes.ai import limiter

    try:
        limiter.reset()
    except Exception:
        inner = getattr(limiter, "_limiter", limiter)
        storage = getattr(inner, "_storage", None)
        if storage is not None:
            storage.reset()
    yield


# ── Flujo principal ────────────────────────────────────────────────────────


def test_generacion_exitosa_201(client, teacher, student, indexed_subtopic_id, mock_llm):
    mock_llm.side_effect = [
        _llm_payload([_question_json(f"¿Pregunta generada {i}?") for i in range(3)])
    ]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 3},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created"] == 3
    assert data["requested"] == 3
    assert all(q["source"] == "ai" for q in data["generated"])
    assert all(q["status"] == "pending" for q in data["generated"])
    assert all(q["is_owner"] for q in data["generated"])

    # Orden consecutivo
    orders = [q["order"] for q in data["generated"]]
    assert orders == sorted(orders)
    assert len(set(orders)) == 3

    # NO visibles para el estudiante
    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(
        f"/api/subtopics/{indexed_subtopic_id}?course_id={general['id']}", headers=student
    )
    prompts = [q["prompt"] for q in resp.json()["questions"]]
    assert not any(p.startswith("¿Pregunta generada") for p in prompts)


def test_generacion_con_fences_json(client, teacher, indexed_subtopic_id, mock_llm):
    payload = "```json\n" + _llm_payload([_question_json("¿Pregunta con fences?")]) + "\n```"
    mock_llm.side_effect = [payload]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["created"] == 1


def test_preguntas_invalidas_se_descartan_con_warning(client, teacher, indexed_subtopic_id, mock_llm):
    valid1 = _question_json("¿Pregunta válida uno de generación?")
    valid2 = _question_json("¿Pregunta válida dos de generación?")
    invalid = {
        "prompt": "¿Pregunta con cinco opciones?",
        "options": ["a", "b", "c", "d", "e"],
        "correct_index": 0,
        "explanation": "",
    }
    mock_llm.side_effect = [_llm_payload([valid1, invalid, valid2])]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 3},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created"] == 2
    assert data["requested"] == 3
    assert data["warning"] is not None


def test_reintento_segundo_intento_valido(client, teacher, indexed_subtopic_id, mock_llm):
    mock_llm.side_effect = [
        "texto sin json útil",
        _llm_payload([_question_json("¿Pregunta del segundo intento?")]),
    ]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    assert mock_llm.call_count == 2
    # Reintento = segundo attempt (temperatura más baja, ver unitario abajo)
    assert mock_llm.call_args_list[0].args[-1] == 1
    assert mock_llm.call_args_list[1].args[-1] == 2


def test_dos_intentos_rotos_502_y_no_guarda_nada(client, teacher, indexed_subtopic_id, mock_llm):
    with SessionLocal() as s:
        before = len(
            s.scalars(
                select(Question.id).where(
                    Question.subtopic_id == indexed_subtopic_id,
                    Question.source == QuestionSource.AI,
                )
            ).all()
        )
    mock_llm.side_effect = ["nada", "tampoco"]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 2},
        headers=teacher,
    )
    assert resp.status_code == 502, resp.text
    assert mock_llm.call_count == 2
    with SessionLocal() as s:
        after = len(
            s.scalars(
                select(Question.id).where(
                    Question.subtopic_id == indexed_subtopic_id,
                    Question.source == QuestionSource.AI,
                )
            ).all()
        )
        assert after == before, "Una respuesta inválida del LLM no debe guardar nada"


def test_cuota_agotada_sin_reintento(client, teacher, indexed_subtopic_id, mock_llm):
    from app.services.ai_service import GeminiCallError

    mock_llm.side_effect = GeminiCallError("cuota agotada")
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 502, resp.text
    assert mock_llm.call_count == 1  # sin reintento


def test_proveedor_saturado_429_sin_reintento(client, teacher, indexed_subtopic_id, mock_llm):
    from app.core.openrouter_client import OpenRouterSaturatedError

    mock_llm.side_effect = OpenRouterSaturatedError("saturado")
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 429, resp.text
    assert mock_llm.call_count == 1


def test_subtema_sin_chunks_422(client, teacher, mock_llm):
    with SessionLocal() as s:
        # Un subtema SIN chunk: los subtemas >= segundo no fueron indexados
        ids = s.scalars(select(Subtopic.id).order_by(Subtopic.id)).all()
        indexed = s.scalar(select(Subtopic.id).limit(1))
        target = next((i for i in ids if i != indexed), None)
        # limpia chunks por si acaso
        from sqlalchemy import delete

        from app.models.subtopic_chunk import SubtopicChunk

        s.execute(delete(SubtopicChunk).where(SubtopicChunk.subtopic_id == target))
        s.commit()
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": target, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 422, resp.text
    assert "indexado" in resp.json()["detail"].lower()


# ── Autorización y validación de payload ──────────────────────────────────


def test_generacion_estudiante_403(client, student, indexed_subtopic_id):
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=student,
    )
    assert resp.status_code == 403


def test_generacion_sin_token_401(client, indexed_subtopic_id):
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
    )
    assert resp.status_code == 401


def test_generacion_subtopic_inexistente_404(client, teacher):
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": 999999, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 404


def test_generacion_payload_con_los_dos_ids_422(client, teacher, indexed_subtopic_id):
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "topic_id": 1, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 422
    resp = client.post(
        "/api/ai/questions/generate",
        json={"count": 1},
        headers=teacher,
    )
    assert resp.status_code == 422


def test_generacion_count_fuera_de_rango_422(client, teacher, indexed_subtopic_id):
    for count in (0, 6):
        resp = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": indexed_subtopic_id, "count": count},
            headers=teacher,
        )
        assert resp.status_code == 422


# ── Rate limit de generación (independiente del de /ask) ──────────────────


def test_rate_limit_generacion_429(client, teacher, indexed_subtopic_id, mock_llm):
    mock_llm.side_effect = lambda *a, **k: _llm_payload([_question_json()])
    # El límite es 5/hour: la 6ta llamada del mismo profesor debe dar 429.
    # (El fixture de módulo ya pudo consumir 1-2; dispara hasta pasarse.)
    statuses = []
    for _ in range(8):
        resp = client.post(
            "/api/ai/questions/generate",
            json={"subtopic_id": indexed_subtopic_id, "count": 1},
            headers=teacher,
        )
        statuses.append(resp.status_code)
    assert 429 in statuses
    # El límite de /ask no se ve afectado: un estudiante aún puede preguntar.
    student = auth_headers(client, "gen-est2@example.com", "Gen Est 2", "STUDENT")
    with patch(
        "app.services.ai_service.call_openrouter", new_callable=AsyncMock
    ) as mock_or:
        mock_or.side_effect = ["normalizada", "respuesta"]
        with SessionLocal() as s:
            chunk_repo.create(
                s,
                subtopic_id=indexed_subtopic_id,
                content="chunk para ask",
                embedding=embed_text("chunk para ask"),
            )
        resp = client.post(
            "/api/ai/ask",
            json={"question": "glaucoma", "subtopic_id": indexed_subtopic_id},
            headers=student,
        )
        assert resp.status_code == 200, resp.text


# ── Duplicados con preguntas existentes ───────────────────────────────────


def test_generacion_descarta_enunciado_existente(client, teacher, indexed_subtopic_id, mock_llm):
    existing = "¿Pregunta ya existente en el banco?"
    client.post(
        f"/api/content/subtopics/{indexed_subtopic_id}/questions",
        json={
            "prompt": existing,
            "options": ["a", "b", "c", "d"],
            "correct_index": 0,
        },
        headers=teacher,
    )
    # El LLM "insiste" con el mismo enunciado + uno nuevo
    mock_llm.side_effect = [
        _llm_payload(
            [
                _question_json(existing),
                _question_json("¿Pregunta nueva distinta del banco?"),
            ]
        )
    ]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 2},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created"] == 1
    assert data["generated"][0]["prompt"] == "¿Pregunta nueva distinta del banco?"


# ── topic_id: distribución entre subtemas ─────────────────────────────────


def test_generacion_por_topic_distribuye(client, teacher, mock_llm):
    """Con un topic de 2 subtemas indexados, 4 preguntas → 2 llamadas al LLM."""
    with SessionLocal() as s:
        topic_id = s.get(Subtopic, s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id).topic_id
        subtopics = s.scalars(
            select(Subtopic).where(Subtopic.topic_id == topic_id).order_by(Subtopic.id)
        ).all()
        # indexa los 2 primeros subtemas
        for subtopic in subtopics[:2]:
            existing = s.scalar(
                select(SubtopicChunk).where(SubtopicChunk.subtopic_id == subtopic.id)
            )
            if existing is None:
                chunk_repo.create(
                    s,
                    subtopic_id=subtopic.id,
                    content=f"Contenido indexado de {subtopic.name}",
                    embedding=embed_text(f"Contenido indexado de {subtopic.name}"),
                )

    mock_llm.side_effect = lambda *a, **k: _llm_payload(
        [_question_json(f"¿Por topic {i}?") for i in range(2)]
    )
    resp = client.post(
        "/api/ai/questions/generate",
        json={"topic_id": topic_id, "count": 4},
        headers=teacher,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["created"] == 4
    # 2 subtemas × 1 llamada cada uno
    assert mock_llm.call_count == 2


# ── Parser puro: casos borde ──────────────────────────────────────────────


def test_parser_texto_alrededor_del_json():
    raw = 'Aquí tienes: {"questions": [' + json.dumps(_question_json()) + ']} Espero sirva.'
    parsed = parse_generated_questions(raw, 3)
    assert len(parsed) == 1


def test_parser_comillas_raras():
    q = _question_json('¿Qué es "el endotelio" corneal?')
    raw = json.dumps({"questions": [q]}, ensure_ascii=False)
    parsed = parse_generated_questions(raw, 3)
    assert len(parsed) == 1


def test_parser_opciones_repetidas_descarta():
    q = _question_json("¿Pregunta con opciones repetidas?")
    q["options"] = ["igual", "igual", "c", "d"]
    parsed = parse_generated_questions(json.dumps({"questions": [q]}), 3)
    assert parsed == []


def test_parser_correct_index_como_string():
    q = _question_json("¿Correct index string?")
    q["correct_index"] = "2"
    parsed = parse_generated_questions(json.dumps({"questions": [q]}), 3)
    assert len(parsed) == 1
    assert parsed[0].correct_index == 2


def test_parser_correct_index_invalido_descarta():
    q = _question_json("¿Correct index bool?")
    q["correct_index"] = True
    assert parse_generated_questions(json.dumps({"questions": [q]}), 3) == []
    q["correct_index"] = "alto"
    assert parse_generated_questions(json.dumps({"questions": [q]}), 3) == []


def test_parser_recorta_al_expected_max():
    questions = [_question_json(f"¿Pregunta extra {i}?") for i in range(5)]
    parsed = parse_generated_questions(json.dumps({"questions": questions}), 2)
    assert len(parsed) == 2


def test_parser_json_roto_devuelve_vacio():
    assert parse_generated_questions("esto no es json", 3) == []
    assert parse_generated_questions('{"questions": "no lista"}', 3) == []
    assert parse_generated_questions("", 3) == []


# ── Regresión: pending jamás visible ──────────────────────────────────────


def test_pending_jamas_visible_para_estudiante(client, teacher, student, indexed_subtopic_id, mock_llm):
    mock_llm.side_effect = [_llm_payload([_question_json("¿Regresión pending invisible?")])]
    resp = client.post(
        "/api/ai/questions/generate",
        json={"subtopic_id": indexed_subtopic_id, "count": 1},
        headers=teacher,
    )
    assert resp.status_code == 201
    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(
        f"/api/subtopics/{indexed_subtopic_id}?course_id={general['id']}", headers=student
    )
    assert "¿Regresión pending invisible?" not in [q["prompt"] for q in resp.json()["questions"]]
    # y el banco del profesor la muestra como pendiente
    resp = client.get(
        f"/api/content/subtopics/{indexed_subtopic_id}/questions/bank?status=pending",
        headers=teacher,
    )
    assert any(q["prompt"] == "¿Regresión pending invisible?" for q in resp.json())


def test_temperatura_por_intento_unitario():
    """Unitario: attempt 1 → 0.3, attempt >=2 → 0.1 (via proveedor mockeado)."""
    from unittest.mock import AsyncMock, patch

    from app.core.config import settings
    from app.services import ai_service

    async def fake_openrouter(**kwargs):
        return kwargs.get("temperature")

    with patch("app.services.ai_service.call_openrouter", new=fake_openrouter):
        import asyncio

        t1 = asyncio.run(
            ai_service._call_llm_for_questions("s", "u", 1)
        )
        t2 = asyncio.run(
            ai_service._call_llm_for_questions("s", "u", 2)
        )
    assert (t1, t2) == (0.3, 0.1)
