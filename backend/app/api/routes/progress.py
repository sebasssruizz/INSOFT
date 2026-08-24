from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_student
from app.database.session import get_db
from app.models.user import User
from app.schemas.progress import CourseProgressSummary, ProgressRead, ProgressUpdate
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("", response_model=ProgressRead)
def update_progress(
    payload: ProgressUpdate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Marca un subtema como completado (o lo desmarca). Solo el propio estudiante."""
    return progress_service.set_progress(
        db, current_user, payload.course_id, payload.subtopic_id, payload.completed
    )


@router.get("", response_model=list[CourseProgressSummary])
def get_all_progress(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return progress_service.get_all_progress(db, current_user)


@router.get("/course", response_model=CourseProgressSummary)
def get_course_progress(
    course_id: int = Query(...),
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return progress_service.get_course_progress(db, current_user, course_id)
