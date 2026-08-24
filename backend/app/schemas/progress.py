from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProgressUpdate(BaseModel):
    course_id: int
    subtopic_id: int
    completed: bool = True


class ProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    subtopic_id: int
    completed: bool
    updated_at: datetime


class CourseProgressSummary(BaseModel):
    course_id: int
    total_subtopics: int
    completed_subtopics: int
    percentage: float
