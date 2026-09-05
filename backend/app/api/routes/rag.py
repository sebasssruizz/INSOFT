"""Ruta de búsqueda semántica (RAG) sobre los chunks indexados del contenido.

Usa `SubtopicChunk` a través de `subtopic_chunk_repository` y el embedding del
modelo local (`embeddings_service.embed_text`). La búsqueda incluye
autorización: si el request filtra por `subtopic_id`, el usuario debe tener
acceso a ese subtema (estudiante inscrito o profesor dueño de un curso que lo
incluya); si no, responde 403.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.content import CourseTopic, Subtopic
from app.models.user import User, UserRole
from app.repositories import course_repository as course_repo
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.schemas.rag import ChunkResult, SearchRequest, SearchResponse
from app.services.embeddings_service import cosine_similarity, embed_text
from app.services.exceptions import ForbiddenError, NotFoundError

router = APIRouter(prefix="/rag", tags=["rag"])


def _courses_with_access(db: Session, user: User) -> list[int]:
    """Ids de los cursos a los que el usuario tiene acceso (inscripción o propiedad)."""
    if user.role == UserRole.TEACHER:
        return [c.id for c in course_repo.get_courses_for_teacher(db, user.id)]
    return [c.id for c in course_repo.get_courses_for_student(db, user.id)]


def _ensure_subtopic_access(db: Session, user: User, subtopic_id: int) -> Subtopic:
    """Valida que el subtema exista y que `user` tenga acceso a él; si no, 403."""
    subtopic = db.get(Subtopic, subtopic_id)
    if subtopic is None:
        raise NotFoundError("Subtema no encontrado.")

    course_ids = _courses_with_access(db, user)
    if not course_ids:
        raise ForbiddenError("No tienes acceso a este subtema.")

    has_access = db.scalar(
        select(CourseTopic.id)
        .where(
            CourseTopic.course_id.in_(course_ids),
            CourseTopic.topic_id == subtopic.topic_id,
            CourseTopic.enabled.is_(True),
        )
        .limit(1)
    )
    if has_access is None:
        raise ForbiddenError("No tienes acceso a este subtema.")
    return subtopic


@router.post("/search", response_model=SearchResponse)
def rag_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Búsqueda semántica sobre el contenido oficial indexado en `subtopic_chunks`."""
    if payload.subtopic_id is not None:
        _ensure_subtopic_access(db, current_user, payload.subtopic_id)
        chunks = chunk_repo.list_chunks_for_subtopic(db, payload.subtopic_id)
    else:
        chunks = chunk_repo.list_all_chunks(db)

    if not chunks:
        return SearchResponse(query=payload.query, results=[])

    query_vector = embed_text(payload.query)
    scored = sorted(
        ((cosine_similarity(chunk.embedding, query_vector), chunk) for chunk in chunks),
        key=lambda item: item[0],
        reverse=True,
    )[: payload.limit]

    subtopic_ids = {chunk.subtopic_id for _, chunk in scored}
    subtopic_names = {
        st.id: st.name
        for st in db.scalars(select(Subtopic).where(Subtopic.id.in_(subtopic_ids)))
    } if scored else {}

    return SearchResponse(
        query=payload.query,
        results=[
            ChunkResult(
                id=chunk.id,
                subtopic_id=chunk.subtopic_id,
                content=chunk.content,
                subtopic_name=subtopic_names.get(chunk.subtopic_id),
                similarity=score,
            )
            for score, chunk in scored
        ],
    )