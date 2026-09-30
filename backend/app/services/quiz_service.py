"""Respuestas de quiz calificadas en el servidor.

El estudiante envía su elección; el backend calcula `is_correct`, guarda la
respuesta (idempotente por attempt_id + question_id) y devuelve el resultado,
incluida la explicación: la respuesta correcta deja de viajar al cliente
antes de responder.
"""
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.content import Question, QuestionStatus
from app.models.question_answer import QuestionAnswer
from app.repositories import quiz_answer_repository as quiz_answer_repo
from app.services.ai_service import _ensure_subtopic_access
from app.services.exceptions import ForbiddenError, NotFoundError


def _validate_attempt_id(attempt_id) -> UUID:
    """El attempt_id debe ser un UUID válido (422 si no)."""
    if isinstance(attempt_id, UUID):
        return attempt_id
    try:
        return UUID(str(attempt_id))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail="attempt_id debe ser un UUID válido.")


def submit_answer(
    db: Session,
    current_user,
    question_id: int,
    selected_index: int,
    attempt_id,
) -> dict:
    """Registra la respuesta de un intento y califica en el servidor.

    - Valida acceso del usuario al subtema de la pregunta (misma regla que /ask).
    - Solo preguntas `approved` (404 si no).
    - Idempotente por (attempt_id, question_id): si ya existe, devuelve la
      respuesta guardada sin crear duplicados.
    """
    attempt_uuid = _validate_attempt_id(attempt_id)
    if not isinstance(selected_index, int) or not 0 <= selected_index <= 3:
        raise HTTPException(
            status_code=422, detail="selected_index debe estar entre 0 y 3."
        )

    question = db.get(Question, question_id)
    if question is None or question.status != QuestionStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")

    try:
        _ensure_subtopic_access(db, current_user, question.subtopic_id)
    except (NotFoundError, ForbiddenError) as exc:
        raise HTTPException(status_code=403, detail=exc.detail)

    # Idempotencia: una respuesta ya guardada se devuelve tal cual.
    existing = quiz_answer_repo.get_for_attempt(db, attempt_uuid, question_id)
    if existing is not None:
        return _result(existing)

    answer = quiz_answer_repo.create(
        db,
        user_id=current_user.id,
        question_id=question.id,
        subtopic_id=question.subtopic_id,
        attempt_id=attempt_uuid,
        selected_index=selected_index,
        is_correct=selected_index == question.correct_index,
    )
    return _result(answer)


def _result(answer: QuestionAnswer) -> dict:
    """Resultado para el estudiante: correcto/incorrecto + explicación (ya respondió)."""
    question = answer.question
    return {
        "is_correct": answer.is_correct,
        "correct_index": question.correct_index,
        "explanation": question.explanation,
    }
