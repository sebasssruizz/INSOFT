"""Indexado del contenido oficial de Oftalmología en `subtopic_chunks` (RAG).

Divide el contenido de cada subtema en chunks de ~200-300 palabras (respetando
párrafos completos), genera su embedding con el modelo local de embeddings
(sentence-transformers, CPU) usando `embeddings_service.embed_batch`, y los
persiste en la tabla `subtopic_chunks`.

Cómo ejecutarlo:
    - Localmente, desde backend/ con las variables de entorno de la app activas
      (en especial `DATABASE_URL`, que debe apuntar a tu PostgreSQL):
          python -m app.seed.index_content
    - Dentro del contenedor del backend de Docker Compose:
          docker compose exec backend python -m app.seed.index_content

El script es idempotente: al reindexar un subtema borra primero sus chunks
previos, por lo que también sirve para reindexar contenido actualizado.
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.content import Subtopic
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.services.embeddings_service import embed_batch

DEFAULT_MAX_CHUNK_WORDS = 300


def _split_long_paragraph(paragraph: str, max_words: int) -> list[str]:
    """Divide un párrafo que excede `max_words` por oraciones completas.

    Solo se corta una oración a la mitad cuando ella sola supera el límite.
    """
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", paragraph.strip())
        if s.strip()
    ]
    result: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current, current_words
        if current:
            result.append(" ".join(current))
            current = []
            current_words = 0

    for sentence in sentences:
        words = len(sentence.split())
        if current_words + words <= max_words:
            current.append(sentence)
            current_words += words
            continue
        flush()
        if words > max_words:  # oración sola que excede: se corta por palabras
            buf: list[str] = []
            buf_words = 0
            for word in sentence.split():
                if buf_words < max_words:
                    buf.append(word)
                    buf_words += 1
                else:
                    result.append(" ".join(buf))
                    buf = [word]
                    buf_words = 1
            if buf:
                current = buf
                current_words = buf_words
        else:
            current = [sentence]
            current_words = words
    flush()
    return result


def chunk_subtopic_content(
    content: str, max_words: int = DEFAULT_MAX_CHUNK_WORDS
) -> list[str]:
    """Divide el contenido de un subtema en chunks de ~`max_words` palabras.

    Respeta párrafos completos: un chunk junta párrafos enteros (separados por
    línea en blanco) hasta el límite de palabras y no corta oraciones a la
    mitad. El contenido corto (< `max_words`) devuelve un único chunk.
    """
    text = content.strip()
    if not text:
        return []
    if len(text.split()) <= max_words:
        return [text]

    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current, current_words
        if current:
            chunks.append("\n\n".join(current))
            current = []
            current_words = 0

    for paragraph in paragraphs:
        words = len(paragraph.split())
        if current_words + words <= max_words:
            current.append(paragraph)
            current_words += words
        else:
            flush()
            if words > max_words:
                chunks.extend(_split_long_paragraph(paragraph, max_words))
            else:
                current.append(paragraph)
                current_words = words
    flush()
    return chunks


def index_all_content(db: Session) -> tuple[int, int]:
    """Indexa todo el contenido oficial en `subtopic_chunks`.

    Devuelve `(n_subtopics_indexados, n_chunks_insertados)`. Idempotente:
    elimina los chunks previos de cada subtema antes de reindexarlo.
    """
    subtopics = list(db.scalars(select(Subtopic).order_by(Subtopic.id)).all())
    total_subtopics = 0
    total_chunks = 0
    for subtopic in subtopics:
        chunks = chunk_subtopic_content(subtopic.content)
        if not chunks:
            continue
        vectors = embed_batch(chunks)
        chunk_repo.delete_chunks_for_subtopic(db, subtopic.id)
        for chunk_text, vector in zip(chunks, vectors):
            chunk_repo.create(
                db, subtopic_id=subtopic.id, content=chunk_text, embedding=vector
            )
        total_subtopics += 1
        total_chunks += len(chunks)
        print(f"[index] subtopic {subtopic.id} ({subtopic.name}): {len(chunks)} chunks")
    return total_subtopics, total_chunks


if __name__ == "__main__":
    db = SessionLocal()
    try:
        subtopic_count, chunk_count = index_all_content(db)
        print(f"[index] LISTO: {subtopic_count} subtopics, {chunk_count} chunks indexados")
    finally:
        db.close()