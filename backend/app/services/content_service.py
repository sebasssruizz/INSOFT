"""Lógica de negocio del contenido académico oficial (solo lectura para usuarios).

El contenido es ÚNICO y centralizado: los cursos referencian los mismos temas
mediante CourseTopic, sin duplicar información médica.
"""
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories import content_repository as content_repo
from app.repositories import progress_repository as progress_repo
from app.services import course_service
from app.services.exceptions import NotFoundError
from app.services.study_time import estimate_minutes


def _serialize_question(question) -> dict:
    return {
        "id": question.id,
        "subtopic_id": question.subtopic_id,
        "prompt": question.prompt,
        "options": question.options,
        "correct_index": question.correct_index,
        "explanation": question.explanation,
        "order": question.order,
    }


def get_course_content(db: Session, user: User, course_id: int) -> list[dict]:
    """Temas y subtemas habilitados del curso, con el progreso del estudiante."""
    course_service.get_course_with_access_check(db, user, course_id)

    completed_ids = set()
    if user.role == UserRole.STUDENT:
        completed_ids = {
            p.subtopic_id
            for p in progress_repo.get_for_course(db, user.id, course_id)
            if p.completed
        }

    result = []
    for course_topic in content_repo.get_course_topics(db, course_id):
        topic = course_topic.topic
        subtopics = [
            {
                "id": sub.id,
                "topic_id": sub.topic_id,
                "name": sub.name,
                "order": sub.order,
                "completed": sub.id in completed_ids,
                "estimated_minutes": estimate_minutes(sub),
                "question_count": len(sub.questions),
            }
            for sub in sorted(topic.subtopics, key=lambda s: s.order)
        ]
        completed_count = sum(1 for s in subtopics if s["completed"])
        result.append(
            {
                "id": topic.id,
                "name": topic.name,
                "description": topic.description,
                "order": topic.order,
                "completed_subtopics": completed_count,
                "total_subtopics": len(subtopics),
                "estimated_minutes": sum(s["estimated_minutes"] for s in subtopics),
                "question_count": sum(s["question_count"] for s in subtopics),
                "subtopics": subtopics,
            }
        )
    return result


def get_subtopic_detail(db: Session, user: User, course_id: int, subtopic_id: int) -> dict:
    """Contenido completo de un subtema, validando acceso al curso."""
    course_service.get_course_with_access_check(db, user, course_id)

    allowed_ids = content_repo.get_subtopic_ids_for_course(db, course_id)
    subtopic = content_repo.get_subtopic(db, subtopic_id)
    if subtopic is None or subtopic.id not in allowed_ids:
        raise NotFoundError("Subtema no encontrado en este curso.")

    completed = False
    if user.role == UserRole.STUDENT:
        record = progress_repo.get_record(db, user.id, course_id, subtopic.id)
        completed = bool(record and record.completed)

    questions = sorted(subtopic.questions, key=lambda q: q.order)
    return {
        "id": subtopic.id,
        "topic_id": subtopic.topic_id,
        "name": subtopic.name,
        "content": subtopic.content,
        "order": subtopic.order,
        "completed": completed,
        "estimated_minutes": estimate_minutes(subtopic),
        "questions": [_serialize_question(question) for question in questions],
    }


def get_topic_questions(db: Session, user: User, course_id: int, topic_id: int) -> list[dict]:
    """Todas las preguntas de una unidad, para el repaso del módulo completo."""
    course_service.get_course_with_access_check(db, user, course_id)

    course_topic = next(
        (ct for ct in content_repo.get_course_topics(db, course_id) if ct.topic_id == topic_id),
        None,
    )
    if course_topic is None:
        raise NotFoundError("Unidad no encontrada en este curso.")

    questions = []
    for subtopic in sorted(course_topic.topic.subtopics, key=lambda s: s.order):
        questions.extend(sorted(subtopic.questions, key=lambda q: q.order))
    return [_serialize_question(question) for question in questions]
