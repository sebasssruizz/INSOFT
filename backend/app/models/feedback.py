from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), nullable=False)
    comentario: Mapped[str] = mapped_column(Text, nullable=False)
    pagina: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class UsabilityEvaluation(Base):
    __tablename__ = "usability_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    submission_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    respuestas: Mapped[dict] = mapped_column(JSON, nullable=False)
    dispositivo: Mapped[str] = mapped_column(String(30), nullable=False)
    comentario: Mapped[str] = mapped_column(Text, nullable=False)
    pagina: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
