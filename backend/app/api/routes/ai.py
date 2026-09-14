"""Endpoint de IA: pregunta al asistente con RAG (OpenRouter).

POST /api/ai/ask — pregunta del estudiante, opcionalmente filtrada por subtema.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_user
from app.auth.jwt import decode_access_token
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.ai import AskRequest, AskResponse
from app.services.ai_service import ask_ai
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
    """
    try:
        result = await ask_ai(
            question=payload.question,
            user_id=current_user.id,
            subtopic_id=payload.subtopic_id,
            db=db,
            current_user=current_user,
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