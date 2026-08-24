"""Lógica de autenticación: alta/búsqueda de usuarios tras Google OAuth."""
from sqlalchemy.orm import Session

from app.auth import google as google_auth
from app.core.config import settings
from app.models.user import User, UserRole
from app.repositories import user_repository as user_repo
from app.services import course_service
from app.services.exceptions import BadRequestError, UnauthorizedError


def _role_for_email(email: str) -> UserRole:
    """Rol inicial: profesor si el correo está en TEACHER_EMAILS, si no estudiante."""
    if email.lower() in settings.teacher_emails:
        return UserRole.TEACHER
    return UserRole.STUDENT


def _finalize_login(db: Session, user: User, is_new: bool) -> User:
    if is_new and user.role == UserRole.STUDENT:
        # Acceso automático al Curso General de Oftalmología
        course_service.enroll_student_in_general_course(db, user)
    return user


def authenticate_with_google(db: Session, credential: str) -> User:
    try:
        info = google_auth.verify_google_credential(credential)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = user_repo.get_by_google_id(db, info["google_id"])
    if user is not None:
        return user

    # Vincular cuenta existente con el mismo correo
    user = user_repo.get_by_email(db, info["email"])
    if user is not None:
        user.google_id = info["google_id"]
        db.commit()
        db.refresh(user)
        return user

    user = user_repo.create(
        db,
        google_id=info["google_id"],
        name=info["name"],
        email=info["email"],
        profile_image=info["profile_image"],
        role=_role_for_email(info["email"]),
    )
    return _finalize_login(db, user, is_new=True)


def change_own_role(db: Session, user: User, new_role: UserRole) -> User:
    """El usuario cambia su propio rol (autogestión).

    No permite modificar roles de otros usuarios. Si pasa a estudiante,
    se le inscribe automáticamente en el Curso General de Oftalmología.
    """
    if user.role == new_role:
        return user
    user.role = new_role
    db.commit()
    db.refresh(user)
    if new_role == UserRole.STUDENT:
        course_service.enroll_student_in_general_course(db, user)
    return user


def authenticate_dev(db: Session, email: str, name: str, role: str) -> User:
    """Login de desarrollo sin Google. Solo disponible si DEV_AUTH_ENABLED=true."""
    if not settings.DEV_AUTH_ENABLED:
        raise BadRequestError("El login de desarrollo está desactivado.")

    email = email.lower()
    user = user_repo.get_by_email(db, email)
    if user is not None:
        # En modo desarrollo, sincronizar el rol con el solicitado facilita las pruebas
        requested = UserRole.TEACHER if role.upper() == "TEACHER" else UserRole.STUDENT
        if user.role != requested:
            user.role = requested
            db.commit()
            db.refresh(user)
            if requested == UserRole.STUDENT:
                course_service.enroll_student_in_general_course(db, user)
        return user
    if user is None:
        # TEACHER_EMAILS tiene prioridad sobre el rol solicitado (igual que con Google)
        user_role = UserRole.TEACHER if (email in settings.teacher_emails or role.upper() == "TEACHER") else UserRole.STUDENT
        user = user_repo.create(
            db,
            google_id=f"dev-{email}",
            name=name,
            email=email,
            profile_image=None,
            role=user_role,
        )
        return _finalize_login(db, user, is_new=True)
    return user
