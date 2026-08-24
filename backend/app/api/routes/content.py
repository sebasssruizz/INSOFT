from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.content import SubtopicRead, TopicWithSubtopics
from app.services import content_service

router = APIRouter(tags=["content"])


@router.get("/courses/{course_id}/topics", response_model=list[TopicWithSubtopics])
def get_course_topics(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Temas y subtemas del contenido oficial habilitados en el curso."""
    return content_service.get_course_content(db, current_user, course_id)


@router.get("/subtopics/{subtopic_id}", response_model=SubtopicRead)
def get_subtopic(
    subtopic_id: int,
    course_id: int = Query(..., description="Curso desde el que se consulta el contenido"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return content_service.get_subtopic_detail(db, current_user, course_id, subtopic_id)
