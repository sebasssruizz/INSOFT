"""Lógica de negocio del banco de preguntas del profesor.

CRUD manual, banco de lectura y revisión de preguntas IA. La generación con
IA vive en ai_service (reutiliza el pipeline RAG); aquí solo se guardan.

Reglas de autorización (helper único `assert_teacher_can_manage_subtopic`):
- 404 si el subtema no existe.
- 403 si el profesor no es dueño de al menos un curso con el topic del
  subtema habilitado.
- Una pregunta solo puede editarse/borrarse/revisarse por su autor
  (`created_by`); las oficiales son de solo lectura para todos.
"""
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import CourseTopic, Question, Subtopic
from app.models.question_meta import QuestionSource, QuestionStatus
from app.models.user import User, UserRole
from app.repositories import content_repository as content_repo
from app.repositories import course_repository as course_repo
from app.services import course_service


def normalize_prompt(prompt: str) -> str:
    """Normaliza un enunciado para detección de duplicados.

    Minúsculas, espacios colapsados, sin signos de apertura ni puntuación
    final (¿ ? . ! ¡ : ; ,).
    """
    normalized = re.sub(r"\s+", " ", prompt.strip().lower())
    return normalized.strip("¿?.!¡:;, ")


def assert_teacher_can_manage_subtopic(db: Session, teacher: User, subtopic_id: int) -> Subtopic:
    """Autorización única de gestión de preguntas sobre un subtema.

    - 404 si el subtema no existe.
    - 403 si el profesor no es dueño de un curso con el topic habilitado.
    """
    subtopic = content_repo.get_subtopic(db, subtopic_id)
    if subtopic is None:
        raise HTTPException(status_code=404, detail="Subtema no encontrado.")

    if teacher.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Solo los profesores pueden gestionar preguntas.")

    course_ids = [c.id for c in course_repo.get_courses_for_teacher(db, teacher.id)]
    if not course_ids:
        raise HTTPException(
            status_code=403, detail="No tienes cursos con este subtema habilitado."
        )

    has_access = db.scalar(
        select(CourseTopic.id).where(
            CourseTopic.course_id.in_(course_ids),
            CourseTopic.topic_id == subtopic.topic_id,
            CourseTopic.enabled.is_(True),
        )
    )
    if has_access is None:
        raise HTTPException(
            status_code=403, detail="No tienes cursos con este subtema habilitado."
        )
    return subtopic


def assert_teacher_can_manage_topic(db: Session, teacher: User, topic_id: int) -> None:
    """Autorización de gestión sobre una unidad completa (para generación IA)."""
    if teacher.role != UserRole.TEACHER:
        raise HTTPException(status_code=403, detail="Solo los profesores pueden gestionar preguntas.")
    course_ids = [c.id for c in course_repo.get_courses_for_teacher(db, teacher.id)]
    if not course_ids:
        raise HTTPException(status_code=403, detail="No tienes cursos con esta unidad habilitada.")
    has_access = db.scalar(
        select(CourseTopic.id).where(
            CourseTopic.course_id.in_(course_ids),
            CourseTopic.topic_id == topic_id,
            CourseTopic.enabled.is_(True),
        )
    )
    if has_access is None:
        raise HTTPException(status_code=403, detail="No tienes cursos con esta unidad habilitada.")


def assert_teacher_can_manage_question(db: Session, teacher: User, question: Question) -> None:
    """Autorización de edición/borrado/revisión de UNA pregunta.

    Requiere (a) poder gestionar su subtema y (b) ser el autor. Las preguntas
    oficiales son de solo lectura (created_by NULL nunca coincide).
    """
    assert_teacher_can_manage_subtopic(db, teacher, question.subtopic_id)
    if question.created_by != teacher.id:
        if question.source == QuestionSource.OFFICIAL:
            raise HTTPException(
                status_code=403,
                detail="Las preguntas oficiales son de solo lectura.",
            )
        raise HTTPException(status_code=403, detail="Solo el autor puede modificar esta pregunta.")


