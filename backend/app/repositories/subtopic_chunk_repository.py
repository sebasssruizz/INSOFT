"""Acceso a datos de los chunks de contenido por subtema (subtopic_chunks)."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.content import CourseTopic, Subtopic
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


def list_chunks_for_course(db: Session, course_id: int) -> list[SubtopicChunk]:
    """Chunks de los topics habilitados en un curso (via course_topics).

    Recorre la relación course_topics -> topics -> subtopics -> subtopic_chunks
    y solo devuelve chunks de topics con `enabled=True` en ese curso.
    """
    stmt = (
        select(SubtopicChunk)
        .join(Subtopic, Subtopic.id == SubtopicChunk.subtopic_id)
        .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
        .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
        .order_by(SubtopicChunk.id)
    )
    return list(db.scalars(stmt).all())


def list_chunks_for_course_ids(db: Session, course_ids: list[int]) -> list[SubtopicChunk]:
    """Chunks de topics habilitados en CUALQUIERA de los cursos indicados.

    Usada para acotar la búsqueda global de /rag/search al contenido que el
    usuario puede ver (sus cursos como estudiante o como profesor).
    """
    if not course_ids:
        return []
    stmt = (
        select(SubtopicChunk)
        .join(Subtopic, Subtopic.id == SubtopicChunk.subtopic_id)
        .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
        .where(CourseTopic.course_id.in_(course_ids), CourseTopic.enabled.is_(True))
        # DISTINCT: un chunk habilitado en varios cursos del usuario NO debe
        # devolverse N veces (igual que el índice global, sin duplicados).
        .distinct()
    )
    return list(db.scalars(stmt).all())


def list_all_chunks(db: Session) -> list[SubtopicChunk]:
    """Todos los chunks indexados (para búsqueda global sin filtro de subtema)."""
    return list(db.scalars(select(SubtopicChunk).order_by(SubtopicChunk.id)).all())


def delete_chunks_for_subtopic(db: Session, subtopic_id: int) -> int:
    """Elimina todos los chunks de un subtema (útil para reindexar)."""
    result = db.execute(
        delete(SubtopicChunk).where(SubtopicChunk.subtopic_id == subtopic_id)
    )
    db.commit()
    return result.rowcount or 0