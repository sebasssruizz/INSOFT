"""Chunks de contenido de un subtema con sus embeddings (búsqueda semántica RAG).

Cada chunk es un fragmento del contenido oficial de un subtema, acompañado de
su vector de embeddings de 384 dimensiones generado por el modelo local
(`embeddings_service`). El tipo `Vector` de SQLAlchemy se resuelve de forma
transparente a la extensión `vector(n)` de pgvector en PostgreSQL; en SQLite
(tests) se usa un fallback no vectorial.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - entorno sin pgvector instalado
    class Vector:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("pgvector no está instalado. Ejecuta: pip install pgvector")


EMBEDDING_DIMENSIONS = 384  # dimensión del modelo de embeddings (MiniLM-L12 multilingüe)


class SubtopicChunk(Base):
    """Fragmento de contenido de un subtema, con su embedding vectorial."""

    __tablename__ = "subtopic_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subtopic_id: Mapped[int] = mapped_column(
        ForeignKey("subtopics.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Vector | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    subtopic = relationship("Subtopic")

    def __repr__(self) -> str:  # pragma: no cover - utilidad de depuración
        return f"<SubtopicChunk id={self.id} subtopic_id={self.subtopic_id}>"