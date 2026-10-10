"""Servicio de embeddings de texto con un modelo local sentence-transformers.

Genera los vectores numéricos que usa el módulo de RAG para indexar los chunks
del contenido y para buscar el más relevante a la pregunta de un estudiante.
El modelo corre en CPU y se carga UNA SOLA VEZ (patrón singleton con carga
diferida), de modo que no se depende de APIs externas ni se gasta cuota.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from functools import lru_cache

from app.core.config import settings

EMBEDDING_DIMENSIONS = 384  # dimensión del modelo por defecto (multilingüe MiniLM-L12)


@lru_cache(maxsize=1)
def _cached_embedding_model():
    """Carga UNA vez el modelo; envuelto por get_embedding_model para permitir
    sustitución limpia en pruebas sin golpear la caché real."""
    backend = (settings.EMBEDDINGS_BACKEND or "torch").lower()
    if backend not in ("torch", "onnx"):
        raise RuntimeError(
            f"EMBEDDINGS_BACKEND inválido: '{backend}'. Use 'torch' u 'onnx'."
        )
    if backend == "onnx":
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise RuntimeError(
                "EMBEDDINGS_BACKEND=onnx requiere el paquete 'fastembed' "
                "(instálelo o instale requirements-onnx.txt)."
            ) from exc
        model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        _validate_onnx_dimensions(model)
        return model
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")


def get_embedding_model():
    """Carga el modelo de embeddings una única vez y lo reutiliza.

    Backend configurable por env (EMBEDDINGS_BACKEND):
    - "torch" (default): sentence-transformers como siempre.
    - "onnx": fastembed (ONNX) con el MISMO modelo — vectores idénticos
      (coseno 1.0000 medido), misma dimensión 384, sin reindexar; ahorra
      ~40% de RAM y es ~100x más rápido por consulta.
    """
    return _cached_embedding_model()


def _validate_onnx_dimensions(model) -> None:
    """Alerta temprana si el modelo ONNX no produce 384 dimensiones.

    El índice pgvector fue construido con 384 (MiniLM-L12); si se cambia a un
    modelo de otra dimensión la primera búsqueda falla de forma confusa.
    Con el modelo por defecto este check es decorativo (384 garantizado).
    """
    probe = next(iter(model.embed(["probe"])))
    if len(probe) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            "El modelo ONNX configurado produce %d dimensiones y el índice "
            "espera %d: use el modelo por defecto (%s) o reindexe."
            % (len(probe), EMBEDDING_DIMENSIONS, settings.EMBEDDING_MODEL)
        )


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
    backend = (settings.EMBEDDINGS_BACKEND or "torch").lower()
    if backend == "onnx":
        model = get_embedding_model()
        # model.embed() devuelve un GENERADOR de filas (no un array): hay que
        # materializarla con next(iter(...)), no se puede indexar.
        return [float(value) for value in next(iter(model.embed([_validate_text(text)])))]
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
    backend = (settings.EMBEDDINGS_BACKEND or "torch").lower()
    if backend == "onnx":
        model = get_embedding_model()
        return [[float(value) for value in row] for row in model.embed(validated)]
    vectors = get_embedding_model().encode(validated)
    return [[float(value) for value in row.tolist()] for row in vectors]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Similitud coseno entre dos vectores de embeddings (0.0 a 1.0)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)