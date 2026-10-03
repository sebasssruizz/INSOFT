"""Guardas de producción y SEED_MODE.

- Con ENV=production la app debe negarse a arrancar con configuración insegura
  (dev-auth activo, secreto JWT débil, OAuth ausente, CORS abierto o vacío).
- Con ENV=production y configuración válida: /docs cerrado salvo EXPOSE_DOCS.
- SEED_MODE=if_empty: un reinicio no modifica contenido existente (incluidas
  las unidades importadas fuera del seed, p. ej. 6–9) y con BD vacía carga todo.
"""
import hashlib
import os

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["ENV"] = "development"
os.environ["SEED_MODE"] = "auto"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.main import create_app
from app.models.content import Topic, Subtopic
from app.models.question_meta import QuestionSource, QuestionStatus
from app.seed.seed_content import run_seed_by_mode


def set_settings(**kwargs):
    """Copia campos sobre la Settings singleton (patrón de conftest)."""
    saved = {k: settings.__dict__[k] for k in kwargs}
    settings.__dict__.update(kwargs)
    return saved


def restore_settings(saved: dict):
    settings.__dict__.update(saved)


@pytest.fixture(scope="module")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def _production_fields(**overrides):
    base = {
        "ENV": "production",
        "DEV_AUTH_ENABLED": False,
        "SECRET_KEY": "a" * 64,
        "GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com",
        "BACKEND_CORS_ORIGINS": "https://insoft.example.com",
        "SEED_MODE": "if_empty",
    }
    base.update(overrides)
    return base


def test_produccion_rechaza_configuracion_insegura():
    saved = set_settings(**_production_fields(DEV_AUTH_ENABLED=True))
    try:
        with pytest.raises(RuntimeError) as exc:
            create_app()
        assert "DEV_AUTH_ENABLED" in str(exc.value)
    finally:
        restore_settings(saved)


def test_produccion_rechaza_secreto_debil():
    saved = set_settings(**_production_fields(SECRET_KEY="change-me-in-production"))
    try:
        with pytest.raises(RuntimeError) as exc:
            create_app()
        assert "SECRET_KEY" in str(exc.value)
    finally:
        restore_settings(saved)

    saved = set_settings(**_production_fields(SECRET_KEY="corto"))
    try:
        with pytest.raises(RuntimeError):
            create_app()
    finally:
        restore_settings(saved)


def test_produccion_rechaza_oauth_ausente():
    saved = set_settings(**_production_fields(GOOGLE_CLIENT_ID=""))
    try:
        with pytest.raises(RuntimeError) as exc:
            create_app()
        assert "GOOGLE_CLIENT_ID" in str(exc.value)
    finally:
        restore_settings(saved)


@pytest.mark.parametrize("cors", ["", "*"])
def test_produccion_rechaza_cors_abierto_o_vacio(cors):
    saved = set_settings(**_production_fields(BACKEND_CORS_ORIGINS=cors))
    try:
        with pytest.raises(RuntimeError) as exc:
            create_app()
        assert "CORS" in str(exc.value)
    finally:
        restore_settings(saved)


def test_produccion_valida_arranca_y_cierra_docs():
    saved = set_settings(**_production_fields())
    try:
        app = create_app()
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/docs").status_code == 404
            assert client.get("/redoc").status_code == 404
            assert client.get("/api/openapi.json").status_code == 404
    finally:
        restore_settings(saved)


def test_produccion_expose_docs_true():
    saved = set_settings(**_production_fields(EXPOSE_DOCS=True))
    try:
        app = create_app()
        with TestClient(app) as client:
            assert client.get("/docs").status_code == 200
    finally:
        restore_settings(saved)


def _content_state() -> list[tuple[str, int, str]]:
    db = SessionLocal()
    try:
        state = []
        for t in db.scalars(select(Topic).order_by(Topic.order)).all():
            for s in sorted(t.subtopics, key=lambda x: x.order):
                n_q = sum(
                    1 for q in s.questions
                    if q.source == QuestionSource.OFFICIAL and q.status == QuestionStatus.APPROVED
                )
                state.append((s.name, n_q, hashlib.md5((s.content or "").encode()).hexdigest()))
        return state
    finally:
        db.close()


def test_seed_if_empty_no_modifica_contenido_existente(client: TestClient):
    # El lifespan del TestClient ya corrió el seed con el entorno del módulo.
    before = _content_state()
    assert len(before) >= 22  # 19 de U1–5 + 3 de U6–8

    # "Reinicio": otro run del seed con if_empty NO cambia nada.
    db = SessionLocal()
    try:
        summary = run_seed_by_mode(db, "if_empty")
    finally:
        db.close()
    assert summary["cargado"] is False
    assert _content_state() == before

    # Con "never" tampoco.
    db = SessionLocal()
    try:
        assert run_seed_by_mode(db, "never")["seed"] == "never"
    finally:
        db.close()
    assert _content_state() == before


def test_seed_if_empty_carga_en_bd_vacia():
    """Con una BD sin unidades, if_empty carga el seed completo."""
    import app.seed.seed_content as sc

    class FakeDB:
        def scalar(self, *a, **k):
            return 0  # conteo de topics: 0 (BD vacía)

    called = {"n": 0}
    original = sc.seed_official_content
    sc.seed_official_content = lambda db: called.__setitem__("n", called["n"] + 1)
    try:
        summary = sc.run_seed_by_mode(FakeDB(), "if_empty")
        assert summary["cargado"] is True
        assert called["n"] == 1
    finally:
        sc.seed_official_content = original


def test_seed_resuelve_auto_por_entorno():
    saved = set_settings(SEED_MODE="auto", ENV="development")
    try:
        assert settings.seed_mode_effective == "always"
    finally:
        restore_settings(saved)
    saved = set_settings(SEED_MODE="auto", ENV="production")
    try:
        assert settings.seed_mode_effective == "if_empty"
    finally:
        restore_settings(saved)
    saved = set_settings(SEED_MODE="nunca-pasado-mal", ENV="development")
    try:
        assert settings.seed_mode_effective == "always"
    finally:
        restore_settings(saved)
