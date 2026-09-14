"""Importación de contenido desde un documento Markdown (unidades, subtemas y preguntas).

Formato soportado (GitHub-flavored, el mismo que se documenta en la UI):

```markdown
# UNIDAD 1. Nombre de la unidad
Descripción breve de la unidad.

## Nombre del subtema
Contenido libre: párrafos, **negritas**, listas con "- " o "1.".

### Preguntas
1. **¿Pregunta de repaso?**
   - [ ] Opción incorrecta
   - [x] Opción correcta
   Explicación de la respuesta.
```

Las opciones se marcan con `[x]`, y la respuesta correcta se indica por
posición. Como alternativa (sin casillas) se acepta una línea
`Correcta: <texto exacto de la opción>`.

El importador es idempotente y no destructivo: actualiza por nombre de
unidad/subtema y por posición, crea lo que falte y nunca borra subtemas o
preguntas que el documento no mencione. Al terminar, reindexa el RAG de los
subtemas afectados y enlaza el contenido a todos los cursos.
"""
from __future__ import annotations

import re
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.content import Question, Subtopic, Topic
from app.models.progress import Progress
from app.models.course import Course


# ── Parser de Markdown ──────────────────────────────────────────────────────

def parse_document(markdown_text: str) -> list[dict[str, Any]]:
    """Convierte el documento Markdown en la estructura de OFFICIAL_CONTENT."""
    topics: list[dict[str, Any]] = []
    current_topic: dict[str, Any] | None = None
    current_subtopic: dict[str, Any] | None = None
    pending_description = False

    def flush_subtopic() -> None:
        nonlocal current_subtopic
        if current_subtopic is not None:
            _finalize_subtopic(current_subtopic)
            if current_subtopic["content"] or current_subtopic["questions"]:
                current_topic["subtopics"].append(current_subtopic)
        current_subtopic = None

    for line in markdown_text.splitlines():
        if re.match(r"^#\s[^#]", line):
            name = line.lstrip("#").strip()
            if not name:
                continue
            flush_subtopic()
            current_topic = {"name": name, "description": "", "subtopics": []}
            topics.append(current_topic)
            pending_description = True
        elif re.match(r"^##\s[^#]", line):
            name = line.lstrip("#").strip()
            if not name:
                continue
            if current_topic is None:
                current_topic = {"name": "Material importado", "description": "", "subtopics": []}
                topics.append(current_topic)
            flush_subtopic()
            current_subtopic = {"name": name, "content": "", "questions": [], "_all": []}
            pending_description = False
        elif (
            current_topic is not None
            and current_subtopic is None
            and pending_description
            and line.strip()
        ):
            current_topic["description"] = " ".join(
                filter(None, [current_topic["description"], line.strip()])
            )
        elif current_subtopic is not None:
            current_subtopic["_all"].append(line)

    flush_subtopic()
    return [topic for topic in topics if topic["name"]]


def _finalize_subtopic(subtopic: dict[str, Any]) -> None:
    """Divide el bloque crudo de un subtema en 'content' y 'questions'."""
    raw = subtopic.pop("_all", [])
    split_index = len(raw)
    for index, line in enumerate(raw):
        if re.match(r"^###\s*Preguntas\s*$", line.strip(), re.I):
            split_index = index
            break
    subtopic["content"] = "\n".join(raw[:split_index]).strip()
    subtopic["questions"] = _parse_questions(raw[split_index + 1 :])


def _parse_questions(body: list[str]) -> list[dict[str, Any]]:
    """Extrae preguntas numeradas con opciones en casillas (o 'Correcta:')."""
    blocks: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] | None = None
    for line in body:
        m = re.match(r"^\d+[.)]\s+(.*)$", line)
        if m:
            if current:
                blocks.append(current)
            current = {"prompt": [], "options": [], "expl": []}
            current["prompt"].append(m.group(1).strip())
            continue
        if current is None:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^[-*]\s+\[[ xX]\]", stripped):
            current["options"].append(stripped)
        elif current["options"]:
            current["expl"].append(stripped)
        else:
            current["prompt"].append(stripped)
    if current:
        blocks.append(current)

    questions: list[dict[str, Any]] = []
    for block in blocks:
        parsed = _parse_question_block(block)
        if parsed is not None:
            questions.append(parsed)
    return questions


