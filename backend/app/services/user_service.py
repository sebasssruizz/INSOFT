"""Lógica de negocio del perfil de usuario."""
from sqlalchemy.orm import Session

from app.models.user import User


def update_profile(
    db: Session,
    user: User,
    *,
    country: str,
    age: int,
    phone: str | None,
    university: str,
) -> User:
    user.country = country.strip()
    user.age = age
    user.phone = phone.strip() if phone else None
    user.university = university.strip()
    db.commit()
    db.refresh(user)
    return user
