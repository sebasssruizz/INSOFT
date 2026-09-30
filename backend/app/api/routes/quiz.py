"""Respuestas de quiz calificadas en servidor y estadísticas (solo profesores).

POST /api/quiz/answers — respuesta del estudiante (califica el backend).
GET  /api/quiz/stats/overview|questions|students|subtopics — stats del profesor.
GET  /api/quiz/stats/export.csv — descarga CSV (escape de fórmulas Excel).
"""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories import quiz_answer_repository as quiz_answer_repo
from app.services import quiz_service
from app.api.routes.ai import _get_user_id_from_auth_header

router = APIRouter(prefix="/quiz", tags=["quiz"])

# Limiter propio (key por user_id del JWT): separado del de IA para no
# interferir con sus contadores.
limiter = Limiter(key_func=_get_user_id_from_auth_header, default_limits=[])


class QuizAnswerRequest(BaseModel):
    """Respuesta del estudiante a una pregunta dentro de un intento."""

    question_id: int = Field(..., description="Pregunta respondida")
    selected_index: int = Field(..., ge=0, le=3, description="Opción elegida (0-3)")
    attempt_id: str = Field(..., description="UUID del intento (compartido por todo el quiz)")


class QuizAnswerResponse(BaseModel):
    """Resultado calificado en el servidor (solo se revela tras responder)."""

    is_correct: bool
    correct_index: int
    explanation: str


def _parse_date(value: str | None, name: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Formato de fecha inválido para {name}; usa ISO (YYYY-MM-DD)."
        )


def _require_teacher(current_user: User) -> None:
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=403, detail="Solo profesores pueden ver estadísticas."
        )


@router.post(
    "/answers",
    response_model=QuizAnswerResponse,
    summary="Registrar y calificar una respuesta del quiz (estudiante)",
    responses={
        200: {"description": "Respuesta calificada (o ya existente: idempotente)"},
        401: {"description": "Sin token"},
        403: {"description": "Sin acceso al subtema de la pregunta"},
        404: {"description": "Pregunta no encontrada o no aprobada"},
        422: {"description": "Payload inválido"},
        429: {"description": "Límite de respuestas alcanzado"},
    },
)
@limiter.limit(settings.QUIZ_ANSWER_RATE_LIMIT)
def submit_answer_endpoint(
    request: Request,
    payload: QuizAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Califica en el servidor: el cliente no conoce la correcta antes de enviar."""
    try:
        return quiz_service.submit_answer(
            db,
            current_user,
            payload.question_id,
            payload.selected_index,
            payload.attempt_id,
        )
    except HTTPException:
        raise


# ── Estadísticas de quiz (solo profesores) ─────────────────────────────────


@router.get("/stats/overview", response_model=dict, tags=["quiz"])
def quiz_stats_overview_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Intentos, respuestas totales, % acierto global y estudiantes activos."""
    _require_teacher(current_user)
    from_dt = _parse_date(from_date, "from_date")
    to_dt = _parse_date(to_date, "to_date")
    if course_id is not None:
        from app.services.exceptions import NotFoundError
        from app.services import course_service

        try:
            course_service.get_course_with_access_check(db, current_user, course_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=exc.detail)
    return quiz_answer_repo.get_stats_overview(
        db,
        current_user.id,
        course_id=course_id,
        subtopic_id=subtopic_id,
        from_date=from_dt,
        to_date=to_dt,
    )


@router.get("/stats/questions", response_model=dict, tags=["quiz"])
def quiz_stats_questions_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Por pregunta: respuestas, % acierto y opción incorrecta más elegida."""
    _require_teacher(current_user)
    if course_id is not None:
        from app.services import course_service

        course_service.get_course_with_access_check(db, current_user, course_id)
    rows, total = quiz_answer_repo.get_stats_questions(
        db,
        current_user.id,
        course_id=course_id,
        subtopic_id=subtopic_id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
        limit=limit,
        offset=offset,
    )
    return {"questions": rows, "total": total}


@router.get("/stats/students", response_model=dict, tags=["quiz"])
def quiz_stats_students_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """Por estudiante: respuestas, % acierto y última actividad."""
    _require_teacher(current_user)
    if course_id is not None:
        from app.services import course_service

        course_service.get_course_with_access_check(db, current_user, course_id)
    rows, total = quiz_answer_repo.get_stats_students(
        db,
        current_user.id,
        course_id=course_id,
        subtopic_id=subtopic_id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
        limit=limit,
        offset=offset,
    )
    return {"students": rows, "total": total}


@router.get("/stats/subtopics", response_model=list[dict], tags=["quiz"])
def quiz_stats_subtopics_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """% acierto por subtema (solo estudiantes de sus cursos)."""
    _require_teacher(current_user)
    if course_id is not None:
        from app.services import course_service

        course_service.get_course_with_access_check(db, current_user, course_id)
    return quiz_answer_repo.get_stats_subtopics(
        db,
        current_user.id,
        course_id=course_id,
        subtopic_id=subtopic_id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
    )


# ── Exportación CSV ────────────────────────────────────────────────────────


def _escape_csv_cell(value) -> str:
    """Evita inyección de fórmulas en Excel: prefija ' a = + - @ iniciales."""
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _csv_response(rows, headers: list[str]):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_escape_csv_cell(cell) for cell in row])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="estadisticas.csv"'},
    )


@router.get("/stats/export.csv", tags=["quiz"])
def quiz_stats_export_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    course_id: int | None = None,
    subtopic_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """CSV descargable con todas las respuestas de estudiantes de sus cursos."""
    _require_teacher(current_user)
    if course_id is not None:
        from app.services import course_service

        course_service.get_course_with_access_check(db, current_user, course_id)
    rows = quiz_answer_repo.iter_answers_for_export(
        db,
        current_user.id,
        course_id=course_id,
        subtopic_id=subtopic_id,
        from_date=_parse_date(from_date, "from_date"),
        to_date=_parse_date(to_date, "to_date"),
    )
    headers = [
        "fecha",
        "estudiante",
        "email",
        "pregunta_id",
        "pregunta",
        "subtopic_id",
        "opcion_elegida",
        "correcta",
        "intento",
    ]
    return _csv_response(rows, headers)
