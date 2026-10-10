"""Rutas de autenticación: Google (producción) y dev (sólo si está habilitado).

Ambos endpoints son públicos (por definición, son el acceso al sistema) y por
eso llevan rate limit por IP: son la superficie pública ataqueable principal.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.jwt import create_access_token
from app.core.config import settings
from app.database.session import get_db
from app.schemas.auth import DevLoginRequest, GoogleLoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# Limitador por IP independiente del de IA: el login es un endpoint público y
# no debe compartir presupuesto de límites con las consultas del asistente.
# LOGIN_RATE_LIMIT (default 60/hora por IP) cubre el uso legítimo: cada
# estudiante inicia sesión 1-2 veces; los reintentos a rachas (credential
# stuffing) quedan frenados sin tocar a estudiantes legítimos en sesión.
limiter = Limiter(key_func=get_remote_address)


@router.post("/google", response_model=TokenResponse)
@limiter.limit(lambda: settings.AUTH_RATE_LIMIT)
def login_with_google(request: Request, payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Recibe el ID token de Google, crea/busca el usuario y devuelve un JWT propio."""
    user = auth_service.authenticate_with_google(db, payload.credential)
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)


@router.post("/dev", response_model=TokenResponse)
@limiter.limit(lambda: settings.AUTH_RATE_LIMIT)
def login_dev(request: Request, payload: DevLoginRequest, db: Session = Depends(get_db)):
    """Login de desarrollo (sin Google). Solo si DEV_AUTH_ENABLED=true."""
    user = auth_service.authenticate_dev(db, payload.email, payload.name, payload.role)
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)
