"""Consultas de los estudiantes al asistente (RAG), para su auditoría y mejora.

Guarda la pregunta original del estudiante y, en pasos posteriores, la pregunta
normalizada y la respuesta generada por el pipeline de IA. Es el insumo para
mejorar el modelo y evaluar la calidad de las respuestas.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AiQuery(Base):
    """Registro de una pregunta de un estudiante al asistente de IA."""

    __tablename__ = "ai_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    subtopic_id: Mapped[int | None] = mapped_column(
        ForeignKey("subtopics.id"), nullable=True
    )
    session_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_original: Mapped[str] = mapped_column(Text, nullable=False)
    # Campos que se llenan en pasos posteriores del pipeline de IA.
    question_normalizada: Mapped[str | None] = mapped_column(Text, nullable=True)
    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User")
    subtopic = relationship("Subtopic")

    def __repr__(self) -> str:  # pragma: no cover - utilidad de depuración
        return f"<AiQuery id={self.id} user_id={self.user_id}>"