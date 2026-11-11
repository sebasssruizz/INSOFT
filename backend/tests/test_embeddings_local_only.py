"""EMBEDDINGS_LOCAL_ONLY: con la opción activa, fastembed solo usa la caché local."""
import os

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DEV_AUTH_ENABLED", "true")

import pytest

from app.core.config import settings
from app.services import embeddings_service


@pytest.fixture()
def capturar(monkeypatch):
    llamadas = []

    class FakeTextEmbedding:
        def __init__(self, **kwargs):
            llamadas.append(kwargs)

    fake_module = type("fastembed", (), {"TextEmbedding": FakeTextEmbedding})
    monkeypatch.setitem(__import__("sys").modules, "fastembed", fake_module)
    monkeypatch.setattr(embeddings_service, "_validate_onnx_dimensions", lambda model: None)
    monkeypatch.setattr(settings, "EMBEDDINGS_BACKEND", "onnx")
    embeddings_service._cached_embedding_model.cache_clear()
    yield llamadas
    embeddings_service._cached_embedding_model.cache_clear()


def test_por_defecto_no_fuerza_solo_local(capturar, monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDINGS_LOCAL_ONLY", False)
    embeddings_service._cached_embedding_model()
    assert capturar == [{"model_name": settings.EMBEDDING_MODEL}]


def test_local_only_pasa_local_files_only(capturar, monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDINGS_LOCAL_ONLY", True)
    embeddings_service._cached_embedding_model()
    assert capturar == [{"model_name": settings.EMBEDDING_MODEL, "local_files_only": True}]
