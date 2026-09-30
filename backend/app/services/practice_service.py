"""Modo práctica: sesiones cortas de banco + IA reutilizable.

Composición: primero del banco aprobado (docente > oficial, excluyendo lo
respondido bien en los últimos 14 días y priorizando lo fallado), luego
preguntas `practice` ya existentes que el usuario no haya respondido, y solo
si el pool no alcanza se genera con el LLM reutilizando el pipeline de
generación (máx. 1 llamada por subtema, 2 por sesión, con tope diario por
subtema). Los fallos del proveedor degradan a solo-banco sin error.
"""
import math
import random
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Question, Subtopic
from app.models.question_meta import QuestionSource, QuestionStatus
from app.repositories import content_repository as content_repo
from app.repositories import practice_repository as practice_repo
from app.services.ai_service import (
    GeminiCallError,
    NoChunksError,
    OpenRouterCallError,
    OpenRouterSaturatedError,
    _ensure_subtopic_access,
    generate_questions_for_subtopic,
)

BANK_SOURCES_PRIORITY = (QuestionSource.TEACHER, QuestionSource.OFFICIAL, QuestionSource.AI)


def _target_subtopics(
    db: Session, user, subtopic_id: int | None, topic_id: int | None
) -> list[Subtopic]:
    """Subtemas objetivo validando acceso (misma regla que /ask).

    Los errores de autorización (`NotFoundError`/`ForbiddenError`) se propagan:
    el handler global de `ServiceError` los traduce a 404/403.
    """
    from app.services.exceptions import ForbiddenError, NotFoundError

    if subtopic_id is not None:
        subtopic = _ensure_subtopic_access(db, user, subtopic_id)
        return [subtopic]

    from app.models.content import Topic

    topic = db.get(Topic, topic_id)
    if topic is None:
        raise NotFoundError("Módulo no encontrado.")

    # Subtemas ordenados; se conservan los accesibles. Si el usuario no accede
    # a ninguno → 403 (el módulo existe pero no es suyo).
    candidates = sorted(topic.subtopics, key=lambda s: s.order)
    accessible: list[Subtopic] = []
    for candidate in candidates:
        try:
            _ensure_subtopic_access(db, user, candidate.id)
            accessible.append(candidate)
        except (NotFoundError, ForbiddenError):
            continue
    if candidates and not accessible:
        raise ForbiddenError("No tienes acceso a los subtemas de este módulo.")
    if not candidates:
        raise NotFoundError("El módulo no tiene subtemas con contenido.")
    return accessible


def _subtopics_with_chunks(db: Session, subtopics: list[Subtopic]) -> list[Subtopic]:
    """Subtemas que tienen preguntas (banco o practice) o contenido indexado."""
    if not subtopics:
        return []
    from app.repositories import subtopic_chunk_repository as chunk_repo

    result = []
    for subtopic in subtopics:
        has_chunks = bool(chunk_repo.list_chunks_for_subtopic(db, subtopic.id))
        has_questions = bool(
            db.scalar(
                select(Question.id)
                .where(Question.subtopic_id == subtopic.id)
                .limit(1)
            )
        )
        if has_chunks or has_questions:
            result.append(subtopic)
    return result


def _bank_pool(db: Session, subtopic_ids: list[int]) -> list[Question]:
    """Preguntas approved de los subtemas objetivo, docente > oficial > IA."""
    if not subtopic_ids:
        return []
    questions = list(
        db.scalars(
            select(Question).where(
                Question.subtopic_id.in_(subtopic_ids),
                Question.status == QuestionStatus.APPROVED,
            )
        ).all()
    )
    priority = {source: index for index, source in enumerate(BANK_SOURCES_PRIORITY)}
    questions.sort(
        key=lambda q: (
            q.subtopic_id,
            priority.get(q.source, len(BANK_SOURCES_PRIORITY)),
            q.order,
        )
    )
    return questions


def _order_bank(
    questions: list[Question], recent: dict[int, bool]
) -> tuple[list[Question], list[Question]]:
    """Particiona el pool: primero lo fallado, luego lo no respondido; excluye lo acertado."""
    failed, fresh = [], []
    for question in questions:
        result = recent.get(question.id)
        if result is True:
            continue  # respondido bien recientemente: fuera
        (failed if result is False else fresh).append(question)
    return failed, fresh


