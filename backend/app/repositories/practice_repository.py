"""Consultas del modo práctica: pools de banco, pool IA reutilizable y popularidad.

Privacidad: las consultas de otros estudiantes se usan SOLO como conteos
agregados por subtema; nunca se lee ni expone el texto de consultas ajenas.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.ai_query import AiQuery
from app.models.content import Question, Subtopic
from app.models.course import CourseMembership
from app.models.question_answer import QuestionAnswer
from app.models.question_meta import QuestionStatus
from app.models.user import User, UserRole


# ── Popularidad ponderada de subtemas ──────────────────────────────────────


def _peer_ids(db: Session, user) -> list[int]:
    """user_ids de los integrantes de los cursos del usuario (sin el propio)."""
    from app.repositories.course_repository import (
        get_courses_for_student,
        get_courses_for_teacher,
    )

    if user.role == UserRole.TEACHER:
        courses = get_courses_for_teacher(db, user.id)
    else:
        courses = get_courses_for_student(db, user.id)
    course_ids = [c.id for c in courses]
    if not course_ids:
        return []
    stmt = (
        select(CourseMembership.user_id)
        .where(CourseMembership.course_id.in_(course_ids), CourseMembership.user_id != user.id)
        .distinct()
    )
    return list(db.scalars(stmt).all())


def popularity_by_subtopic(
    db: Session, user, subtopic_ids: list[int], *, days: int = 30
) -> dict[int, float]:
    """Peso de cada subtema para elegir dónde practicar.

    popularidad = consultas de pares (mismos cursos, últimos `days` días)
    + 3 × consultas propias + bonus por bajo % de acierto propio.
    """
    if not subtopic_ids:
        return {}
    since = datetime.now(timezone.utc) - timedelta(days=days)

    peers = _peer_ids(db, user)
    scores: dict[int, float] = {sid: 0.0 for sid in subtopic_ids}

    if peers:
        rows = db.execute(
            select(AiQuery.subtopic_id, func.count(AiQuery.id))
            .where(
                AiQuery.subtopic_id.in_(subtopic_ids),
                AiQuery.user_id.in_(peers),
                AiQuery.created_at >= since,
            )
            .group_by(AiQuery.subtopic_id)
        ).all()
        for sid, total in rows:
            if sid in scores:
                scores[sid] += float(total)

    own = db.execute(
        select(AiQuery.subtopic_id, func.count(AiQuery.id))
        .where(
            AiQuery.subtopic_id.in_(subtopic_ids),
            AiQuery.user_id == user.id,
            AiQuery.created_at >= since,
        )
        .group_by(AiQuery.subtopic_id)
    ).all()
    for sid, total in own:
        if sid in scores:
            scores[sid] += 3 * float(total)

    # Bonus por menor % de acierto propio en question_answers (0–5 puntos).
    acc = db.execute(
        select(
            QuestionAnswer.subtopic_id,
            func.count(QuestionAnswer.id),
            func.sum(case((QuestionAnswer.is_correct.is_(True), 1), else_=0)),
        )
        .where(QuestionAnswer.user_id == user.id, QuestionAnswer.subtopic_id.in_(subtopic_ids))
        .group_by(QuestionAnswer.subtopic_id)
    ).all()
    for sid, total, correct in acc:
        if sid in scores and total:
            ratio = float(correct or 0) / float(total)
            scores[sid] += (1 - ratio) * 5

    return scores


# ── Resultados recientes del usuario (exclusión/prioridad del banco) ───────


def recent_results_by_question(
    db: Session, user_id: int, question_ids: list[int], *, days: int = 14
) -> dict[int, bool]:
    """Último resultado del usuario por pregunta dentro de la ventana.

    {question_id: is_correct} con la respuesta más reciente de cada pregunta.
    Preguntas ausentes = nunca respondidas (o fuera de la ventana).
    """
    if not question_ids:
        return {}
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.execute(
        select(QuestionAnswer.question_id, QuestionAnswer.is_correct)
        .where(
            QuestionAnswer.user_id == user_id,
            QuestionAnswer.question_id.in_(question_ids),
            QuestionAnswer.answered_at >= since,
        )
        .order_by(QuestionAnswer.answered_at.desc())
    ).all()
    result: dict[int, bool] = {}
    for question_id, is_correct in rows:
        # La primera aparición ya es la más reciente (orden desc).
        if question_id not in result:
            result[question_id] = bool(is_correct)
    return result


def answered_question_ids(db: Session, user_id: int, question_ids: list[int]) -> set[int]:
    """Preguntas que el usuario respondió alguna vez (para no repetir practice)."""
    if not question_ids:
        return set()
    rows = db.execute(
        select(QuestionAnswer.question_id)
        .where(
            QuestionAnswer.user_id == user_id,
            QuestionAnswer.question_id.in_(question_ids),
        )
        .distinct()
    ).all()
    return {row[0] for row in rows}


# ── Pool de práctica y tope diario de generaciones ─────────────────────────


def practice_pool(db: Session, subtopic_ids: list[int], exclude_ids: list[int]) -> list[Question]:
    """Preguntas practice de los subtemas, excluyendo las dadas (no respondidas antes)."""
    if not subtopic_ids:
        return []
    stmt = (
        select(Question)
        .where(
            Question.subtopic_id.in_(subtopic_ids),
            Question.status == QuestionStatus.PRACTICE,
        )
        .order_by(Subtopic.order, Question.order)
        .join(Subtopic, Subtopic.id == Question.subtopic_id)
    )
    if exclude_ids:
        stmt = stmt.where(Question.id.not_in(exclude_ids))
    return list(db.scalars(stmt).all())


def practice_generated_today_by_subtopic(db: Session, subtopic_ids: list[int]) -> dict[int, int]:
    """Preguntas practice creadas HOY (UTC) por subtema: tope de costo diario."""
    if not subtopic_ids:
        return {}
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = db.execute(
        select(Question.subtopic_id, func.count(Question.id))
        .where(
            Question.subtopic_id.in_(subtopic_ids),
            Question.status == QuestionStatus.PRACTICE,
            Question.created_at >= start_of_day,
        )
        .group_by(Question.subtopic_id)
    ).all()
    return {sid: int(total) for sid, total in rows}
