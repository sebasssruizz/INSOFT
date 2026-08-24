from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.database.session import get_db
from app.schemas.auth import DevLoginRequest, GoogleLoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
def login_with_google(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Recibe el ID token de Google, crea/busca el usuario y devuelve un JWT propio."""
    user = auth_service.authenticate_with_google(db, payload.credential)
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)


@router.post("/dev", response_model=TokenResponse)
def login_dev(payload: DevLoginRequest, db: Session = Depends(get_db)):
    """Login de desarrollo (sin Google). Solo si DEV_AUTH_ENABLED=true."""
    user = auth_service.authenticate_dev(db, payload.email, payload.name, payload.role)
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)