async def create_practice_session(
    db: Session,
    user,
    *,
    subtopic_id: int | None = None,
    topic_id: int | None = None,
    count: int | None = None,
) -> dict:
    """Arma la sesión de práctica; devuelve el payload del endpoint."""
    if (subtopic_id is None) == (topic_id is None):
        raise HTTPException(
            status_code=422,
            detail="Debe indicar exactamente uno de subtopic_id o topic_id.",
        )

    target = min(
        count if count is not None else settings.PRACTICE_DEFAULT_COUNT,
        settings.PRACTICE_MAX_COUNT,
    )
    if target < 1:
        raise HTTPException(status_code=422, detail="count debe ser al menos 1.")

    subtopics = _target_subtopics(db, user, subtopic_id, topic_id)
    subtopics = _subtopics_with_chunks(db, subtopics)
    subtopic_ids = [s.id for s in subtopics]

    popularity = practice_repo.popularity_by_subtopic(db, user, subtopic_ids)
    ordered_ids = sorted(subtopic_ids, key=lambda sid: popularity.get(sid, 0.0), reverse=True)

    bank_target = math.ceil(target * (1 - settings.PRACTICE_AI_RATIO))
    ai_target = target - bank_target

    # ── 1. Banco: docente > oficial; excluye acertadas, prioriza falladas ──
    bank_pool = _bank_pool(db, ordered_ids)
    recent = practice_repo.recent_results_by_question(db, user.id, [q.id for q in bank_pool])
    failed, fresh = _order_bank(bank_pool, recent)

    # Reparto por subtemas (popularidad) intercalando falladas y frescas.
    bank_selected: list[Question] = []
    if bank_target > 0:
        per_subtopic = _fair_share(ordered_ids, bank_target)
        for sid in ordered_ids:
            want = per_subtopic.get(sid, 0)
            if want <= 0:
                continue
            sid_failed = [q for q in failed if q.subtopic_id == sid]
            sid_fresh = [q for q in fresh if q.subtopic_id == sid]
            picked = (sid_failed + sid_fresh)[:want]
            bank_selected.extend(picked)
        # Si el reparto parejo no alcanzó por subtema, rellena con lo restante.
        if len(bank_selected) < bank_target:
            used = set(q.id for q in bank_selected)
            remaining = [q for q in (failed + fresh) if q.id not in used]
            bank_selected.extend(remaining[: bank_target - len(bank_selected)])

    bank_selected = bank_selected[:bank_target]

    # ── 2. IA: reutiliza practice no respondidas; genera solo si falta ──
    ai_selected: list[Question] = []
    ai_available = True
    llm_calls = 0

    if ai_target > 0:
        already_answered = practice_repo.answered_question_ids(
            db, user.id, _practice_ids(db, ordered_ids)
        )
        pool = practice_repo.practice_pool(db, ordered_ids, list(already_answered))
        ai_selected = pool[:ai_target]

        missing = ai_target - len(ai_selected)
        if missing > 0:
            generated_today = practice_repo.practice_generated_today_by_subtopic(
                db, ordered_ids
            )
            daily_cap = settings.PRACTICE_MAX_GENERATIONS_PER_SUBTOPIC_PER_DAY
            for sid in ordered_ids:
                if missing <= 0 or llm_calls >= 2:
                    break
                if generated_today.get(sid, 0) >= daily_cap:
                    continue
                want = min(missing, 5)
                try:
                    result = await generate_questions_for_subtopic(
                        db,
                        user,
                        sid,
                        want,
                        status=QuestionStatus.PRACTICE,
                        created_by=None,
                    )
                    llm_calls += 1
                    fresh_generated = [
                        q for q in result["questions"] if q.id not in already_answered
                    ]
                    ai_selected.extend(fresh_generated[:missing])
                    missing = ai_target - len(ai_selected)
                except (
                    GeminiCallError,
                    OpenRouterSaturatedError,
                    OpenRouterCallError,
                    NoChunksError,
                ):
                    # Fallos del LLM no deben romper la sesión: degrada a banco.
                    llm_calls += 1
                    ai_available = False
                    continue

    questions = list(bank_selected) + list(ai_selected)
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="Aún no hay preguntas disponibles para practicar este tema.",
        )

    random.shuffle(questions)

    return {
        "attempt_id": str(uuid4()),
        "mode": "practice",
        "questions": [
            {
                "id": q.id,
                "subtopic_id": q.subtopic_id,
                "prompt": q.prompt,
                "options": q.options,
                "order": q.order,
                "is_ai_generated": q.source == QuestionSource.AI,
            }
            for q in questions
        ],
        "composition": {"bank": len(bank_selected), "ai": len(ai_selected)},
        "ai_available": ai_available,
    }


def _practice_ids(db: Session, subtopic_ids: list[int]) -> list[int]:
    if not subtopic_ids:
        return []
    return list(
        db.scalars(
            select(Question.id).where(
                Question.subtopic_id.in_(subtopic_ids),
                Question.status == QuestionStatus.PRACTICE,
            )
        ).all()
    )


def _fair_share(ordered_ids: list[int], total: int) -> dict[int, int]:
    """Reparte `total` entre los subtemas según orden de popularidad."""
    if not ordered_ids or total <= 0:
        return {}
    shares = {sid: total // len(ordered_ids) for sid in ordered_ids}
    remainder = total - sum(shares.values())
    for sid in ordered_ids[:remainder]:
        shares[sid] += 1
    return shares