def _clean_options(options: list[str]) -> list[str]:
    """Valida/limpia las 4 opciones: exactamente 4, no vacías, sin duplicados."""
    if len(options) != 4:
        raise HTTPException(status_code=422, detail="Debe haber exactamente 4 opciones (A-D).")
    cleaned = [option.strip() for option in options]
    if any(len(option) < 1 or len(option) > 300 for option in cleaned):
        raise HTTPException(status_code=422, detail="Cada opción debe tener entre 1 y 300 caracteres.")
    lowered = [option.casefold() for option in cleaned]
    if len(set(lowered)) != 4:
        raise HTTPException(status_code=422, detail="Las opciones no pueden repetirse.")
    return cleaned


def _clean_prompt(prompt: str) -> str:
    cleaned = (prompt or "").strip()
    if len(cleaned) < 5 or len(cleaned) > 500:
        raise HTTPException(status_code=422, detail="El enunciado debe tener entre 5 y 500 caracteres.")
    return cleaned


def _clean_explanation(explanation: str | None) -> str:
    cleaned = (explanation or "").strip()
    if len(cleaned) > 1000:
        raise HTTPException(status_code=422, detail="La explicación no puede superar 1000 caracteres.")
    return cleaned


def _clean_correct_index(correct_index: int) -> int:
    if not isinstance(correct_index, int) or not 0 <= correct_index <= 3:
        raise HTTPException(status_code=422, detail="correct_index debe estar entre 0 y 3.")
    return correct_index


