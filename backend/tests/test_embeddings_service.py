"""Tests del servicio de embeddings con modelo local (sentence-transformers).

Verifican que los vectores tengan la dimensión esperada, que el batching
devuelva un vector por texto y que la similitud coseno refleje la cercanía
semántica real entre textos.
"""
import math
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/oftallearn_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest

from app.services.embeddings_service import EMBEDDING_DIMENSIONS, embed_batch, embed_text


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def test_embed_text_devuelve_vector_de_384_floats():
    vector = embed_text("la córnea es la ventana transparente del ojo")
    assert isinstance(vector, list)
    assert len(vector) == EMBEDDING_DIMENSIONS
    assert all(isinstance(v, float) for v in vector)


def test_embed_batch_devuelve_un_vector_por_texto():
    textos = [
        "la presión intraocular normal suele estar entre 10 y 21 mmHg",
        "el cristalino enfoca la luz sobre la retina",
        "el glaucoma daña el nervio óptico de forma progresiva",
    ]
    vectors = embed_batch(textos)
    assert isinstance(vectors, list)
    assert len(vectors) == 3
    assert all(len(v) == EMBEDDING_DIMENSIONS for v in vectors)
    assert all(isinstance(v, float) for vector in vectors for v in vector)


def test_textos_semanticamente_similares_quedan_mas_cerca():
    dolor_ocular = embed_text("el ojo duele mucho")
    dolor_intenso = embed_text("dolor ocular intenso")
    clima = embed_text("el clima está lluvioso hoy")

    similitud_relacionada = cosine_similarity(dolor_ocular, dolor_intenso)
    similitud_no_relacionada = cosine_similarity(dolor_ocular, clima)

    assert similitud_relacionada > similitud_no_relacionada


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_embed_text_lanza_value_error_con_texto_vacio(texto):
    with pytest.raises(ValueError):
        embed_text(texto)


def test_embed_batch_rechaza_textos_invalidos():
    with pytest.raises(ValueError):
        embed_batch([])
    with pytest.raises(ValueError):
        embed_batch(["texto válido", ""])
    with pytest.raises(ValueError):
        embed_batch(["texto válido", None])