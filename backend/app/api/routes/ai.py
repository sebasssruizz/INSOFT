"""Endpoint de IA: pregunta al asistente con RAG (OpenRouter).

Orquesta: normalización de pregunta → búsqueda de chunks por similitud →
respuesta final con contexto → guardado en historial (ai_queries).

POST /api/ai/ask — pregunta del estudiante, opcionalmente filtrada por subtema.
GET /api/ai/history — historial propio del estudiante autenticado.
GET /api/ai/history/all — historial completo (solo profesor, sus cursos).
GET /api/ai/stats/overview|students|subtopics — estadísticas (solo profesor).
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_user, require_teacher
from app.auth.jwt import decode_access_token
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories import ai_query_repository as ai_query_repo
from app.repositories import content_repository as content_repo
from app.schemas.ai import AskRequest, AskResponse, GenerateQuestionsRequest, GenerateQuestionsResponse
from app.services import ai_service, question_service
from app.services.ai_service import (
    ConcurrencyExceeded,
    DailyLimitError,
    GeminiCallError,
    ask_ai,
)
from app.services.content_service import serialize_question_for_teacher
from app.services.exceptions import ForbiddenError, NotFoundError
from app.core.openrouter_client import (
    OpenRouterCallError,
    OpenRouterQuotaError,
    OpenRouterSaturatedError,
)

router = APIRouter(prefix="/ai", tags=["ai"])


def _get_user_id_from_auth_header(request: Request) -> str:
    """Extrae el user_id del JWT en el header Authorization (para slowapi key_func).

    Si el token es inválido o no hay header, usa la IP como fallback (aunque
    slowapi bloqueará antes de llegar aquí si no hay usuario autenticado).
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return get_remote_address(request)

    token = auth.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return f"user:{user_id}"
    except Exception:
        pass
    return get_remote_address(request)


# Limiter con key_func que usa el user_id del JWT (no la IP)
limiter = Limiter(key_func=_get_user_id_from_auth_header, default_limits=[])


@router.post("/ask", response_model=AskResponse)
@limiter.limit(lambda: settings.AI_ASK_RATE_LIMIT)
async def ask_ai_endpoint(
    request: Request,
    payload: Annotated[AskRequest, Body(...)],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pregunta al asistente de IA con RAG sobre el contenido oficial.

    - `question`: pregunta del estudiante (máx. 500 caracteres).
    - `subtopic_id`: opcional. Si se pasa, valida que el usuario tenga acceso
      a ese subtema (inscripción o profesor dueño del curso); si no tiene acceso
      → 403; si no existe → 404. Si no se pasa, busca en todo el contenido.
    - `course_id`: opcional. Acota la búsqueda RAG a los topics habilitados en
      ese curso y valida la membresía del usuario; si el usuario no pertenece
      al curso → 403. Sin `course_id` se conserva la búsqueda global (fallback).
    """
    try:
        result = await ask_ai(
            question=payload.question,
            user_id=current_user.id,
            subtopic_id=payload.subtopic_id,
            db=db,
            current_user=current_user,
            course_id=payload.course_id,
            session_id=payload.session_id,
        )
        return AskResponse(**result)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=exc.detail)
    except OpenRouterSaturatedError as exc:
        # 429 estable + Retry-After: la frontend muestra reintento en 60 s.
        raise HTTPException(
            status_code=429, detail=str(exc), headers={"Retry-After": "60"}
        )
    except DailyLimitError as exc:
        raise HTTPException(
            status_code=429, detail=str(exc), headers={"Retry-After": "3600"}
        )
    except (OpenRouterQuotaError, OpenRouterCallError, GeminiCallError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"[asistente-no-disponible] {exc}",
            headers={"Retry-After": "60"},
        )
    except ConcurrencyExceeded as exc:
        raise HTTPException(
            status_code=503,
            detail=f"[asistente-saturado] {exc}",
            headers={"Retry-After": "10"},
        )

# ── Generación de preguntas con IA (solo profesores) ───────────────────────


def _validate_generate_payload(payload) -> None:
    """Debe venir exactamente uno de subtopic_id o topic_id (422)."""
    if (payload.subtopic_id is None) == (payload.topic_id is None):
        raise HTTPException(
            status_code=422,
            detail="Debe indicar exactamente uno de subtopic_id o topic_id.",
        )


@router.post(
    "/questions/generate",
    response_model=GenerateQuestionsResponse,
    status_code=201,
    tags=["ai"],
    summary="Generación de preguntas con IA a partir del contenido oficial (profesor)",
    responses={
        201: {"description": "Preguntas generadas (quedan pending)"},
        401: {"description": "Sin token"},
        403: {"description": "No es profesor o sin acceso al subtema/unidad"},
        404: {"description": "Subtema/unidad no encontrada"},
        422: {"description": "Payload inválido o subtema sin contenido indexado"},
        429: {"description": "Límite de generación alcanzado o cuota del proveedor"},
        502: {"description": "La IA no devolvió preguntas válidas"},
        503: {"description": "Proveedor de IA no disponible"},
    },
)
@limiter.limit(lambda: settings.AI_QUESTION_RATE_LIMIT)
async def generate_questions_endpoint(
    request: Request,
    payload: GenerateQuestionsRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Genera preguntas IA (source=ai, status=pending) sobre el contenido oficial.

    Las preguntas nacen pendientes: no se muestran a estudiantes hasta que el
    profesor las apruebe desde el banco de preguntas.
    """
    _validate_generate_payload(payload)
    try:
        if payload.subtopic_id is not None:
            question_service.assert_teacher_can_manage_subtopic(
                db, current_user, payload.subtopic_id
            )
            result = await ai_service.generate_questions_for_subtopic(
                db, current_user, payload.subtopic_id, payload.count
            )
        else:
            topic = content_repo.get_topic(db, payload.topic_id)
            if topic is None:
                raise NotFoundError("Unidad no encontrada.")
            question_service.assert_teacher_can_manage_topic(
                db, current_user, payload.topic_id
            )
            result = await ai_service.generate_questions_for_topic(
                db, current_user, topic, payload.count
            )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=exc.detail)
    except ai_service.NoChunksError as exc:
        raise HTTPException(status_code=422, detail=exc.detail)
    except OpenRouterSaturatedError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except OpenRouterCallError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except GeminiCallError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    generated = [
        serialize_question_for_teacher(q, current_user.id)
        for q in result["questions"]
    ]
    warning = None
    if result["created"] < result["requested"]:
        warning = (
            f"Se generaron {result['created']} de {result['requested']} preguntas "
            "solicitadas; descarta las inválidas o intenta de nuevo."
        )
    return GenerateQuestionsResponse(
        generated=generated,
        requested=result["requested"],
        created=result["created"],
        warning=warning,
    )


