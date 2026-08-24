"""Lógica de negocio del progreso del estudiante."""
from sqlalchemy.orm import Session

from app.models.progress import Progress
from app.models.user import User
from app.repositories import content_repository as content_repo
from app.repositories import course_repository as course_repo
from app.repositories import progress_repository as progress_repo
from app.services.exceptions import BadRequestError, ForbiddenError, NotFoundError


def _check_membership(db: Session, student: User, course_id: int):
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        raise NotFoundError("Curso no encontrado.")
    if course_repo.get_membership(db, course_id, student.id) is None:
        raise ForbiddenError("Debes pertenecer al curso para registrar progreso en él.")
    return course


def set_progress(db: Session, student: User, course_id: int, subtopic_id: int, completed: bool) -> Progress:
    _check_membership(db, student, course_id)

    allowed_ids = content_repo.get_subtopic_ids_for_course(db, course_id)
    if subtopic_id not in allowed_ids:
        raise BadRequestError("Ese subtema no pertenece al contenido de este curso.")

    return progress_repo.upsert(db, student.id, course_id, subtopic_id, completed)


def get_course_progress(db: Session, student: User, course_id: int) -> dict:
    _check_membership(db, student, course_id)
    subtopic_ids = content_repo.get_subtopic_ids_for_course(db, course_id)
    total = len(subtopic_ids)
    completed = progress_repo.count_completed_in_course(db, student.id, course_id, subtopic_ids)
    return {
        "course_id": course_id,
        "total_subtopics": total,
        "completed_subtopics": completed,
        "percentage": round((completed / total) * 100, 1) if total > 0 else 0.0,
    }


def get_all_progress(db: Session, student: User) -> list[dict]:
    courses = course_repo.get_courses_for_student(db, student.id)
    return [get_course_progress(db, student, course.id) for course in courses]
