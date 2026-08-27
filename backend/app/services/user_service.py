"""Lógica de negocio del perfil de usuario."""
from sqlalchemy.orm import Session

from app.models.user import User


def update_profile(
    db: Session,
    user: User,
    *,
    country: str,
    age: int,
) -> User:
    user.country = country.strip()
    user.age = age
    db.commit()
    db.refresh(user)
    return user
