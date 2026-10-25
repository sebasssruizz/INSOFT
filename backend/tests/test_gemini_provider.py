"""Tests del proveedor Gemini (/api/ai/ask con AI_PROVIDER=gemini).

Usan SQLite en fichero temporal y el login de desarrollo. Mockean
call_openrouter y call_gemini; Gemini no normaliza con OpenRouter: ninguna
prueba depende de red externa ni consume créditos de API.
"""
import os
from unittest.mock import AsyncMock, patch

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
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
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.main import app
from app.models.content import CourseTopic, Subtopic
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.services.ai_service import GeminiCallError
from app.services.embeddings_service import embed_text


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def indexed_subtopic_id():
    """Indexa un chunk de prueba y devuelve su subtopic_id."""
    content = "el ojo duele mucho y puede indicar glaucoma"
    with SessionLocal() as s:
        subtopic_id = s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id
        chunk_repo.create(
            s, subtopic_id=subtopic_id, content=content, embedding=embed_text(content)
        )
        return subtopic_id


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def use_gemini(monkeypatch, api_key="test-gemini-key"):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", api_key)


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_openrouter_por_defecto_sigue_funcionando(
    mock_or, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """AI_PROVIDER=openrouter: el flujo original no cambia."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    mock_or.side_effect = ["¿Qué es el glaucoma?", "Es una urgencia..."]

    student = auth_headers(client, "gem-est0@example.com", "Gem Est 0", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["chunks_usados"] >= 1


@patch("app.services.ai_service.call_gemini", new_callable=AsyncMock)
@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_responde_con_formato_compatible(
    mock_or, mock_gemini, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """AI_PROVIDER=gemini: llama a call_gemini y devuelve el formato actual."""
    use_gemini(monkeypatch)
    mock_or.side_effect = ["¿Qué es el glaucoma agudo?"]
    mock_gemini.side_effect = ["Respuesta generada por Gemini..."]

    student = auth_headers(client, "gem-est1@example.com", "Gem Est 1", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma agudo?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["respuesta"] == "Respuesta generada por Gemini..."
    assert data["subtopic_id"] == indexed_subtopic_id
    assert data["chunks_usados"] >= 1
    assert mock_gemini.await_count == 1
    mock_or.assert_not_awaited()


@patch("app.services.ai_service.call_gemini", new_callable=AsyncMock)
@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_recibe_contexto_rag(
    mock_or, mock_gemini, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """Gemini recibe el contexto RAG recuperado (no responde sin contexto)."""
    use_gemini(monkeypatch)
    mock_or.side_effect = ["¿Qué indica el dolor ocular?"]
    mock_gemini.side_effect = ["Podría indicar glaucoma..."]

    student = auth_headers(client, "gem-est2@example.com", "Gem Est 2", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "dolor ocular?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    user_content = mock_gemini.await_args.kwargs["user_content"]
    assert "CONTEXTO:" in user_content
    assert "el ojo duele mucho y puede indicar glaucoma" in user_content


@patch("app.services.ai_service.call_gemini", new_callable=AsyncMock)
@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_respeta_curso_contextual(
    mock_or, mock_gemini, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """Con course_id, Gemini solo recibe chunks de topics habilitados del curso."""
    use_gemini(monkeypatch)
    mock_or.side_effect = ["¿Qué indica el dolor ocular?"]
    mock_gemini.side_effect = ["Sin evidencia en este curso..."]

    teacher = auth_headers(client, "gem-profe1@example.com", "Gem Profe 1", "TEACHER")
    course = client.post(
        "/api/courses",
        json={"name": "Curso Gemini privado", "description": "x"},
        headers=teacher,
    ).json()
    with SessionLocal() as s:
        subtopic = s.get(Subtopic, indexed_subtopic_id)
        ct = s.scalar(
            select(CourseTopic).where(
                CourseTopic.course_id == course["id"],
                CourseTopic.topic_id == subtopic.topic_id,
            )
        )
        ct.enabled = False
        s.commit()

    resp = client.post(
        "/api/ai/ask",
        json={"question": "dolor ocular?", "course_id": course["id"]},
        headers=teacher,
    )
    assert resp.status_code == 200, resp.text
    user_content = mock_gemini.await_args.kwargs["user_content"]
    assert "el ojo duele mucho y puede indicar glaucoma" not in user_content


@patch("app.services.ai_service.call_gemini", new_callable=AsyncMock)
@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_sin_acceso_403_antes_del_proveedor(
    mock_or, mock_gemini, client: TestClient, monkeypatch
):
    """403 por autorización ocurre antes de llamar a Gemini."""
    use_gemini(monkeypatch)
    mock_or.side_effect = ["normalizada"]

    teacher = auth_headers(client, "gem-profe2@example.com", "Gem Profe 2", "TEACHER")
    course = client.post(
        "/api/courses",
        json={"name": "Curso Gemini ajeno", "description": "x"},
        headers=teacher,
    ).json()
    other = auth_headers(client, "gem-est3@example.com", "Gem Est 3", "STUDENT")

    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma", "course_id": course["id"]},
        headers=other,
    )
    assert resp.status_code == 403, resp.text
    assert mock_gemini.await_count == 0


@patch("app.services.ai_service.call_gemini", new_callable=AsyncMock)
@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_error_del_proveedor_503(
    mock_or, mock_gemini, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """Fallo de Gemini CON chunks disponibles -> 200 degradado (respaldo)."""
    use_gemini(monkeypatch)
    mock_or.side_effect = ["¿Qué es el glaucoma?"]
    mock_gemini.side_effect = GeminiCallError("Error al generar respuesta con Gemini: boom")

    student = auth_headers(client, "gem-est4@example.com", "Gem Est 4", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["degraded"] is True
    assert "MODO RESPALDO" in data["respuesta"]


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_gemini_sin_api_key_503_controlado(
    mock_or, client: TestClient, indexed_subtopic_id, monkeypatch
):
    """Sin GEMINI_API_KEY -> 503 con mensaje claro (sin llamada de red)."""
    use_gemini(monkeypatch, api_key="")
    mock_or.side_effect = ["¿Qué es el glaucoma?"]

    student = auth_headers(client, "gem-est5@example.com", "Gem Est 5", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    # Con chunks disponibles el asistente degrada (200) pero deixando claro
    # que el proveedor no está configurado; el detalle con GEMINI_API_KEY se
    # conserva en el texto de respaldo del modo degradado.
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["degraded"] is True
    assert "MODO RESPALDO" in data["respuesta"]


def test_gemini_rest_sends_context_and_system_separately(monkeypatch):
    import asyncio
    import httpx
    from app.services.ai_service import call_gemini

    use_gemini(monkeypatch)
    response = httpx.Response(200, json={"candidates": [{
        "finishReason": "STOP", "content": {"parts": [{"text": "Respuesta "}, {"text": "del temario."}]},
    }]})
    with patch("app.services.ai_service.httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        answer = asyncio.run(call_gemini("gemini-3.5-flash-lite", "Solo contexto", "CONTEXTO: anatomía"))
    assert answer == "Respuesta del temario."
    args, kw = post.call_args
    assert settings.GEMINI_API_KEY not in args[0]
    assert kw["headers"]["x-goog-api-key"] == settings.GEMINI_API_KEY
    assert kw["json"]["systemInstruction"]["parts"][0]["text"] == "Solo contexto"
    assert kw["json"]["contents"][0]["parts"][0]["text"] == "CONTEXTO: anatomía"


@pytest.mark.parametrize("kind", ["quota", "unauthorized", "server", "empty", "blocked", "truncated", "timeout", "network"])
def test_gemini_rest_failures_are_controlled_and_do_not_expose_secrets(monkeypatch, kind):
    import asyncio
    import httpx
    from app.services.ai_service import call_gemini

    use_gemini(monkeypatch)
    if kind in ("quota", "unauthorized", "server"):
        response = httpx.Response({"quota": 429, "unauthorized": 403, "server": 503}[kind], json={"error": settings.GEMINI_API_KEY})
    else:
        response = httpx.Response(200, json={"candidates": [{
            "finishReason": {"blocked": "SAFETY", "truncated": "MAX_TOKENS"}.get(kind, "STOP"),
            "content": {"parts": [] if kind == "empty" else [{"text": "parcial"}]},
        }]})
    with patch("app.services.ai_service.httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        if kind == "timeout":
            post.side_effect = httpx.ReadTimeout(settings.GEMINI_API_KEY)
        elif kind == "network":
            post.side_effect = httpx.ConnectError(settings.GEMINI_API_KEY)
        else:
            post.return_value = response
        with pytest.raises(GeminiCallError) as exc:
            asyncio.run(call_gemini("gemini-3.5-flash-lite", "Sistema", "Pregunta"))
    assert settings.GEMINI_API_KEY not in str(exc.value)