# ── Historial de consultas ─────────────────────────────────────────────────


def _parse_date(value: str | None, name: str) -> datetime | None:
    """Convierte una fecha ISO (YYYY-MM-DD) en datetime; 400 si es inválida."""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Formato de fecha inválido para {name}; usa ISO (YYYY-MM-DD)."
        )


def _serialize_ai_query(q) -> dict:
    return {
        "id": q.id,
        "question": q.question_original,
        "answer": q.respuesta,
        "subtopic_id": q.subtopic_id,
        "session_id": str(q.session_id) if q.session_id else None,
        "model_used": q.model_used,
        "response_time_ms": q.response_time_ms,
        "created_at": q.created_at.isoformat(),
    }


@router.get("/history", response_model=list[dict], tags=["ai"])
def history_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subtopic_id: int | None = None,
    session_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Historial de consultas del estudiante autenticado (solo lo suyo)."""
    queries, _ = ai_query_repo.get_by_user(
        db,
        current_user.id,
        subtopic_id=subtopic_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return [_serialize_ai_query(q) for q in queries]


@router.get("/history/all", response_model=list[dict], tags=["ai"])
def history_all_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subtopic_id: int | None = None,
    session_id: str | None = None,
    user_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Historial de consultas (solo profesor; estudiantes de sus cursos).

    - `from_date`/`to_date`: rango ISO (YYYY-MM-DD); si no hay `from_date`, se
      acota a los últimos 30 días.
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403, detail="Solo profesores pueden ver el historial completo."
        )
    from_date_dt = _parse_date(from_date, "from_date")
    to_date_dt = _parse_date(to_date, "to_date")
    if from_date_dt is None:
        from_date_dt = datetime.now(timezone.utc) - timedelta(days=30)

    queries, _ = ai_query_repo.get_all_filtered(
        db,
        teacher_id=current_user.id,
        subtopic_id=subtopic_id,
        session_id=session_id,
        user_id=user_id,
        from_date=from_date_dt,
        to_date=to_date_dt,
        limit=limit,
        offset=offset,
    )
    return [_serialize_ai_query(q) for q in queries]


# ── Estadísticas de uso de IA (solo profesores) ────────────────────────────


def _require_teacher_role(current_user: User) -> None:
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403, detail="Solo profesores pueden ver estadísticas."
        )


@router.get("/stats/overview", response_model=dict, tags=["ai"])
def stats_overview_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Estadísticas generales de IA: total, tiempo promedio, conteo por subtema."""
    _require_teacher_role(current_user)
    return ai_query_repo.get_stats_overview(
        db,
        current_user.id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
    )


@router.get("/stats/students", response_model=dict, tags=["ai"])
def stats_students_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Preguntas por estudiante y último uso (solo estudiantes de sus cursos)."""
    _require_teacher_role(current_user)
    students, total = ai_query_repo.get_stats_students(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
    )
    return {"students": students, "total": total}


@router.get("/stats/subtopics", response_model=dict, tags=["ai"])
def stats_subtopics_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Conteo por subtema y preguntas más frecuentes (solo estudiantes de sus cursos)."""
    _require_teacher_role(current_user)
    subtopics, total = ai_query_repo.get_stats_subtopics(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
    )
    return {"subtopics": subtopics, "total": total}


# ── Exportación CSV de estadísticas de IA ──────────────────────────────────


def _escape_csv_cell(value) -> str:
    """Evita inyección de fórmulas en Excel: prefija ' a = + - @ iniciales."""
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _csv_response(rows, headers: list[str]):
    import csv
    import io

    from fastapi.responses import StreamingResponse

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_escape_csv_cell(cell) for cell in row])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="estadisticas_ia.csv"'},
    )


@router.get("/stats/export.csv", tags=["ai"])
def ai_stats_export_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """CSV descargable con las consultas de IA de estudiantes de sus cursos."""
    _require_teacher_role(current_user)
    queries, _ = ai_query_repo.get_all_filtered(
        db,
        teacher_id=current_user.id,
        subtopic_id=subtopic_id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
        limit=10000,
    )
    headers = [
        "fecha",
        "pregunta",
        "respuesta",
        "subtopic_id",
        "session_id",
        "modelo",
        "tiempo_respuesta_ms",
    ]
    rows = (
        [
            q.created_at.isoformat(),
            q.question_original,
            q.respuesta,
            q.subtopic_id,
            str(q.session_id) if q.session_id else None,
            q.model_used,
            q.response_time_ms,
        ]
        for q in queries
    )
    return _csv_response(rows, headers)
