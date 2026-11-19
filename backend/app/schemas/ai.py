"""Esquemas Pydantic para el endpoint de IA (/api/ai/ask)."""
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """Petición de pregunta al asistente de IA."""

    question: str = Field(..., min_length=1, max_length=500, description="Pregunta del estudiante")
    topic_id: int | None = None
    selected_text: str | None = Field(default=None, max_length=2000)

    @field_validator("question")
    @classmethod
    def nonblank_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Escribe una pregunta.")
        return value.strip()
    subtopic_id: int | None = Field(
        default=None, description="Subtema opcional para limitar la búsqueda"
    )
    course_id: int | None = Field(
        default=None,
        description="Curso/carpeta actual para acotar el RAG al contenido habilitado"
        " en ese curso. Si se omite, se conserva la búsqueda global.",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Identificador de sesión (UUID) para agrupar consultas del mismo intento",
    )


class AskResponse(BaseModel):
    """Respuesta del asistente de IA."""

    respuesta: str = Field(..., description="Respuesta generada por el modelo")
    query_id: int | None = None
    session_id: UUID | None = None
    sources: list[dict] = Field(default_factory=list)
    degraded: bool = Field(
        default=False,
        description="True cuando la IA no respondió y se entregaron fragmentos del contenido como respaldo",
    )
    subtopic_id: int | None = Field(
        default=None, description="Subtema usado como filtro (si se pasó)"
    )
    chunks_usados: int = Field(
        ..., description="Número de chunks recuperados y usados como contexto"
    )

class AnswerFeedbackRequest(BaseModel):
    helpful: bool
    reason: Literal["context", "incomplete", "incorrect", "other"] | None = None
    comment: str | None = Field(default=None, max_length=1000)


class GenerateQuestionsRequest(BaseModel):
    """Petición de generación de preguntas con IA (solo profesores).

    Debe venir exactamente uno de `subtopic_id` o `topic_id`.
    """

    subtopic_id: int | None = None
    topic_id: int | None = None
    count: int = Field(default=3, ge=1, le=5, description="Cantidad a generar (1-5)")


class GenerateQuestionsResponse(BaseModel):
    """Resultado de la generación: preguntas IA creadas (pending)."""

    generated: list
    requested: int
    created: int
    warning: str | None = None
