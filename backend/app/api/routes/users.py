from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import ProfileUpdate, RoleUpdate, UserRead
from app.services import auth_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me/role", response_model=UserRead)
def change_my_role(
    payload: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cambio de rol propio: SOLO con DEV_AUTH_ENABLED (desarrollo).

    En producción el rol se adjudica al CREAR la cuenta (TEACHER_EMAILS) o con
    el script backend/app/scripts/promote_teacher.py por parte del equipo: un
    cliente NO puede promoverse a sí mismo (evita autogestión a docente y
    acceso al panel docente).
    """
    if not settings.DEV_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El cambio de rol propio está deshabilitado. Los roles se "
                "asignan al crear la cuenta (TEACHER_EMAILS) o por el equipo "
                "del curso."
            ),
        )
    return auth_service.change_own_role(db, current_user, payload.role)


@router.patch("/me/profile", response_model=UserRead)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Completa/actualiza los datos de perfil del propio usuario."""
    return user_service.update_profile(
        db,
        current_user,
        country=payload.country,
        age=payload.age,
    )
