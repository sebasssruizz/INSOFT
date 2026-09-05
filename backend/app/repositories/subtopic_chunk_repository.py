"""Acceso a datos de los chunks de contenido por subtema (subtopic_chunks)."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.subtopic_chunk import SubtopicChunk


def create(
    db: Session,
    *,
    subtopic_id: int,
    content: str,
    embedding: list[float],
) -> SubtopicChunk:
    """Crea y persiste un chunk con su embedding."""
    chunk = SubtopicChunk(subtopic_id=subtopic_id, content=content, embedding=embedding)
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def list_chunks_for_subtopic(db: Session, subtopic_id: int) -> list[SubtopicChunk]:
    """Chunks de un subtema, en orden de insertado."""
    stmt = (
        select(SubtopicChunk)
        .where(SubtopicChunk.subtopic_id == subtopic_id)
        .order_by(SubtopicChunk.id)
    )
    return list(db.scalars(stmt).all())


def delete_chunks_for_subtopic(db: Session, subtopic_id: int) -> int:
    """Elimina todos los chunks de un subtema (útil para reindexar)."""
    result = db.execute(
        delete(SubtopicChunk).where(SubtopicChunk.subtopic_id == subtopic_id)
    )
    db.commit()
    return result.rowcount or 0