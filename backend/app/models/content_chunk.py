"""Fragmentos de contenido indexados como vectores para búsqueda semántica (RAG).

Cada chunk pertenece a un subtema del contenido oficial y lleva asociado un
vector de embeddings numérico almacenado en PostgreSQL + pgvector. El tipo
`Vector` de SQLAlchemy se resuelve de forma transparente a la extensión
`vector(n)` de pgvector cuando la base es PostgreSQL; en SQLite (tests) se usa
un fallback no vectorial.
"""
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - entorno sin pgvector instalado
    class Vector:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("pgvector no está instalado. Ejecuta: pip install pgvector")


EMBEDDING_DIMENSIONS = 384  # dimensión por defecto del modelo de embeddings


class ContentChunk(Base):
    """Fragmento de texto del contenido oficial, con su vector de embeddings."""

    __tablename__ = "content_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey("subtopics.id"), nullable=False)
    # Orden del fragmento dentro del subtema (para poder reconstruir el texto)
    chunk_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # El vector se crea mediante la extensión pgvector (PostgreSQL).
    embedding: Mapped[Vector | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )

    subtopic = relationship("Subtopic")

    def __repr__(self) -> str:  # pragma: no cover - utilidad de depuración
        return f"<ContentChunk id={self.id} subtopic_id={self.subtopic_id} order={self.chunk_order}>"
