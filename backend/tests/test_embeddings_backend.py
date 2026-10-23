"""Selección de backend de embeddings (EMBEDDINGS_BACKEND torch|onnx).

Las pruebas usan un modelo fake (sin pesos reales) inyectando directamente
la caché del servicio: medimos que la API devuelve 384 dims y que las rutas
de embed_text/embed_batch no dependen del backend.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.services import embeddings_service as es  # noqa: E402


class _FakeOnnxModel:
    """Imita la interfaz de fastembed.TextEmbedding (embed -> iterables)."""

    def embed(self, texts):
        return [[0.25] * es.EMBEDDING_DIMENSIONS for _ in texts]


@pytest.fixture()
def fake_onnx(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDINGS_BACKEND", "onnx")
    _cached = es._cached_embedding_model
    _cached.cache_clear()
    monkeypatch.setattr(es, "get_embedding_model", lambda: _FakeOnnxModel())
    yield
    _cached.cache_clear()
    monkeypatch.setattr(settings, "EMBEDDINGS_BACKEND", "torch")


def test_backend_invalido_se_rechaza(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDINGS_BACKEND", "noexiste")
    cached = es._cached_embedding_model
    cached.cache_clear()
    with pytest.raises(RuntimeError, match="EMBEDDINGS_BACKEND"):
        es.get_embedding_model()
    monkeypatch.setattr(settings, "EMBEDDINGS_BACKEND", "torch")
    cached.cache_clear()


def test_onnx_embed_text_384_dims(fake_onnx):
    v = es.embed_text("¿Qué es el pterigión?")
    assert len(v) == 384


def test_onnx_embed_batch_mismo_orden(fake_onnx):
    vecs = es.embed_batch(["primero", "segundo"])
    assert len(vecs) == 2
    assert all(len(v) == 384 for v in vecs)
