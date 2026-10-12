"""Interruptores operativos: IA apagada, tope global diario y modo mantenimiento.

El proveedor de IA siempre está mockeado: ninguna prueba llama a la red.
"""
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")
os.environ.setdefault("TEACHER_EMAILS", "")
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-v1-test")
os.environ.setdefault("AI_ASK_RATE_LIMIT", "1000/hour")

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import ai_service
from app.services.ai_budget import AiDisabledError, reservar_llamada

FRAGMENTO = SimpleNamespace(content="El glaucoma de ángulo cerrado requiere valoración urgente.")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _contador_del_dia_limpio(client):
    """El contador diario vive en la base: cada prueba parte de cero."""
    from sqlalchemy import text

    from app.database.session import SessionLocal

    with SessionLocal() as s:
        s.execute(text("DELETE FROM ai_calls_daily"))
        s.commit()
    yield


def _login(client, email, role):
    resp = client.post("/api/auth/dev", json={"email": email, "name": "Interruptor", "role": role})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def estudiante(client):
    return _login(client, "interruptor-est@example.com", "STUDENT")


@pytest.fixture()
def docente(client):
    return _login(client, "interruptor-doc@example.com", "TEACHER")


def _sin_chunks(monkeypatch):
    monkeypatch.setattr(ai_service, "_retrieve_chunks", AsyncMock(return_value=[]))


def _con_chunks(monkeypatch):
    monkeypatch.setattr(ai_service, "_retrieve_chunks", AsyncMock(return_value=[FRAGMENTO]))


# ── IA apagada ────────────────────────────────────────────────────────────────


def test_ia_apagada_sin_contexto_responde_503_y_no_llama_al_proveedor(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    _sin_chunks(monkeypatch)
    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
        resp = client.post("/api/ai/ask", json={"question": "¿qué es el glaucoma?"}, headers=estudiante)
    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"].startswith("[asistente-desactivado]")
    llm.assert_not_called()


def test_ia_apagada_con_fragmentos_usa_el_modo_respaldo_sin_llamadas(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    _con_chunks(monkeypatch)
    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
        resp = client.post("/api/ai/ask", json={"question": "¿qué es el glaucoma?"}, headers=estudiante)
    assert resp.status_code == 200, resp.text
    assert resp.json()["degraded"] is True
    llm.assert_not_called()


def test_generacion_con_ia_apagada_lanza_el_error_tipado(monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
        with pytest.raises(AiDisabledError):
            ai_service._call_llm_for_questions("sistema", "usuario", 1)
    llm.assert_not_called()


# ── Tope global diario ───────────────────────────────────────────────────────


def test_tope_global_corta_las_llamadas_y_luego_responde_429(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_GLOBAL_DAILY_CALLS", 2)
    _sin_chunks(monkeypatch)
    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
        llm.side_effect = lambda *a, **k: "respuesta de prueba"
        primera = client.post("/api/ai/ask", json={"question": "primera consulta"}, headers=estudiante)
        assert primera.status_code == 200, primera.text
        assert llm.call_count == 2  # normalización + respuesta: agota el tope de 2

        segunda = client.post("/api/ai/ask", json={"question": "segunda consulta"}, headers=estudiante)
    assert segunda.status_code == 429, segunda.text
    assert segunda.json()["detail"].startswith("[asistente-tope-global]")
    assert int(segunda.headers["Retry-After"]) >= 60
    assert llm.call_count == 2, "con el tope agotado no debe haber más llamadas al proveedor"


def test_tope_agotado_con_fragmentos_degrada_sin_gastar(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "AI_GLOBAL_DAILY_CALLS", 1)
    _con_chunks(monkeypatch)
    with patch("app.services.ai_service.call_openrouter", new_callable=AsyncMock) as llm:
        llm.side_effect = lambda *a, **k: "respuesta de prueba"
        client.post("/api/ai/ask", json={"question": "agota el tope"}, headers=estudiante)
        llamadas_antes = llm.call_count
        resp = client.post("/api/ai/ask", json={"question": "con el tope agotado"}, headers=estudiante)
    assert resp.status_code == 200, resp.text
    assert resp.json()["degraded"] is True
    assert llm.call_count == llamadas_antes


def test_sin_tope_configurado_no_toca_el_contador(monkeypatch):
    monkeypatch.setattr(settings, "AI_GLOBAL_DAILY_CALLS", 0)
    assert reservar_llamada(session_factory=_session_que_no_debe_abrirse) is True


def _session_que_no_debe_abrirse():
    raise AssertionError("con tope 0 no debe abrirse la base")


def test_reserva_se_detiene_exactamente_en_el_limite(monkeypatch):
    from app.database.session import SessionLocal

    monkeypatch.setattr(settings, "AI_GLOBAL_DAILY_CALLS", 3)
    resultados = [reservar_llamada(session_factory=SessionLocal) for _ in range(5)]
    assert resultados == [True, True, True, False, False]


# ── Modo mantenimiento ───────────────────────────────────────────────────────


def test_mantenimiento_bloquea_a_estudiantes_con_503(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    resp = client.get("/api/courses", headers=estudiante)
    assert resp.status_code == 503
    assert resp.json()["detail"].startswith("[mantenimiento]")
    assert resp.headers["Retry-After"] == "600"


def test_mantenimiento_deja_pasar_a_docentes(client, docente, monkeypatch):
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    assert client.get("/api/courses", headers=docente).status_code == 200


def test_mantenimiento_no_bloquea_salud_ni_acceso(client, monkeypatch):
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    assert client.get("/health").status_code == 200
    assert client.get("/api/auth/dev", params={}).status_code != 503


def test_mantenimiento_con_token_invalido_no_cuenta_como_docente(client, monkeypatch):
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", True)
    resp = client.get("/api/courses", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert resp.status_code == 503


def test_sin_mantenimiento_todo_funciona(client, estudiante, monkeypatch):
    monkeypatch.setattr(settings, "MAINTENANCE_MODE", False)
    assert client.get("/api/courses", headers=estudiante).status_code == 200
