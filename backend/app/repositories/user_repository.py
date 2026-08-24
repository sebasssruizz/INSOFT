from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


def get_by_google_id(db: Session, google_id: str) -> User | None:
    return db.scalar(select(User).where(User.google_id == google_id))


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create(
    db: Session,
    *,
    google_id: str,
    name: str,
    email: str,
    profile_image: str | None,
    role: UserRole = UserRole.STUDENT,
) -> User:
    user = User(
        google_id=google_id,
        name=name,
        email=email.lower(),
        profile_image=profile_image,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
