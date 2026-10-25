from datetime import datetime
from typing import Literal, Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

HEURISTIC_IDS = tuple(f"h{i:02d}" for i in range(1, 11))


class FeedbackPage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pagina: str = Field(min_length=1, max_length=2048, pattern=r"^/")

    @field_validator("pagina")
    @classmethod
    def pathname_only(cls, value):
        if value.startswith("//") or any(character in value for character in ("?", "#", "\\", "\n", "\r")):
            raise ValueError("Envía solo la ruta de la página, sin parámetros.")
        return value


class FeedbackCreate(FeedbackPage):
    model_config = ConfigDict(extra="forbid")

    tipo: Literal["Petición", "Queja", "Reclamo", "Sugerencia", "Felicitación"]
    categoria: Literal[
        "Diseño y apariencia", "Error o bug", "Contenido educativo", "Asistente de IA",
        "Rendimiento y velocidad", "Cuenta e inicio de sesión", "Otro",
    ]
    comentario: str = Field(min_length=10, max_length=1000)

    @field_validator("comentario", mode="before")
    @classmethod
    def strip_comentario(cls, value):
        return value.strip() if isinstance(value, str) else value


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creado_en: datetime


class EvaluationCreate(FeedbackPage):
    submission_id: UUID
    version: Literal["insoft-nielsen-v1"]
    respuestas: dict[str, Annotated[StrictInt, Field(ge=1, le=5)] | None]
    dispositivo: Literal["Teléfono", "Tableta", "Computador", "Otro", "No indicado"] = "No indicado"
    comentario: str = Field(default="", max_length=2000)

    @field_validator("respuestas")
    @classmethod
    def complete_evaluation(cls, value):
        if set(value) != set(HEURISTIC_IDS):
            raise ValueError("Responde las diez preguntas o marca No lo he probado.")
        if all(rating is None for rating in value.values()):
            raise ValueError("Valora al menos una experiencia que hayas probado.")
        return value

    @field_validator("comentario", mode="before")
    @classmethod
    def trim_comment(cls, value):
        return value.strip() if isinstance(value, str) else value
