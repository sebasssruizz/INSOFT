"""Tests del endpoint de IA (/api/ai/ask).

Usan SQLite en memoria y el login de desarrollo. Mockean las llamadas a OpenRouter
para no depender de red externa. Cubren: autorización, éxito, rate limit por
usuario, errores de OpenRouter, validación de max_length.
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

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Subtopic
from app.repositories import subtopic_chunk_repository as chunk_repo
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


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_success(mock_call, client: TestClient, indexed_subtopic_id):
    """Éxito: pregunta normalizada, chunks recuperados, respuesta guardada."""
    # Mockea normalización + respuesta final (2 llamadas)
    mock_call.side_effect = [
        "¿Qué es el glaucoma de ángulo cerrado y por qué sube la presión?",  # normalizada
        "El glaucoma de ángulo cerrado es una urgencia...",  # respuesta
    ]

    student = auth_headers(client, "ai-est1@example.com", "AI Est 1", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "profe, ¿qué es el glaucoma ese que sube la presión?", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "respuesta" in data
    assert data["subtopic_id"] == indexed_subtopic_id
    assert data["chunks_usados"] >= 1


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_sin_subtopic_id(mock_call, client: TestClient, indexed_subtopic_id):
    """Éxito sin subtopic_id: busca en todo el contenido."""
    mock_call.side_effect = [
        "¿Qué es el glaucoma agudo?",
        "Es una urgencia oftalmológica...",
    ]

    student = auth_headers(client, "ai-est2@example.com", "AI Est 2", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma agudo?"},
        headers=student,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["subtopic_id"] is None
    assert data["chunks_usados"] >= 1


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_subtopic_sin_acceso_403(mock_call, client: TestClient, indexed_subtopic_id):
    """Profesor sin cursos -> 403 al pasar subtopic_id."""
    mock_call.side_effect = [
        "normalizada",
        "respuesta",
    ]

    teacher = auth_headers(client, "ai-profe@example.com", "AI Profe", "TEACHER")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma", "subtopic_id": indexed_subtopic_id},
        headers=teacher,
    )
    assert resp.status_code == 403, resp.text


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_subtopic_inexistente_404(mock_call, client: TestClient):
    """Subtopic inexistente -> 404."""
    mock_call.side_effect = ["normalizada", "respuesta"]

    student = auth_headers(client, "ai-est3@example.com", "AI Est 3", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma", "subtopic_id": 999999},
        headers=student,
    )
    assert resp.status_code == 404, resp.text


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_sin_token_401(mock_call, client: TestClient):
    """Sin token -> 401."""
    resp = client.post("/api/ai/ask", json={"question": "glaucoma"})
    assert resp.status_code == 401


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_openrouter_saturated_429(mock_call, client: TestClient, indexed_subtopic_id):
    """OpenRouterSaturatedError -> 429."""
    from app.core.openrouter_client import OpenRouterSaturatedError
    mock_call.side_effect = OpenRouterSaturatedError("Límite global alcanzado")

    student = auth_headers(client, "ai-est4@example.com", "AI Est 4", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 429, resp.text


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_openrouter_call_error_503(mock_call, client: TestClient, indexed_subtopic_id):
    """OpenRouterCallError -> 503."""
    from app.core.openrouter_client import OpenRouterCallError
    mock_call.side_effect = OpenRouterCallError("Timeout llamando a OpenRouter")

    student = auth_headers(client, "ai-est5@example.com", "AI Est 5", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "glaucoma", "subtopic_id": indexed_subtopic_id},
        headers=student,
    )
    assert resp.status_code == 503, resp.text


def test_ask_ai_question_max_length_422(client: TestClient):
    """Pregunta > 500 chars -> 422."""
    student = auth_headers(client, "ai-est6@example.com", "AI Est 6", "STUDENT")
    resp = client.post(
        "/api/ai/ask",
        json={"question": "a" * 501},
        headers=student,
    )
    assert resp.status_code == 422, resp.text


@patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock)
def test_ask_ai_rate_limit_user_429(mock_call, client: TestClient, indexed_subtopic_id):
    """Rate limit por usuario (slowapi) -> 429 al superar AI_ASK_RATE_LIMIT."""
    # 11 peticiones x 2 llamadas (normalize + answer) = 22 side effects
    mock_call.side_effect = ["normalizada", "respuesta"] * 12

    student = auth_headers(client, "ai-ratelimit@example.com", "AI Rate", "STUDENT")
    # AI_ASK_RATE_LIMIT = 10/hour en test env; haremos 11 peticiones
    for i in range(11):
        resp = client.post(
            "/api/ai/ask",
            json={"question": f"glaucoma pregunta {i}", "subtopic_id": indexed_subtopic_id},
            headers=student,
        )
        if i < 10:
            assert resp.status_code == 200, f"fallo en petición {i}: {resp.text}"
        else:
            assert resp.status_code == 429, f"petición {i} debería ser 429: {resp.text}"