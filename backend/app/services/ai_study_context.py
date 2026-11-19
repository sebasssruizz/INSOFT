"""Contexto académico disponible incluso antes de indexar el RAG."""
import re
import unicodedata
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import CourseTopic, Subtopic, Topic
from app.models.course import Course


def search_terms(text: str) -> set[str]:
    plain = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))
    return set(re.findall(r'\w{4,}', plain))


def available_subtopics(db: Session, course_ids: list[int], topic_id: int | None = None) -> list[Subtopic]:
    if not course_ids:
        return []
    statement = (select(Subtopic).join(CourseTopic, CourseTopic.topic_id == Subtopic.topic_id)
                 .join(Topic, Topic.id == Subtopic.topic_id)
                 .where(CourseTopic.course_id.in_(course_ids), CourseTopic.enabled.is_(True)))
    if topic_id is not None:
        statement = statement.where(Subtopic.topic_id == topic_id)
    return list(db.scalars(statement.order_by(Topic.order, Subtopic.order, Subtopic.id)).unique().all())


def unindexed_chunks(db: Session, course_ids: list[int], topic_id: int | None = None,
                     subtopic_id: int | None = None) -> list:
    from app.seed.index_content import chunk_subtopic_content

    subtopics = available_subtopics(db, course_ids, topic_id)
    if subtopic_id is not None:
        subtopics = [subtopic for subtopic in subtopics if subtopic.id == subtopic_id]
    return [SimpleNamespace(content=text, subtopic_id=subtopic.id)
            for subtopic in subtopics for text in chunk_subtopic_content(subtopic.content)]


def syllabus_sources(db: Session, course_ids: list[int], topic_id: int | None = None) -> list[dict]:
    """El temario es una fuente explícita, no una búsqueda semántica de párrafos."""
    result = []
    remaining = 12000
    for course in db.scalars(select(Course).where(Course.id.in_(course_ids)).order_by(Course.id)):
        topics = list(db.scalars(select(Topic).join(CourseTopic, CourseTopic.topic_id == Topic.id).where(
            CourseTopic.course_id == course.id, CourseTopic.enabled.is_(True),
            *([Topic.id == topic_id] if topic_id is not None else []),
        ).order_by(CourseTopic.order, Topic.order, Topic.id)))
        if not topics:
            continue
        lines = [f'Curso: {course.name}', f'Descripción: {course.description or "Sin descripción adicional"}',
                 'Temario habilitado (los títulos describen el alcance; no inventes objetivos adicionales):']
        for topic in topics:
            lines.append(f'- {topic.name}')
            lines.append('  Subtemas: ' + '; '.join(subtopic.name for subtopic in topic.subtopics))
        content = '\n'.join(lines)
        if len(content) > remaining:
            content = content[:remaining] + '\n[Temario parcial por límite de contexto.]'
        remaining -= len(content)
        result.append({'content': content, 'course_id': course.id, 'topic_id': topic_id,
                       'subtopic_id': None, 'title': f'Temario: {course.name}', 'kind': 'syllabus'})
        if remaining <= 0:
            break
    return result
