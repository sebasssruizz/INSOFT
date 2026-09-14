"""Esquemas Pydantic para la importación de contenido (endpoint /api/content/import)."""

from pydantic import BaseModel, Field


class ImportDocumentRequest(BaseModel):
    """Documento Markdown con unidades, subtemas y preguntas de repaso."""

    document: str = Field(
        ...,
        min_length=20,
        max_length=200_000,
        description="Texto del documento Markdown a importar",
    )


class ImportDocumentResponse(BaseModel):
    """Resumen de la operación de importación (para mostrarlo en la UI)."""

    unidades: int
    unidades_creadas: int
    subtemas_creados: int
    subtemas_actualizados: int
    preguntas_creadas: int
    preguntas_actualizadas: int
    chunks_indexados: int
    subtemas: list[str]