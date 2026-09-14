"""Esquemas Pydantic para el endpoint de IA (/api/ai/ask)."""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Petición de pregunta al asistente de IA."""

    question: str = Field(..., max_length=500, description="Pregunta del estudiante")
    subtopic_id: int | None = Field(
        default=None, description="Subtema opcional para limitar la búsqueda"
    )


class AskResponse(BaseModel):
    """Respuesta del asistente de IA."""

    respuesta: str = Field(..., description="Respuesta generada por el modelo")
    subtopic_id: int | None = Field(
        default=None, description="Subtema usado como filtro (si se pasó)"
    )
    chunks_usados: int = Field(
        ..., description="Número de chunks recuperados y usados como contexto"
    )