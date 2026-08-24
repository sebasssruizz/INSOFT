from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_student, require_teacher
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.course import (
    CourseCreate,
    CourseRead,
    JoinCourseRequest,
    JoinCourseResponse,
    StudentCourseRead,
    TeacherCourseRead,
)
from app.schemas.user import StudentRead
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[StudentCourseRead] | list[TeacherCourseRead])
def list_my_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cursos del usuario autenticado (según su rol)."""
    if current_user.role == UserRole.TEACHER:
        return course_service.list_teacher_courses(db, current_user)
    return course_service.list_student_courses(db, current_user)


@router.post("", response_model=CourseRead, status_code=201)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Solo profesores. Genera automáticamente un código único (p. ej. OFT-A72K)."""
    return course_service.create_teacher_course(db, current_user, payload.name, payload.description)


@router.post("/join", response_model=JoinCourseResponse)
def join_course(
    payload: JoinCourseRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    """Solo estudiantes. Une al estudiante a un curso mediante su código."""
    course = course_service.join_course_by_code(db, current_user, payload.code)
    return JoinCourseResponse(message=f"Te has unido a «{course.name}».", course=course)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return course_service.get_course_with_access_check(db, current_user, course_id)


@router.get("/{course_id}/students", response_model=list[StudentRead])
def get_course_students(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Solo el profesor dueño del curso puede ver sus estudiantes."""
    return course_service.get_course_students(db, current_user, course_id)