def _parse_question_block(block: dict[str, list[str]]) -> dict[str, Any] | None:
    prompt = " ".join(part for part in block["prompt"] if part).strip()
    options: list[str] = []
    correct_index: int | None = None

    for raw_option in block["options"]:
        marker = re.match(r"^[-*]\s*\[([ xX])\]\s*(.*)$", raw_option)
        if marker:
            checked = marker.group(1).lower() == "x"
            options.append(marker.group(2).strip())
            if checked:
                correct_index = len(options) - 1
            continue
        # Opción sin casilla: se admite un indicador ✔ o se aclara con "Correcta:".
        plain = re.sub(r"^[-*]\s+", "", raw_option).strip()
        check = re.match(r"^[✔✓]\s*(.*)$", plain)
        if check:
            plain = check.group(1).strip()
            correct_index = len(options)
        options.append(plain)

    explanation = " ".join(part for part in block["expl"] if part).strip()

    # Fallback: línea tipo "Correcta: <texto exacto de la opción>".
    if correct_index is None:
        answer_line = re.search(
            r"^(?:respuesta|correcta|answer)\s*[:：]\s*(.+)$", explanation, re.I | re.M
        )
        if answer_line:
            answer_text = answer_line.group(1).strip().lower()
            explanation = re.sub(
                r"^(?:respuesta|correcta|answer)\s*[:：]\s*(.+)$",
                "",
                explanation,
                count=1,
                flags=re.I,
            ).strip()
            for index, option in enumerate(options):
                if option.strip().lower() == answer_text or option.strip().lower().startswith(answer_text):
                    correct_index = index
                    break

    if not options or prompt == "":
        return None

    explanation = re.sub(r"^explicaci[oó]n\s*[:：]\s*", "", explanation, flags=re.I).strip()

    return {
        "prompt": prompt,
        "options": options,
        "correct_index": correct_index if correct_index is not None else 0,
        "explanation": explanation,
    }


# ── Sincronización con la base de datos ─────────────────────────────────────

def sync_questions(
    db: Session,
    subtopic: Subtopic,
    desired: list[dict[str, Any]],
    *,
    prune: bool = True,
) -> tuple[int, int]:
    """Alinea las preguntas del subtema con `desired`, creando/actualizando por orden."""
    created = 0
    updated = 0
    current = sorted(subtopic.questions, key=lambda question: question.order)

    for order, question_data in enumerate(desired):
        if order < len(current):
            question = current[order]
            updated += 1
        else:
            question = Question(subtopic=subtopic)
            db.add(question)
            created += 1
        question.prompt = question_data["prompt"]
        question.options = question_data["options"]
        question.correct_index = question_data["correct_index"]
        question.explanation = question_data["explanation"]
        question.order = order

    if prune:
        for stale in current[len(desired) :]:
            db.delete(stale)
    return created, updated


