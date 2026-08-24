from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.progress import Progress


def get_record(db: Session, user_id: int, course_id: int, subtopic_id: int) -> Progress | None:
    return db.scalar(
        select(Progress).where(
            Progress.user_id == user_id,
            Progress.course_id == course_id,
            Progress.subtopic_id == subtopic_id,
        )
    )


def upsert(db: Session, user_id: int, course_id: int, subtopic_id: int, completed: bool) -> Progress:
    record = get_record(db, user_id, course_id, subtopic_id)
    if record is None:
        record = Progress(
            user_id=user_id, course_id=course_id, subtopic_id=subtopic_id, completed=completed
        )
        db.add(record)
    else:
        record.completed = completed
    db.commit()
    db.refresh(record)
    return record


def get_for_course(db: Session, user_id: int, course_id: int) -> list[Progress]:
    return list(db.scalars(
        select(Progress).where(Progress.user_id == user_id, Progress.course_id == course_id)
    ).all())


def count_completed_in_course(db: Session, user_id: int, course_id: int, subtopic_ids: list[int]) -> int:
    if not subtopic_ids:
        return 0
    stmt = select(func.count(Progress.id)).where(
        Progress.user_id == user_id,
        Progress.course_id == course_id,
        Progress.subtopic_id.in_(subtopic_ids),
        Progress.completed.is_(True),
    )
    return db.scalar(stmt) or 0
