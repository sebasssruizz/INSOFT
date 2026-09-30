"""Respuestas de estudiantes a preguntas del quiz (intentos calificados en servidor).

Cada respuesta queda atada a un intento (`attempt_id` UUID): todas las
respuestas del mismo intento comparten identificador, lo que permite
estadísticas por quiz y hace el endpoint idempotente ante reintentos.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class QuestionAnswer(Base):
    """Respuesta de un estudiante a una pregunta concreta dentro de un intento."""

    __tablename__ = "question_answers"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
        Index("ix_question_answers_user_subtopic", "user_id", "subtopic_id"),
        Index("ix_question_answers_question", "question_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    # Desnormalizado para consultas rápidas de estadísticas por subtema.
    subtopic_id: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_id: Mapped[UUID] = mapped_column(nullable=False)
    selected_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User")
    question = relationship("Question")

    def __repr__(self) -> str:  # pragma: no cover - utilidad de depuración
        return f"<QuestionAnswer id={self.id} user_id={self.user_id} question_id={self.question_id}>"