def sync_topic(
    db: Session,
    topic_data: dict[str, Any],
    topic_order: int,
    *,
    prune: bool = True,
    match_by_order: bool = True,
) -> tuple[Topic, dict[str, int], list[int]]:
    """Crea o actualiza una unidad. Devuelve `(topic, counts, subtopic_ids)`."""
    counts = {"topics_created": 0, "subtopics_created": 0, "subtopics_updated": 0,
              "questions_created": 0, "questions_updated": 0}
    touched_subtopic_ids: list[int] = []

    topic = db.scalar(select(Topic).where(Topic.name == topic_data["name"]))
    if topic is None and match_by_order:
        topic = db.scalar(select(Topic).where(Topic.order == topic_order))
    if topic is None:
        topic = Topic(name=topic_data["name"], order=topic_order)
        db.add(topic)
        db.flush()
        counts["topics_created"] = 1

    topic.name = topic_data["name"]
    topic.description = topic_data["description"]
    if match_by_order:
        topic.order = topic_order

    current_subtopics = sorted(topic.subtopics, key=lambda subtopic: subtopic.order)
    desired_subtopics = topic_data["subtopics"]
    for subtopic_order, subtopic_data in enumerate(desired_subtopics):
        if subtopic_order < len(current_subtopics):
            subtopic = current_subtopics[subtopic_order]
            counts["subtopics_updated"] += 1
        else:
            subtopic = Subtopic(topic=topic)
            db.add(subtopic)
            counts["subtopics_created"] += 1
        subtopic.name = subtopic_data["name"]
        subtopic.content = subtopic_data["content"]
        subtopic.order = subtopic_order
        db.flush()
        q_created, q_updated = sync_questions(db, subtopic, subtopic_data.get("questions", []), prune=prune)
        counts["questions_created"] += q_created
        counts["questions_updated"] += q_updated
        touched_subtopic_ids.append(subtopic.id)

    if prune:
        stale_subtopics = current_subtopics[len(desired_subtopics) :]
        stale_ids = [subtopic.id for subtopic in stale_subtopics if subtopic.id is not None]
        if stale_ids:
            db.execute(delete(Progress).where(Progress.subtopic_id.in_(stale_ids)))
            for subtopic in stale_subtopics:
                db.delete(subtopic)

    return topic, counts, touched_subtopic_ids


# ── Orquestación ────────────────────────────────────────────────────────────

def _link_to_all_courses(db: Session) -> None:
    """Enlaza los temas (incluidos los nuevos) a todos los cursos existentes."""
    from app.repositories import content_repository as content_repo

    courses = list(db.scalars(select(Course).order_by(Course.id)).all())
    for course in courses:
        content_repo.link_all_topics_to_course(db, course.id)


def import_document(db: Session, markdown_text: str) -> dict[str, Any]:
    """Importa un documento Markdown: parsea, sincroniza, reindexa RAG y enlaza.

    Nunca borra contenido existente (prune=False). Devuelve un resumen con los
    conteos del resultado para mostrarlo en la UI.
    """
    from app.seed.index_content import index_subtopics

    topics = parse_document(markdown_text)
    if not topics:
        raise ValueError(
            "No se encontró ninguna unidad en el documento. "
            "Usá títulos `# Unidad N. Nombre` y `## Subtema`."
        )

    next_order = db.scalar(select(Topic.order).order_by(Topic.order.desc()).limit(1)) or 0

    totals = {
        "topics_created": 0,
        "subtopics_created": 0,
        "subtopics_updated": 0,
        "questions_created": 0,
        "questions_updated": 0,
    }
    touched_ids: list[int] = []
    subtopic_names: list[str] = []

    for topic_data in topics:
        if match_topics_by_name(db, topic_data["name"]):
            topic_order = db.scalar(select(Topic.order).where(Topic.name == topic_data["name"]))
        else:
            next_order += 1
            topic_order = next_order
        topic, counts, ids = sync_topic(
            db, topic_data, topic_order, prune=False, match_by_order=False
        )
        for key in totals:
            totals[key] += counts[key]
        touched_ids.extend(ids)
        if ids:
            names = [sub["name"] for sub in topic_data["subtopics"]]
            subtopic_names.extend(names)

    db.commit()

    chunks_indexed = index_subtopics(db, touched_ids)

    _link_to_all_courses(db)
    db.commit()

    return {
        "unidades": len(topics),
        "unidades_creadas": totals["topics_created"],
        "subtemas_creados": totals["subtopics_created"],
        "subtemas_actualizados": totals["subtopics_updated"],
        "preguntas_creadas": totals["questions_created"],
        "preguntas_actualizadas": totals["questions_updated"],
        "chunks_indexados": chunks_indexed,
        "subtemas": subtopic_names,
    }


def match_topics_by_name(db: Session, name: str) -> Topic | None:
    return db.scalar(select(Topic).where(Topic.name == name))