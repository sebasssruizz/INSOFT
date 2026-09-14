"""Benchmark de respuesta con contexto (Prueba B) usando recuperación real por similitud.

Toma las 3 preguntas de la Prueba A, las normaliza con liquid/lfm-2.5-2.6b:free,
y para cada pregunta normalizada recupera los top-3 chunks por cosine similarity
contra subtopic_chunks (mismo flujo que /rag/search). Luego pide respuesta a
minimax/minimax-m3:free y liquid/lfm-2.5-2.6b:free.

Imprime: qué chunks recuperó (subtopic, similitud), y respuesta completa.
Controla verbosidad de minimax y alucinación parcial.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests
from pydantic_settings import BaseSettings, SettingsConfigDict

# Añade backend/ al path para importar embeddings_service
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.embeddings_service import embed_text  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT = (10, 180)

NORMALIZE_MODEL = "liquid/lfm-2.5-2.6b:free"
ANSWER_MODELS = [
    "liquid/lfm-2.5-2.6b:free",
    "minimax/minimax-m3:free",
]

DIRTY_QUESTIONS = [
    "profe disculpe la molestia, es que no entendí bien lo del glaucoma ese "
    "que sube la presión de un momento a otro, ¿cómo era que se llamaba y por "
    "qué pasa?",
    "oiga una pregunta rapidita, en la clase pasada hablaron de una prueba "
    "para medir algo del ojo con una lucecita, no recuerdo el nombre, ¿cuál "
    "es y para qué sirve exactamente?",
    "no logro diferenciar cuando es conjuntivitis viral o bacteriana, hay "
    "alguna forma de saber viendo los síntomas nada más?",
]

NORMALIZE_SYSTEM = (
    "Eres un asistente que reformula preguntas de estudiantes de oftalmología. "
    "Recibes preguntas coloquiales o desordenadas y debes devolverlas como "
    "preguntas claras de 1-2 frases cada una, SIN resolverlas. Devuelve solo "
    "las preguntas reformuladas, numeradas, sin texto adicional."
)

ANSWER_SYSTEM = (
    "Eres el asistente de estudio de Oftalmología de INSOFT. Responde la "
    "pregunta del estudiante usando SOLO el siguiente contenido. Si el contenido "
    "no cubre la pregunta, dilo explícitamente en vez de inventar. Sé conciso."
)

TOP_K = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )
    OPENROUTER_API_KEY: str = ""
    DATABASE_URL: str = "postgresql+psycopg2://oftallearn:oftallearn@localhost:5433/oftallearn"


settings = Settings()


def chat_completion(model: str, system: str, user: str, max_tokens: int = 1200) -> tuple[float, str]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    start = time.perf_counter()
    try:
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        elapsed = time.perf_counter() - start
        if resp.status_code == 429:
            return elapsed, "[rate-limit 429] Cuota de este modelo agotada."
        resp.raise_for_status()
        data = resp.json()
        return elapsed, data["choices"][0]["message"]["content"]
    except requests.Timeout:
        return time.perf_counter() - start, "[timeout] No respondió dentro del límite."
    except requests.RequestException as exc:
        return time.perf_counter() - start, f"[error de red] {exc.__class__.__name__}: {exc}"


def normalize_questions() -> list[str]:
    """PRUEBA A: normaliza las 3 preguntas sucias con el modelo ligero."""
    user = "\n".join(f"{i+1}. {q}" for i, q in enumerate(DIRTY_QUESTIONS))
    elapsed, out = chat_completion(NORMALIZE_MODEL, NORMALIZE_SYSTEM, user)
    print(f"[normalize] modelo={NORMALIZE_MODEL} time={elapsed:.2f}s")
    print(out)
    print()
    lines = [l.strip() for l in out.split("\n") if l.strip()]
    return [l.split(". ", 1)[1] if ". " in l else l for l in lines]


def fetch_all_chunks(database_url: str) -> list[dict]:
    """Trae todos los chunks con su embedding (JSON string -> list[float])."""
    import psycopg2

    dsn = (
        database_url.replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgres://", "postgresql://")
    )
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, subtopic_id, content, embedding FROM subtopic_chunks"
            )
            rows = cur.fetchall()
    chunks = []
    for row in rows:
        chunks.append({
            "id": row[0],
            "subtopic_id": row[1],
            "content": row[2],
            "embedding": json.loads(row[3]) if isinstance(row[3], str) else row[3],
        })
    return chunks


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve_top_chunks(query_vec: list[float], all_chunks: list[dict], k: int = TOP_K) -> list[dict]:
    scored = sorted(
        ((cosine_similarity(chunk["embedding"], query_vec), chunk) for chunk in all_chunks),
        key=lambda item: item[0],
        reverse=True,
    )[:k]
    return [{"similarity": score, **chunk} for score, chunk in scored]


def get_subtopic_names(database_url: str, subtopic_ids: set[int]) -> dict[int, str]:
    import psycopg2

    dsn = (
        database_url.replace("postgresql+psycopg2://", "postgresql://")
        .replace("postgres://", "postgresql://")
    )
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            ids_str = ",".join(str(i) for i in subtopic_ids)
            cur.execute(
                f"SELECT id, name FROM subtopics WHERE id IN ({ids_str})"
            )
            rows = cur.fetchall()
    return {r[0]: r[1] for r in rows}


def run_answer(model: str, chunks: list[dict], question: str) -> tuple[float, str]:
    context = "\n\n".join(
        f"[Chunk {i+1} | subtopic_id={c['subtopic_id']} | sim={c['similarity']:.3f}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    user = f"{context}\n\nPregunta: {question}"
    return chat_completion(model, ANSWER_SYSTEM, user, max_tokens=1200)


def print_section(title: str, model: str, elapsed: float, content: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"{title} | modelo: {model} | {elapsed:.2f} s")
    print(f"{'═' * 70}")
    print(content)
    print()


def main() -> None:
    if not settings.OPENROUTER_API_KEY:
        print("ERROR: falta OPENROUTER_API_KEY en .env", file=sys.stderr)
        sys.exit(1)

    print(f"Modelo normalización: {NORMALIZE_MODEL}")
    print(f"Modelos respuesta: {', '.join(ANSWER_MODELS)}")
    print(f"Chunks recuperados por pregunta: top-{TOP_K}\n")

    normalized = normalize_questions()
    if len(normalized) != 3:
        print("ERROR: normalización no devolvió 3 preguntas", file=sys.stderr)
        sys.exit(1)

    print("Cargando chunks de BD...")
    all_chunks = fetch_all_chunks(settings.DATABASE_URL)
    print(f"Total chunks en BD: {len(all_chunks)}\n")

    for idx, question in enumerate(normalized, start=1):
        print(f"\n{'─' * 70}")
        print(f"PREGUNTA {idx}: {question}")
        print(f"{'─' * 70}")

        print("  → embed_text...")
        q_vec = embed_text(question)
        print("  → retrieve_top_chunks...")
        top_chunks = retrieve_top_chunks(q_vec, all_chunks, TOP_K)

        subtopic_ids = {c["subtopic_id"] for c in top_chunks}
        print("  → get_subtopic_names...")
        subtopic_names = get_subtopic_names(settings.DATABASE_URL, subtopic_ids)

        print(f"Chunks recuperados (top-{TOP_K}):")
        for c in top_chunks:
            name = subtopic_names.get(c["subtopic_id"], f"id:{c['subtopic_id']}")
            print(f"  • subtopic={name} (id={c['subtopic_id']})  sim={c['similarity']:.3f}  chunk_id={c['id']}")

        for model in ANSWER_MODELS:
            print(f"  → run_answer({model})...")
            elapsed, answer = run_answer(model, top_chunks, question)
            print_section(f"PREGUNTA {idx} - RESPUESTA", model, elapsed, answer)


if __name__ == "__main__":
    main()