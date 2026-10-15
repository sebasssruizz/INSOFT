"""3.1 — medios por subtema: SOLO ENLACES con dominio en lista blanca.

Nunca se sube un binario: el backend no almacena archivos de video/pdf; solo
URLs verificadas contra MEDIA_ALLOWED_HOSTS (defecto vacío = se rechaza todo).
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SubtopicMedia(Base):
    """Enlace multimedia asociado a un subtema (solo URL con host permitido)."""

    __tablename__ = "subtopic_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey("subtopics.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="video", nullable=False)  # video|pdf|animacion|enlace
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    subtopic = relationship("Subtopic", backref="media")
