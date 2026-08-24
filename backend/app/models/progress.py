from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Progress(Base):
    """Progreso de un estudiante sobre un subtema dentro de un curso."""

    __tablename__ = "progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "subtopic_id", name="uq_progress_user_course_subtopic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    subtopic_id: Mapped[int] = mapped_column(ForeignKey("subtopics.id"), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="progress_records")
    subtopic = relationship("Subtopic")
