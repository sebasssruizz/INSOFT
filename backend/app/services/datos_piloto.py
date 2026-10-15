"""Acceso y borrar (3.5): pseudónimos y exportes anonimizados del piloto.

- Exporte propio (`GET /api/users/me/export`): JSON con un pseudónimo HMAC
  (derivado de SECRET_KEY, no reversible desde DATABASE_URL ni a la inversa).
  Nunca incluye email ni google_id.
- Anonimización (`DELETE /api/users/me`): sustituye PII por pseudónimos;
  conserva integridad referencial (progreso/auditoría NO se borran).
- Retención de consultas IA (`AI_QUERY_RETENTION_DAYS`, 0 desactiva).
"""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai_query import AiQuery
from app.models.progress import Progress
from app.models.question_answer import QuestionAnswer
from app.models.user import User


def pseudonimo(user_id: int) -> str:
    """Pseudónimo estable del usuario (HMAC-SHA256 con SECRET_KEY).

    Determinístico: la segunda anonimización produce el mismo valor, y las
    tablas de auditoría pueden agrupar por este código sin exponer PII.
    """
    mac = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), f"piloto:{user_id}".encode("utf-8"), hashlib.sha256
    )
    return mac.hexdigest()[:16]


def _email_anonimo(user_id: int) -> str:
    """Correo sintético para el UNIQUE de la cuenta anonimizada.

    Dominio reservado de ejemplo (.invalid): nunca le llega correo real.
    """
    return f"eliminado-{pseudonimo(user_id)}@ejemplo.invalid"


def export_user(db: Session, user: User) -> dict:
    """Datos en poder del usuario, SIN PII difusa (identificador pseudónimo)."""
    progreso = (
        db.query(Progress)
        .filter(Progress.user_id == user.id)
        .order_by(Progress.updated_at)
        .all()
    )
    consultas = (
        db.query(AiQuery)
        .filter(AiQuery.user_id == user.id)
        .order_by(AiQuery.created_at)
        .all()
    )
    respuestas = (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.user_id == user.id)
        .order_by(QuestionAnswer.answered_at)
        .all()
    )
    return {
        "nota_generacion": "Exporte anonimizado; el pseudónimo es HMAC-SHA256(SECRET_KEY, piloto:<id>) truncado.",
        "pseudonimo": pseudonimo(user.id),
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "perfil": {
            "rol": user.role.value if user.role else None,
            "pais": user.country,
            "edad": user.age,
            "fecha_registro": user.created_at.isoformat() if user.created_at else None,
        },
        "progreso": [
            {
                "curso_id": p.course_id,
                "subtema_id": p.subtopic_id,
                "completado": p.completed,
                "actualizado": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in progreso
        ],
        "consultas_ia": [
            {
                "subtema_id": q.subtopic_id,
                "sesion": str(q.session_id) if q.session_id else None,
                "estado": q.status,
                "pregunta": q.question_original,
                "fecha": q.created_at.isoformat() if q.created_at else None,
            }
            for q in consultas
        ],
        "respuestas_practica": [
            {
                "pregunta_id": a.question_id,
                "subtema_id": a.subtopic_id,
                "intentos": a.attempt_id,
                "opcion_elegida": a.selected_index,
                "correcta": a.is_correct,
                "fecha": a.answered_at.isoformat() if a.answered_at else None,
            }
            for a in respuestas
        ],
    }


def anonimizar_user(db: Session, user: User) -> None:
    """Borra PII del usuario preservando filas e integridad referencial.

    Tras esto la cuenta es inútil: google_id cambia y el siguiente inicio de
    sesión con Google crea una cuenta NUEVA; los scores históricos subsisten
    bajo el pseudónimo.
    """
    user.google_id = f"eliminado-{pseudonimo(user.id)}"
    user.email = _email_anonimo(user.id)
    user.name = "Estudiante eliminado"
    user.profile_image = None
    user.country = None
    user.age = None
    db.commit()


def purgar_ai_anteriores(db: Session) -> int:
    """Elimina consultas IA más viejas que AI_QUERY_RETENTION_DAYS.

    0 desactiva (para entornos de desarrollo/pruebas). Devuelve cuántas filas
    se borraron (para el log del arranque). No toca nada más.
    """
    dias = settings.AI_QUERY_RETENTION_DAYS
    if dias <= 0:
        return 0
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    res = db.execute(delete(AiQuery).where(AiQuery.created_at < limite))
    db.commit()
    return int(res.rowcount or 0)
