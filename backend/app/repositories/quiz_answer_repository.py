"""Acceso a datos de las respuestas de estudiantes a preguntas del quiz."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import Integer, case, func, select
from sqlalchemy.orm import Session

from app.models.content import Question
from app.models.question_answer import QuestionAnswer
from app.models.course import CourseMembership
from app.models.user import User, UserRole


def create(
    db: Session,
    *,
    user_id: int,
    question_id: int,
    subtopic_id: int,
    attempt_id: UUID,
    selected_index: int,
    is_correct: bool,
) -> QuestionAnswer:
    answer = QuestionAnswer(
        user_id=user_id,
        question_id=question_id,
        subtopic_id=subtopic_id,
        attempt_id=attempt_id,
        selected_index=selected_index,
        is_correct=is_correct,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def get_for_attempt(
    db: Session, attempt_id: UUID, question_id: int
) -> QuestionAnswer | None:
    """Busca la respuesta ya guardada para (attempt_id, question_id)."""
    stmt = select(QuestionAnswer).where(
        QuestionAnswer.attempt_id == attempt_id,
        QuestionAnswer.question_id == question_id,
    )
    return db.scalar(stmt)


def question_has_answers(db: Session, question_id: int) -> bool:
    """True si algún estudiante respondió esta pregunta (para archivar vs borrar)."""
    stmt = (
        select(QuestionAnswer.id)
        .where(QuestionAnswer.question_id == question_id)
        .limit(1)
    )
    return db.scalar(stmt) is not None


def _get_teacher_student_ids(db: Session, teacher_id: int) -> list[int]:
    """user_ids de estudiantes inscritos en cursos del profesor."""
    from app.repositories.course_repository import get_courses_for_teacher

    courses = get_courses_for_teacher(db, teacher_id)
    course_ids = [c.id for c in courses]
    if not course_ids:
        return []
    stmt = (
        select(CourseMembership.user_id)
        .where(CourseMembership.course_id.in_(course_ids))
        .join(User, User.id == CourseMembership.user_id)
        .where(User.role == UserRole.STUDENT)
        .distinct()
    )
    return list(db.scalars(stmt).all())


def _conditions(
    db: Session,
    teacher_id: int,
    *,
    course_id=None,
    subtopic_id=None,
    from_date=None,
    to_date=None,
):
    """Condiciones comunes de stats: estudiantes del profesor + filtros."""
    student_ids = _get_teacher_student_ids(db, teacher_id)
    conditions = [QuestionAnswer.user_id.in_(student_ids)]
    if course_id is not None:
        # Preguntas de los subtemas de los topics habilitados en ese curso.
        from app.models.content import CourseTopic, Subtopic

        sub_ids = list(
            db.scalars(
                select(Subtopic.id)
                .join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
                .where(CourseTopic.course_id == course_id, CourseTopic.enabled.is_(True))
            ).all()
        )
        conditions.append(QuestionAnswer.subtopic_id.in_(sub_ids))
    if subtopic_id is not None:
        conditions.append(QuestionAnswer.subtopic_id == subtopic_id)
    if from_date is not None:
        conditions.append(QuestionAnswer.answered_at >= from_date)
    if to_date is not None:
        conditions.append(QuestionAnswer.answered_at <= to_date)
    return conditions, student_ids


def _percent(correct: int, total: int) -> int:
    return round(100 * correct / total) if total else 0


def get_stats_overview(
    db: Session,
    teacher_id: int,
    *,
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> dict:
    """Intentos, respuestas totales, % acierto global y estudiantes activos."""
    empty = {
        "total_intentos": 0,
        "total_respuestas": 0,
        "porcentaje_acierto": 0,
        "estudiantes_activos": 0,
    }
    conditions, student_ids = _conditions(
        db, teacher_id, course_id=course_id, subtopic_id=subtopic_id,
        from_date=from_date, to_date=to_date,
    )
    if not student_ids:
        return empty

    totals = db.execute(
        select(
            func.count(QuestionAnswer.id),
            func.sum(case((QuestionAnswer.is_correct.is_(True), 1), else_=0)),
            func.count(func.distinct(QuestionAnswer.attempt_id)),
            func.count(func.distinct(QuestionAnswer.user_id)),
        ).where(*conditions)
    ).one()
    total_respuestas, correctas, total_intentos, estudiantes_activos = totals

    return {
        "total_intentos": int(total_intentos or 0),
        "total_respuestas": int(total_respuestas or 0),
        "porcentaje_acierto": _percent(int(correctas or 0), int(total_respuestas or 0)),
        "estudiantes_activos": int(estudiantes_activos or 0),
    }


def get_stats_questions(
    db: Session,
    teacher_id: int,
    *,
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Por pregunta: respuestas, % acierto y opción incorrecta más elegida."""
    conditions, student_ids = _conditions(
        db, teacher_id, course_id=course_id, subtopic_id=subtopic_id,
        from_date=from_date, to_date=to_date,
    )
    if not student_ids:
        return [], 0

    totals = dict(
        db.execute(
            select(QuestionAnswer.question_id, func.count(QuestionAnswer.id))
            .where(*conditions)
            .group_by(QuestionAnswer.question_id)
        ).all()
    )
    correct = dict(
        db.execute(
            select(QuestionAnswer.question_id, func.count(QuestionAnswer.id))
            .where(*conditions, QuestionAnswer.is_correct.is_(True))
            .group_by(QuestionAnswer.question_id)
        ).all()
    )
    ordered_ids = sorted(totals, key=lambda qid: totals[qid], reverse=True)
    total = len(ordered_ids)

    rows = []
    for qid in ordered_ids[offset : offset + min(limit, 200)]:
        question = db.get(Question, qid)
        if question is None:
            continue
        wrong_counts = db.execute(
            select(QuestionAnswer.selected_index, func.count(QuestionAnswer.id))
            .where(
                *conditions,
                QuestionAnswer.question_id == qid,
                QuestionAnswer.is_correct.is_(False),
            )
            .group_by(QuestionAnswer.selected_index)
        ).all()
        most_wrong = max(wrong_counts, key=lambda r: r[1])[0] if wrong_counts else None
        rows.append(
            {
                "question_id": qid,
                "prompt": question.prompt,
                "subtopic_id": question.subtopic_id,
                "respuestas": int(totals[qid]),
                "porcentaje_acierto": _percent(int(correct.get(qid, 0)), int(totals[qid])),
                "opcion_incorrecta_mas_elegida": most_wrong,
            }
        )
    return rows, total