def create_teacher_question(
    db: Session,
    teacher: User,
    subtopic_id: int,
    *,
    prompt: str,
    options: list[str],
    correct_index: int,
    explanation: str | None,
) -> Question:
    """Crea una pregunta docente (approved, visible de inmediato)."""
    subtopic = assert_teacher_can_manage_subtopic(db, teacher, subtopic_id)

    cleaned_prompt = _clean_prompt(prompt)
    cleaned_options = _clean_options(options)
    cleaned_index = _clean_correct_index(correct_index)
    cleaned_explanation = _clean_explanation(explanation)

    duplicate = content_repo.find_duplicate_prompt(db, subtopic_id, normalize_prompt(cleaned_prompt))
    if duplicate is not None:
        raise HTTPException(
            status_code=409, detail="Ya existe una pregunta con ese enunciado en este subtema."
        )

    question = Question(
        subtopic_id=subtopic_id,
        prompt=cleaned_prompt,
        options=cleaned_options,
        correct_index=cleaned_index,
        explanation=cleaned_explanation,
        order=content_repo.next_question_order(db, subtopic_id),
        source=QuestionSource.TEACHER,
        status=QuestionStatus.APPROVED,
        created_by=teacher.id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def get_subtopic_bank(
    db: Session,
    teacher: User,
    subtopic_id: int,
    *,
    status: str | None = None,
    source: str | None = None,
) -> list[Question]:
    """Banco de preguntas de un subtema: TODAS las estados y orígenes."""
    assert_teacher_can_manage_subtopic(db, teacher, subtopic_id)
    if status is not None and status not in QuestionStatus.ALL:
        raise HTTPException(status_code=422, detail="Estado inválido.")
    if source is not None and source not in QuestionSource.ALL:
        raise HTTPException(status_code=422, detail="Origen inválido.")

    stmt = select(Question).where(Question.subtopic_id == subtopic_id)
    if status is not None:
        stmt = stmt.where(Question.status == status)
    if source is not None:
        stmt = stmt.where(Question.source == source)
    return list(db.scalars(stmt.order_by(Question.order)).all())


def get_topic_bank_summary(db: Session, teacher: User, topic_id: int) -> list[dict]:
    """Resumen por subtema de una unidad: conteos por estado y origen.

    Valida que el profesor tenga el topic habilitado en algún curso propio.
    """
    from app.models.content import Topic

    topic = content_repo.get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Unidad no encontrada.")

    assert_teacher_can_manage_topic(db, teacher, topic_id)

    counts = content_repo.count_questions_by_status_and_source(db, topic_id)
    summary = []
    for subtopic in sorted(topic.subtopics, key=lambda s: s.order):
        bucket = counts.get(subtopic.id, {})
        approved = bucket.get(QuestionStatus.APPROVED, 0)
        pending = bucket.get(QuestionStatus.PENDING, 0)
        rejected = bucket.get(QuestionStatus.REJECTED, 0)
        summary.append(
            {
                "subtopic_id": subtopic.id,
                "title": subtopic.name,
                "total": approved + pending + rejected,
                "approved": approved,
                "pending": pending,
                "rejected": rejected,
                "official": bucket.get(QuestionSource.OFFICIAL, 0),
                "teacher": bucket.get(QuestionSource.TEACHER, 0),
                "ai": bucket.get(QuestionSource.AI, 0),
            }
        )
    return summary


def update_question(
    db: Session,
    teacher: User,
    question_id: int,
    *,
    prompt: str | None = None,
    options: list[str] | None = None,
    correct_index: int | None = None,
    explanation: str | None = None,
) -> Question:
    """Edita una pregunta propia (oficiales y ajenas → 403).

    Editar una IA pendiente NO la aprueba: sigue pending.
    """
    question = content_repo.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")
    assert_teacher_can_manage_question(db, teacher, question)

    if prompt is not None:
        cleaned_prompt = _clean_prompt(prompt)
        duplicate = content_repo.find_duplicate_prompt(
            db,
            question.subtopic_id,
            normalize_prompt(cleaned_prompt),
            exclude_question_id=question.id,
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=409, detail="Ya existe una pregunta con ese enunciado en este subtema."
            )
        question.prompt = cleaned_prompt
    if options is not None:
        question.options = _clean_options(options)
    if correct_index is not None:
        question.correct_index = _clean_correct_index(correct_index)
    if explanation is not None:
        question.explanation = _clean_explanation(explanation)

    db.commit()
    db.refresh(question)
    return question


def delete_question(db: Session, teacher: User, question_id: int) -> dict:
    """Borra una pregunta propia.

    Si tiene intentos/respuestas de estudiantes asociadas (no hay FK hacia
    questions hoy, pero se verifica por consistencia futura) se archiva
    (status=rejected) en lugar de borrado duro. Oficiales/ajenas → 403.
    """
    question = content_repo.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")
    assert_teacher_can_manage_question(db, teacher, question)

    archived = _question_has_student_answers(db, question.id)
    if archived:
        question.status = QuestionStatus.REJECTED
        db.commit()
        return {"deleted": False, "archived": True, "detail": "La pregunta tiene respuestas de estudiantes; se archivó en lugar de borrarse."}
    db.delete(question)
    db.commit()
    return {"deleted": True, "archived": False}


def _question_has_student_answers(db: Session, question_id: int) -> bool:
    """True si hay respuestas de estudiantes (FK question_answers → questions)."""
    from app.repositories import quiz_answer_repository as quiz_answer_repo

    return quiz_answer_repo.question_has_answers(db, question_id)


def review_ai_question(
    db: Session, teacher: User, question_id: int, action: str
) -> Question:
    """Aprueba o rechaza una pregunta IA pendiente (solo el autor)."""
    question = content_repo.get_question(db, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada.")
    assert_teacher_can_manage_question(db, teacher, question)

    if question.source != QuestionSource.AI or question.status != QuestionStatus.PENDING:
        raise HTTPException(
            status_code=409, detail="Solo se pueden revisar preguntas de IA pendientes."
        )
    if action == "approve":
        question.status = QuestionStatus.APPROVED
    elif action == "reject":
        question.status = QuestionStatus.REJECTED
    else:
        raise HTTPException(status_code=422, detail="action debe ser 'approve' o 'reject'.")

    db.commit()
    db.refresh(question)
    return question
