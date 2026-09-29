"""Endpoint de IA: pregunta al asistente con RAG (OpenRouter).

POST /api/ai/ask — pregunta del estudiante, opcionalmente filtrada por subtema.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_user, require_teacher
from app.auth.jwt import decode_access_token
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.repositories import content_repository as content_repo
from app.schemas.ai import AskRequest, AskResponse, GenerateQuestionsRequest, GenerateQuestionsResponse
from app.services import ai_service, question_service
from app.services.ai_service import GeminiCallError, ask_ai
from app.services.content_service import serialize_question_for_teacher
from app.services.exceptions import ForbiddenError, NotFoundError
from app.core.openrouter_client import OpenRouterCallError, OpenRouterSaturatedError

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
@limiter.limit(settings.AI_ASK_RATE_LIMIT)
async def ask_ai_endpoint(
    request: Request,
    payload: AskRequest,
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
        )
        return AskResponse(**result)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.detail)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=exc.detail)
    except OpenRouterSaturatedError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except OpenRouterCallError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except GeminiCallError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

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
@limiter.limit(settings.AI_QUESTION_RATE_LIMIT)
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