def get_stats_students(
    db: Session,
    teacher_id: int,
    *,
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Por estudiante: respuestas, % acierto y última actividad."""
    conditions, student_ids = _conditions(
        db, teacher_id, course_id=course_id, subtopic_id=subtopic_id,
        from_date=from_date, to_date=to_date,
    )
    if not student_ids:
        return [], 0

    stats_subq = (
        select(
            QuestionAnswer.user_id,
            func.count(QuestionAnswer.id).label("respuestas"),
            func.sum(case((QuestionAnswer.is_correct.is_(True), 1), else_=0)).label("correctas"),
            func.max(QuestionAnswer.answered_at).label("ultima_actividad"),
        )
        .where(*conditions)
        .group_by(QuestionAnswer.user_id)
        .subquery()
    )
    total = db.scalar(select(func.count()).select_from(stats_subq)) or 0
    stmt = (
        select(
            User.id,
            User.name,
            stats_subq.c.respuestas,
            stats_subq.c.correctas,
            stats_subq.c.ultima_actividad,
        )
        .join(stats_subq, User.id == stats_subq.c.user_id)
        .order_by(stats_subq.c.ultima_actividad.desc())
        .limit(min(limit, 200))
        .offset(offset)
    )
    rows = db.execute(stmt).all()

    result = []
    for user_id_val, nombre, respuestas, correctas, ultima in rows:
        result.append(
            {
                "user_id": user_id_val,
                "nombre": nombre,
                "respuestas": int(respuestas),
                "porcentaje_acierto": _percent(int(correctas or 0), int(respuestas)),
                "ultima_actividad": ultima.isoformat() if ultima else None,
            }
        )
    return result, total


def get_stats_subtopics(
    db: Session,
    teacher_id: int,
    *,
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[dict]:
    """% acierto por subtema."""
    from app.models.content import Subtopic

    conditions, student_ids = _conditions(
        db, teacher_id, course_id=course_id, subtopic_id=subtopic_id,
        from_date=from_date, to_date=to_date,
    )
    if not student_ids:
        return []

    rows = db.execute(
        select(
            QuestionAnswer.subtopic_id,
            func.count(QuestionAnswer.id),
            func.sum(case((QuestionAnswer.is_correct.is_(True), 1), else_=0)),
        )
        .where(*conditions)
        .group_by(QuestionAnswer.subtopic_id)
    ).all()

    result = []
    for sid, respuestas, correctas in rows:
        subtopic = db.get(Subtopic, sid)
        result.append(
            {
                "subtopic_id": sid,
                "nombre": subtopic.name if subtopic else f"Subtema {sid}",
                "respuestas": int(respuestas),
                "porcentaje_acierto": _percent(int(correctas or 0), int(respuestas)),
            }
        )
    return sorted(result, key=lambda item: item["respuestas"], reverse=True)


def iter_answers_for_export(
    db: Session,
    teacher_id: int,
    *,
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
):
    """Filas planas de respuestas (para el CSV de exportación)."""
    conditions, student_ids = _conditions(
        db, teacher_id, course_id=course_id, subtopic_id=subtopic_id,
        from_date=from_date, to_date=to_date,
    )
    if not student_ids:
        return
    stmt = (
        select(
            QuestionAnswer.answered_at,
            User.name,
            User.email,
            QuestionAnswer.question_id,
            Question.prompt,
            QuestionAnswer.subtopic_id,
            QuestionAnswer.selected_index,
            QuestionAnswer.is_correct,
            QuestionAnswer.attempt_id,
        )
        .join(User, User.id == QuestionAnswer.user_id)
        .join(Question, Question.id == QuestionAnswer.question_id)
        .where(*conditions)
        .order_by(QuestionAnswer.answered_at.desc())
    )
    for row in db.execute(stmt).all():
        yield row
