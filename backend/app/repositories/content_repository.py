from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.content import CourseTopic, Question, Subtopic, Topic
from app.models.question_meta import QuestionSource, QuestionStatus


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
        .options(
            selectinload(CourseTopic.topic)
            .selectinload(Topic.subtopics)
            .selectinload(Subtopic.questions)
        )
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


def get_subtopics_for_course(db: Session, course_id: int) -> list[Subtopic]:
    """Subtemas habilitados del curso, con sus preguntas cargadas."""
    stmt = (
        select(Subtopic)
        .options(selectinload(Subtopic.questions))
        .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
        .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
        .order_by(Subtopic.topic_id, Subtopic.order)
    )
    return list(db.scalars(stmt).all())


def count_course_topics(db: Session, course_id: int) -> int:
    stmt = select(CourseTopic.id).where(
        CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True)
    )
    return len(list(db.scalars(stmt).all()))


def get_subtopic_ids_for_course(db: Session, course_id: int) -> list[int]:
    stmt = (
        select(Subtopic.id)
        .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
        .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
    )
    return list(db.scalars(stmt).all())


def get_approved_questions_by_subtopic(db: Session, subtopic_id: int) -> list[Question]:
    """Preguntas visibles para estudiantes de un subtema (solo approved).

    Filtro centralizado: TODO listado para estudiantes debe pasar por aquí
    (oficiales + docentes + IA aprobadas). Orden por `order` del subtema.
    """
    return list(
        db.scalars(
            select(Question)
            .where(Question.subtopic_id == subtopic_id, Question.status == QuestionStatus.APPROVED)
            .order_by(Question.order)
        ).all()
    )


def get_approved_questions_by_topic(db: Session, topic_id: int) -> list[Question]:
    """Preguntas aprobadas de todos los subtemas de una unidad, ordenadas."""
    return list(
        db.scalars(
            select(Question)
            .join(Subtopic, Subtopic.id == Question.subtopic_id)
            .where(Subtopic.topic_id == topic_id, Question.status == QuestionStatus.APPROVED)
            .order_by(Subtopic.order, Question.order)
        ).all()
    )


def next_question_order(db: Session, subtopic_id: int) -> int:
    """Siguiente valor de `order` para una pregunta nueva del subtema.

    Único punto de cálculo (creación manual, generación IA e importador).
    """
    current_max = db.scalar(
        select(func.max(Question.order)).where(Question.subtopic_id == subtopic_id)
    )
    return (current_max + 1) if current_max is not None else 0


def find_duplicate_prompt(
    db: Session, subtopic_id: int, normalized_prompt: str, exclude_question_id: int | None = None
) -> Question | None:
    """Pregunta existente en el subtema con el mismo enunciado normalizado.

    Ignora las rechazadas (se pueden re-crear versiones nuevas). A escala de
    subtema (pocas preguntas) la comparación normalizada se hace en Python
    con la misma función que normaliza el nuevo enunciado.
    """
    from app.services.question_service import normalize_prompt

    stmt = select(Question).where(
        Question.subtopic_id == subtopic_id,
        Question.status != QuestionStatus.REJECTED,
    )
    if exclude_question_id is not None:
        stmt = stmt.where(Question.id != exclude_question_id)
    for question in db.scalars(stmt).all():
        if normalize_prompt(question.prompt) == normalized_prompt:
            return question
    return None


def count_approved_questions_by_subtopics(db: Session, subtopic_ids: list[int]) -> dict[int, int]:
    """Conteo de preguntas aprobadas por subtema (una sola query agregada)."""
    if not subtopic_ids:
        return {}
    rows = db.execute(
        select(Question.subtopic_id, func.count(Question.id))
        .where(
            Question.subtopic_id.in_(subtopic_ids),
            Question.status == QuestionStatus.APPROVED,
        )
        .group_by(Question.subtopic_id)
    ).all()
    return dict(rows)


def count_questions_by_status_and_source(db: Session, topic_id: int) -> dict[int, dict[str, int]]:
    """Conteos por subtema de una unidad: {subtopic_id: {status/source: n}}.

    Una sola query agregada (GROUP BY) para alimentar el resumen del panel
    del profesor sin N+1.
    """
    rows = db.execute(
        select(
            Question.subtopic_id,
            Question.status,
            Question.source,
            func.count(Question.id),
        )
        .join(Subtopic, Subtopic.id == Question.subtopic_id)
        .where(Subtopic.topic_id == topic_id)
        .group_by(Question.subtopic_id, Question.status, Question.source)
    ).all()

    counts: dict[int, dict[str, int]] = {}
    for subtopic_id, status, source, total in rows:
        bucket = counts.setdefault(subtopic_id, {})
        bucket[status] = bucket.get(status, 0) + total
        bucket[source] = bucket.get(source, 0) + total
    return counts


def get_question(db: Session, question_id: int) -> Question | None:
    return db.get(Question, question_id)
