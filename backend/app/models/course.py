import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CourseType(str, enum.Enum):
    GENERAL = "GENERAL"  # Curso General de Oftalmología, creado por el sistema
    TEACHER = "TEACHER"  # Curso creado por un profesor


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    type: Mapped[CourseType] = mapped_column(Enum(CourseType), default=CourseType.TEACHER, nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    teacher = relationship("User", back_populates="taught_courses")
    memberships = relationship("CourseMembership", back_populates="course", cascade="all, delete-orphan")
    course_topics = relationship(
        "CourseTopic", back_populates="course", cascade="all, delete-orphan", order_by="CourseTopic.order"
    )


class CourseMembership(Base):
    """Relación muchos-a-muchos entre estudiantes y cursos."""

    __tablename__ = "course_memberships"
    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_membership_course_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    course = relationship("Course", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
