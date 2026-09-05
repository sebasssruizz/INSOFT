"""Acceso a datos de las consultas de los estudiantes al asistente (ai_queries)."""
from sqlalchemy.orm import Session

from app.models.ai_query import AiQuery


def create(
    db: Session,
    *,
    user_id: int,
    question_original: str,
    subtopic_id: int | None = None,
) -> AiQuery:
    """Registra una pregunta del estudiante (y su subtema asociado si aplica)."""
    query = AiQuery(
        user_id=user_id,
        subtopic_id=subtopic_id,
        question_original=question_original,
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query