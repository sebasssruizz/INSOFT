from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course, CourseMembership, CourseType
from app.models.user import User, UserRole


def get_by_id(db: Session, course_id: int) -> Course | None:
    return db.get(Course, course_id)


def get_by_code(db: Session, code: str) -> Course | None:
    return db.scalar(select(Course).where(Course.code == code.strip().upper()))


def get_general_course(db: Session) -> Course | None:
    return db.scalar(select(Course).where(Course.type == CourseType.GENERAL).limit(1))


def create(db: Session, *, name: str, description: str | None, code: str | None,
           course_type: CourseType, teacher_id: int | None) -> Course:
    course = Course(
        name=name,
        description=description,
        code=code,
        type=course_type,
        teacher_id=teacher_id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def get_membership(db: Session, course_id: int, user_id: int) -> CourseMembership | None:
    return db.scalar(
        select(CourseMembership).where(
            CourseMembership.course_id == course_id,
            CourseMembership.user_id == user_id,
        )
    )


def create_membership(db: Session, course_id: int, user_id: int) -> CourseMembership:
    membership = CourseMembership(course_id=course_id, user_id=user_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def get_courses_for_student(db: Session, user_id: int) -> list[Course]:
    stmt = (
        select(Course)
        .join(CourseMembership, CourseMembership.course_id == Course.id)
        .where(CourseMembership.user_id == user_id, Course.active.is_(True))
        .order_by(Course.type, Course.created_at)  # GENERAL antes que TEACHER
    )
    return list(db.scalars(stmt).all())


def get_courses_for_teacher(db: Session, teacher_id: int) -> list[Course]:
    stmt = (
        select(Course)
        .where(Course.teacher_id == teacher_id)
        .order_by(Course.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def count_students(db: Session, course_id: int) -> int:
    stmt = (
        select(func.count(User.id))
        .join(CourseMembership, CourseMembership.user_id == User.id)
        .where(CourseMembership.course_id == course_id, User.role == UserRole.STUDENT)
    )
    return db.scalar(stmt) or 0


def get_students(db: Session, course_id: int) -> list[tuple[User, object]]:
    """Devuelve (usuario, fecha de inscripción) de los estudiantes del curso."""
    stmt = (
        select(User, CourseMembership.joined_at)
        .join(CourseMembership, CourseMembership.user_id == User.id)
        .where(CourseMembership.course_id == course_id, User.role == UserRole.STUDENT)
        .order_by(CourseMembership.joined_at)
    )
    return list(db.execute(stmt).all())
