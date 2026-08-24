from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content import CourseTopic, Subtopic, Topic


def get_all_topics(db: Session) -> list[Topic]:
    return list(db.scalars(
        select(Topic).options(selectinload(Topic.subtopics)).order_by(Topic.order)
    ).all())


def get_topic(db: Session, topic_id: int) -> Topic | None:
    return db.scalar(
        select(Topic).options(selectinload(Topic.subtopics)).where(Topic.id == topic_id)
    )


def get_subtopic(db: Session, subtopic_id: int) -> Subtopic | None:
    return db.get(Subtopic, subtopic_id)


def get_course_topics(db: Session, course_id: int) -> list[CourseTopic]:
    """Temas habilitados de un curso, con sus subtemas cargados."""
    stmt = (
        select(CourseTopic)
        .options(selectinload(CourseTopic.topic).selectinload(Topic.subtopics))
        .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
        .order_by(CourseTopic.order)
    )
    return list(db.scalars(stmt).all())


def link_all_topics_to_course(db: Session, course_id: int) -> None:
    """Vincula todos los temas oficiales al curso (sin duplicar contenido)."""
    topics = get_all_topics(db)
    for topic in topics:
        exists = db.scalar(
            select(CourseTopic).where(
                CourseTopic.course_id == course_id, CourseTopic.topic_id == topic.id
            )
        )
        if not exists:
            db.add(CourseTopic(course_id=course_id, topic_id=topic.id, enabled=True, order=topic.order))
    db.commit()


def get_subtopic_ids_for_course(db: Session, course_id: int) -> list[int]:
    stmt = (
        select(Subtopic.id)
        .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
        .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
    )
    return list(db.scalars(stmt).all())
