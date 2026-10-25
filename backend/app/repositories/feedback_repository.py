from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feedback import Feedback, UsabilityEvaluation
from app.schemas.feedback import FeedbackCreate


def create(db: Session, user_id: int, payload: FeedbackCreate) -> Feedback:
    feedback = Feedback(user_id=user_id, **payload.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def create_evaluation(db: Session, user_id: int, payload):
    data = payload.model_dump(mode="json")
    submission_id = data["submission_id"]
    existing = db.scalar(select(UsabilityEvaluation).where(
        UsabilityEvaluation.submission_id == submission_id,
    ))
    if existing is not None:
        if existing.user_id != user_id:
            raise ValueError("submission_conflict")
        return existing
    evaluation = UsabilityEvaluation(user_id=user_id, **data)
    db.add(evaluation)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Dos reintentos concurrentes de la misma entrega cuentan una sola vez.
        existing = db.scalar(select(UsabilityEvaluation).where(
            UsabilityEvaluation.submission_id == submission_id,
        ))
        if existing is not None and existing.user_id == user_id:
            return existing
        raise ValueError("submission_conflict") from None
    db.refresh(evaluation)
    return evaluation
