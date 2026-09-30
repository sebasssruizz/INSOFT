"""Acceso a datos de las consultas de los estudiantes al asistente (ai_queries).

Incluye historiales (propio y de profesor) y estadísticas de uso de IA,
siempre acotadas a los estudiantes inscritos en los cursos del profesor.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_query import AiQuery
from app.models.content import Subtopic
from app.models.course import CourseMembership
from app.models.user import User, UserRole


def create(
    db: Session,
    *,
    user_id: int,
    question_original: str,
    subtopic_id: int | None = None,
    question_normalizada: str | None = None,
    respuesta: str | None = None,
    session_id: UUID | None = None,
    model_used: str | None = None,
    response_time_ms: int | None = None,
) -> AiQuery:
    """Registra una pregunta del estudiante (y su subtema asociado si aplica)."""
    query = AiQuery(
        user_id=user_id,
        subtopic_id=subtopic_id,
        session_id=session_id,
        model_used=model_used,
        response_time_ms=response_time_ms,
        question_original=question_original,
        question_normalizada=question_normalizada,
        respuesta=respuesta,
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


def get_by_user(
    db: Session,
    user_id: int,
    *,
    subtopic_id: int | None = None,
    session_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AiQuery], int]:
    """Devuelve las consultas de un usuario, con filtros opcionales y paginación."""
    conditions = [AiQuery.user_id == user_id]
    if subtopic_id is not None:
        conditions.append(AiQuery.subtopic_id == subtopic_id)
    if session_id is not None:
        conditions.append(AiQuery.session_id == session_id)
    total = db.scalar(select(func.count()).select_from(AiQuery).where(*conditions)) or 0
    rows = db.scalars(
        select(AiQuery)
        .where(*conditions)
        .order_by(AiQuery.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    ).all()
    return list(rows), total


def get_all_filtered(
    db: Session,
    *,
    teacher_id: int,
    subtopic_id: int | None = None,
    session_id: str | None = None,
    user_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AiQuery], int]:
    """Devuelve consultas de estudiantes de un profesor, con filtros (acumulativos, no or)."""
    student_ids = _get_teacher_student_ids(db, teacher_id)
    conditions = [AiQuery.user_id.in_(student_ids)]
    if subtopic_id is not None:
        conditions.append(AiQuery.subtopic_id == subtopic_id)
    if session_id is not None:
        conditions.append(AiQuery.session_id == session_id)
    if user_id is not None:
        conditions.append(AiQuery.user_id == user_id)
    if from_date is not None:
        conditions.append(AiQuery.created_at >= from_date)
    if to_date is not None:
        conditions.append(AiQuery.created_at <= to_date)
    total = db.scalar(select(func.count()).select_from(AiQuery).where(*conditions)) or 0
    rows = db.scalars(
        select(AiQuery)
        .where(*conditions)
        .order_by(AiQuery.created_at.desc())
        .limit(min(limit, 200))
        .offset(offset)
    ).all()
    return list(rows), total


def _get_teacher_student_ids(db: Session, teacher_id: int) -> list[int]:
    """Obtiene los user_ids de estudiantes inscritos en cursos del profesor."""
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


def get_stats_overview(
    db: Session,
    teacher_id: int,
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> dict:
    """Estadísticas generales: total preguntas, tiempo promedio, por subtema, últimos 7 días.

    Siempre filtra a estudiantes inscritos en los cursos del profesor.
    """
    student_ids = _get_teacher_student_ids(db, teacher_id)
    if not student_ids:
        return {
            "total_preguntas": 0,
            "tiempo_respuesta_promedio_ms": 0,
            "preguntas_por_subtema": [],
            "preguntas_ultimos_7_dias": 0,
        }

    conditions = [AiQuery.user_id.in_(student_ids)]
    if from_date is not None:
        conditions.append(AiQuery.created_at >= from_date)
    if to_date is not None:
        conditions.append(AiQuery.created_at <= to_date)

    total = db.scalar(select(func.count()).select_from(AiQuery).where(*conditions)) or 0

    avg_time = db.scalar(
        select(func.avg(AiQuery.response_time_ms)).where(
            *conditions, AiQuery.response_time_ms.is_not(None)
        )
    )

    subtopic_query = (
        select(
            Subtopic.id,
            Subtopic.name,
            func.count(AiQuery.id),
        )
        .join(AiQuery, AiQuery.subtopic_id == Subtopic.id)
        .where(*conditions)
        .group_by(Subtopic.id, Subtopic.name)
    )
    subtopic_rows = db.execute(subtopic_query).all()
    preguntas_por_subtema = [
        {"subtopic_id": sid, "nombre": sname, "total": cnt}
        for sid, sname, cnt in subtopic_rows
    ]

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_total = db.scalar(
        select(func.count())
        .select_from(AiQuery)
        .where(*conditions, AiQuery.created_at >= seven_days_ago)
    ) or 0

    return {
        "total_preguntas": total,
        "tiempo_respuesta_promedio_ms": int(avg_time) if avg_time else 0,
        "preguntas_por_subtema": preguntas_por_subtema,
        "preguntas_ultimos_7_dias": recent_total,
    }


def get_stats_students(
    db: Session,
    teacher_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> tuple[list[dict], int]:
    """Lista de estudiantes con sus stats (preguntas y último uso), filtrada a sus cursos."""
    student_ids = _get_teacher_student_ids(db, teacher_id)
    if not student_ids:
        return [], 0

    conditions = [AiQuery.user_id.in_(student_ids)]
    if from_date is not None:
        conditions.append(AiQuery.created_at >= from_date)
    if to_date is not None:
        conditions.append(AiQuery.created_at <= to_date)

    stats_subq = (
        select(
            AiQuery.user_id,
            func.count(AiQuery.id).label("total_preguntas"),
            func.max(AiQuery.created_at).label("ultima_consulta"),
        )
        .where(*conditions)
        .group_by(AiQuery.user_id)
        .subquery()
    )

    total = db.scalar(
        select(func.count()).select_from(stats_subq)
    ) or 0

    stmt = (
        select(
            User.id,
            User.name,
            func.coalesce(stats_subq.c.total_preguntas, 0),
            stats_subq.c.ultima_consulta,
        )
        .join(stats_subq, User.id == stats_subq.c.user_id)
        .order_by(stats_subq.c.ultima_consulta.desc())
        .limit(min(limit, 200))
        .offset(offset)
    )
    rows = db.execute(stmt).all()

    result = []
    for user_id_val, nombre, total_preguntas, ultima_consulta in rows:
        result.append(
            {
                "user_id": user_id_val,
                "nombre": nombre,
                "total_preguntas": total_preguntas or 0,
                "ultima_consulta": ultima_consulta.isoformat() if ultima_consulta else None,
            }
        )
    return result, total


def get_stats_subtopics(
    db: Session,
    teacher_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> tuple[list[dict], int]:
    """Stats por subtema (conteo y preguntas más frecuentes), filtrado a sus cursos."""
    student_ids = _get_teacher_student_ids(db, teacher_id)
    if not student_ids:
        return [], 0

    conditions = [AiQuery.user_id.in_(student_ids)]
    if from_date is not None:
        conditions.append(AiQuery.created_at >= from_date)
    if to_date is not None:
        conditions.append(AiQuery.created_at <= to_date)

    subtopic_stats = (
        select(
            Subtopic.id,
            Subtopic.name,
            func.count(AiQuery.id).label("total"),
        )
        .join(AiQuery, AiQuery.subtopic_id == Subtopic.id)
        .where(*conditions)
        .group_by(Subtopic.id, Subtopic.name)
        .order_by(func.count(AiQuery.id).desc())
    )
    subtopic_rows = db.execute(subtopic_stats).all()

    total_subtopics = len(subtopic_rows)
    page = subtopic_rows[offset : offset + min(limit, 200)]

    result = []
    for sid, sname, total in page:
        freq_q = (
            select(AiQuery.question_original, func.count(AiQuery.id).label("cnt"))
            .where(*conditions, AiQuery.subtopic_id == sid)
            .group_by(AiQuery.question_original)
            .order_by(func.count(AiQuery.id).desc())
            .limit(5)
        )
        freq_rows = db.execute(freq_q).all()
        preguntas_frecuentes = [q for q, _ in freq_rows]
        if len(preguntas_frecuentes) < 5:
            recent_q = (
                select(AiQuery.question_original)
                .where(*conditions, AiQuery.subtopic_id == sid)
                .order_by(AiQuery.created_at.desc())
                .limit(5)
            )
            for (q,) in db.execute(recent_q).all():
                if q not in preguntas_frecuentes:
                    preguntas_frecuentes.append(q)
            preguntas_frecuentes = preguntas_frecuentes[:5]

        result.append(
            {
                "subtopic_id": sid,
                "nombre": sname,
                "total_preguntas": int(total),
                "preguntas_mas_frecuentes": preguntas_frecuentes,
            }
        )
    return result, total_subtopics
