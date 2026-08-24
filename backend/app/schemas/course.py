from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.course import CourseType


class CourseCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    code: str | None = None
    type: CourseType
    teacher_id: int | None = None
    active: bool
    created_at: datetime


class StudentCourseRead(CourseRead):
    """Curso visto por un estudiante, con su progreso calculado."""

    progress_percentage: float = 0.0
    completed_subtopics: int = 0
    total_subtopics: int = 0


class TeacherCourseRead(CourseRead):
    """Curso visto por su profesor, con estadísticas básicas."""

    student_count: int = 0


class JoinCourseRequest(BaseModel):
    code: str = Field(min_length=4, max_length=20)


class JoinCourseResponse(BaseModel):
    message: str
    course: CourseRead
