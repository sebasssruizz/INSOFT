"""Modo práctica: sesiones cortas de banco + IA reutilizable.

POST /api/practice/sessions — crea una sesión de práctica para el usuario.
"""
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request
from pydantic import BaseModel, Field
from slowapi import Limiter

from app.api.routes.ai import _get_user_id_from_auth_header
from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User
from app.services import practice_service

router = APIRouter(prefix="/practice", tags=["practice"])

# Limiter propio (key por user_id del JWT), separado de los de IA y quiz.
limiter = Limiter(key_func=_get_user_id_from_auth_header, default_limits=[])


class PracticeSessionRequest(BaseModel):
    """Solicitud de sesión de práctica.

    Debe venir exactamente uno de `subtopic_id` o `topic_id`.
    """

    subtopic_id: int | None = None
    topic_id: int | None = None
    count: int | None = Field(
        default=None,
        ge=1,
        le=settings.PRACTICE_MAX_COUNT,
        description="Cantidad de preguntas (default PRACTICE_DEFAULT_COUNT)",
    )


@router.post(
    "/sessions",
    summary="Crear una sesión de práctica (banco + IA reutilizable)",
    responses={
        200: {"description": "Sesión creada (puede venir solo de banco si la IA falla)"},
        401: {"description": "Sin token"},
        403: {"description": "Sin acceso al subtema/módulo"},
        404: {"description": "Sin preguntas disponibles para practicar"},
        422: {"description": "Payload inválido"},
        429: {"description": "Límite de sesiones por hora alcanzado"},
    },
)
@limiter.limit(lambda: settings.PRACTICE_RATE_LIMIT)
async def create_practice_session_endpoint(
    request: Request,
    payload: Annotated[PracticeSessionRequest, Body(...)],
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Sesión de práctica con `attempt_id` del servidor.

    El cliente no recibe `correct_index` ni `explanation`: la calificación
    ocurre en el servidor vía `POST /api/quiz/answers`.
    """
    return await practice_service.create_practice_session(
        db,
        current_user,
        subtopic_id=payload.subtopic_id,
        topic_id=payload.topic_id,
        count=payload.count,
    )
