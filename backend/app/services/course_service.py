"""Lógica de negocio de cursos, membresías y códigos de acceso."""
import secrets
import string

from sqlalchemy.orm import Session

from app.models.course import Course, CourseType
from app.models.user import User
from app.repositories import content_repository as content_repo
from app.repositories import course_repository as course_repo
from app.repositories import progress_repository as progress_repo
from app.services.exceptions import ConflictError, ForbiddenError, NotFoundError

GENERAL_COURSE_NAME = "Curso General de Oftalmología"
GENERAL_COURSE_DESCRIPTION = (
    "Curso oficial de INSOFT con el contenido académico completo de Oftalmología. "
    "Disponible automáticamente para todos los estudiantes."
)

# Alfabeto sin caracteres ambiguos (sin I, L, O, 0, 1) para códigos legibles.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_PREFIX = "OFT-"


def generate_unique_code(db: Session, length: int = 4) -> str:
    """Genera un código único tipo OFT-A72K verificando colisiones en PostgreSQL."""
    for _ in range(20):
        suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))
        code = f"{CODE_PREFIX}{suffix}"
        if course_repo.get_by_code(db, code) is None:
            return code
    raise ConflictError("No se pudo generar un código único. Inténtalo de nuevo.")


def ensure_general_course(db: Session) -> Course:
    """Obtiene (o crea) el Curso General de Oftalmología y le vincula el contenido oficial."""
    course = course_repo.get_general_course(db)
    if course is None:
        course = course_repo.create(
            db,
            name=GENERAL_COURSE_NAME,
            description=GENERAL_COURSE_DESCRIPTION,
            code=None,
            course_type=CourseType.GENERAL,
            teacher_id=None,
        )
    content_repo.link_all_topics_to_course(db, course.id)
    return course


def enroll_student_in_general_course(db: Session, student: User) -> None:
    """Todo estudiante accede automáticamente al Curso General."""
    course = ensure_general_course(db)
    if course_repo.get_membership(db, course.id, student.id) is None:
        course_repo.create_membership(db, course.id, student.id)


def create_teacher_course(db: Session, teacher: User, name: str, description: str | None) -> Course:
    code = generate_unique_code(db)
    course = course_repo.create(
        db,
        name=name,
        description=description,
        code=code,
        course_type=CourseType.TEACHER,
        teacher_id=teacher.id,
    )
    # El curso usa el MISMO contenido oficial centralizado, sin duplicarlo.
    content_repo.link_all_topics_to_course(db, course.id)
    return course


def join_course_by_code(db: Session, student: User, code: str) -> Course:
    course = course_repo.get_by_code(db, code)
    if course is None:
        raise NotFoundError("No existe ningún curso con ese código.")
    if not course.active:
        raise BadRequestError("Este curso no está activo.")
    if course.type != CourseType.TEACHER:
        raise BadRequestError("El Curso General no requiere código de acceso.")
    if course_repo.get_membership(db, course.id, student.id) is not None:
        raise ConflictError("Ya perteneces a este curso.")
    course_repo.create_membership(db, course.id, student.id)
    return course


def _student_course_summary(db: Session, student: User, course: Course) -> dict:
    subtopic_ids = content_repo.get_subtopic_ids_for_course(db, course.id)
    total = len(subtopic_ids)
    completed = progress_repo.count_completed_in_course(db, student.id, course.id, subtopic_ids)
    percentage = round((completed / total) * 100, 1) if total > 0 else 0.0
    return {
        **{c.name: getattr(course, c.name) for c in course.__table__.columns},
        "progress_percentage": percentage,
        "completed_subtopics": completed,
        "total_subtopics": total,
    }


def list_student_courses(db: Session, student: User) -> list[dict]:
    courses = course_repo.get_courses_for_student(db, student.id)
    return [_student_course_summary(db, student, course) for course in courses]


def list_teacher_courses(db: Session, teacher: User) -> list[dict]:
    courses = course_repo.get_courses_for_teacher(db, teacher.id)
    return [
        {
            **{c.name: getattr(course, c.name) for c in course.__table__.columns},
            "student_count": course_repo.count_students(db, course.id),
        }
        for course in courses
    ]


def get_course_with_access_check(db: Session, user: User, course_id: int) -> Course:
    """Autorización: el profesor debe ser dueño del curso; el estudiante debe estar inscrito."""
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        raise NotFoundError("Curso no encontrado.")

    if course.type == CourseType.TEACHER and course.teacher_id == user.id:
        return course  # el profesor dueño siempre tiene acceso a su curso

    if course_repo.get_membership(db, course.id, user.id) is not None:
        return course

    raise ForbiddenError("No tienes acceso a este curso.")


def get_course_students(db: Session, teacher: User, course_id: int) -> list[dict]:
    course = course_repo.get_by_id(db, course_id)
    if course is None:
        raise NotFoundError("Curso no encontrado.")
    if course.teacher_id != teacher.id:
        raise ForbiddenError("Solo puedes consultar los estudiantes de tus propios cursos.")
    return [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "profile_image": student.profile_image,
            "joined_at": joined_at,
        }
        for student, joined_at in course_repo.get_students(db, course.id)
    ]
