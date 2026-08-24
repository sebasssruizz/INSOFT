from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Topic(Base):
    """Tema del contenido académico oficial de Oftalmología (único, centralizado)."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subtopics = relationship(
        "Subtopic", back_populates="topic", cascade="all, delete-orphan", order_by="Subtopic.order"
    )
    course_topics = relationship("CourseTopic", back_populates="topic", cascade="all, delete-orphan")


class Subtopic(Base):
    """Subtema con el contenido oficial. Nunca se duplica por curso."""

    __tablename__ = "subtopics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    topic = relationship("Topic", back_populates="subtopics")


class CourseTopic(Base):
    """Asocia el contenido oficial a un curso sin duplicarlo.

    Permite que en el futuro un curso habilite/deshabilite temas concretos.
    """

    __tablename__ = "course_topics"
    __table_args__ = (UniqueConstraint("course_id", "topic_id", name="uq_course_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    course = relationship("Course", back_populates="course_topics")
    topic = relationship("Topic", back_populates="course_topics")
