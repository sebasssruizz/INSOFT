"""Esquemas Pydantic para el endpoint de IA (/api/ai/ask)."""
from uuid import UUID

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Petición de pregunta al asistente de IA."""

    question: str = Field(..., max_length=500, description="Pregunta del estudiante")
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
