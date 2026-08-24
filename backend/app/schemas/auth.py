from pydantic import BaseModel

from app.schemas.user import UserRead


class GoogleLoginRequest(BaseModel):
    """Credential (ID token) emitido por Google Identity Services en el frontend."""

    credential: str


class DevLoginRequest(BaseModel):
    """Login de desarrollo (solo si DEV_AUTH_ENABLED=true)."""

    email: str
    name: str = "Usuario de desarrollo"
    role: str = "STUDENT"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
