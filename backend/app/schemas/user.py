from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    profile_image: str | None = None
    role: UserRole
    country: str | None = None
    age: int | None = None
    phone: str | None = None
    university: str | None = None
    profile_completed: bool = False
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Datos de perfil complementarios del propio usuario."""

    country: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=10, le=110)
    phone: str | None = Field(default=None, max_length=30)
    university: str = Field(min_length=2, max_length=255)


class RoleUpdate(BaseModel):
    """Cambio de rol del propio usuario (autogestión)."""

    role: UserRole


class StudentRead(BaseModel):
    """Información básica de un estudiante visible para su profesor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    profile_image: str | None = None
    joined_at: datetime
