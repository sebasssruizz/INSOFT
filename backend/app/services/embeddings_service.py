"""Servicio de embeddings de texto con un modelo local sentence-transformers.

Genera los vectores numéricos que usa el módulo de RAG para indexar los chunks
del contenido y para buscar el más relevante a la pregunta de un estudiante.
El modelo corre en CPU y se carga UNA SOLA VEZ (patrón singleton con carga
diferida), de modo que no se depende de APIs externas ni se gasta cuota.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings

EMBEDDING_DIMENSIONS = 384  # dimensión del modelo por defecto (multilingüe MiniLM-L12)


@lru_cache(maxsize=1)
def get_embedding_model():
    """Carga el modelo de embeddings una única vez y lo reutiliza.

    La primera llamada instancia el modelo (descargándolo de Hugging Face
    si no está cacheado localmente) en CPU; las siguientes llamadas devuelven
    la misma instancia en memoria, evitando recargas lentas y costosas.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")


def _validate_text(text: str | None) -> str:
    """Valida que el texto no sea None ni esté vacío (o solo espacios)."""
    if text is None or not text.strip():
        raise ValueError("El texto a embeber no puede ser None ni estar vacío.")
    return text


def embed_text(text: str | None) -> list[float]:
    """Genera el embedding (vector) de una sola cadena de texto.

    Pensado para embeber en tiempo real una pregunta del estudiante.

    Args:
        text: El texto a embeber. No puede ser None ni estar vacío.

    Returns:
        list[float]: Vector de `EMBEDDING_DIMENSIONS` dimensiones.

    Raises:
        ValueError: Si `text` es None o una cadena vacía (o solo espacios).
    """
    vector = get_embedding_model().encode(_validate_text(text))
    return [float(value) for value in vector.tolist()]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Genera embeddings de varios textos en una sola pasada (batching nativo).

    Mucho más eficiente que llamar `embed_text` en un bucle porque
    sentence-transformers procesa la lista completa en lotes sobre el modelo.

    Args:
        texts: Textos a embeber, uno por línea. Ninguno puede ser None ni vacío.

    Returns:
        list[list[float]]: Un vector por cada texto, en el mismo orden.

    Raises:
        ValueError: Si la lista está vacía o algún texto es None/vacío.
    """
    if not texts:
        raise ValueError("La lista de textos no puede estar vacía.")
    validated = [_validate_text(text) for text in texts]
    vectors = get_embedding_model().encode(validated)
    return [[float(value) for value in row.tolist()] for row in vectors]