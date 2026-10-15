"""3.1/3.2 — medios por subtema (solo enlaces) y validación de contenido.

- Los medios son SIEMPRE URLs con host en MEDIA_ALLOWED_HOSTS (defecto
  vacío: se rechaza cualquier enlace hasta que el despliegue
  defina la lista). Nunca se suben binarios.
- validated es un flag conmutable por docente por unidad y por subtema.
  SHOW_ONLY_VALIDATED (defecto False) decide si el catálogo filtra al mostrar.
"""
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.content import Subtopic, Topic
from app.models.media import SubtopicMedia
from app.schemas.content import MediaCreate, MediaRead
from app.services.exceptions import NotFoundError, ServiceError

# Roles de media permitidos (listón corto y explícito).
MEDIA_KINDS = {"video", "pdf", "animacion", "enlace"}


def _hosts_permitidos() -> list[str]:
    return [h.strip().lower() for h in settings.MEDIA_ALLOWED_HOSTS.split(",") if h.strip()]


def url_con_host_permitido(url: str) -> bool:
    """El host del URL (exacto o coincidencia con comodín *.dominio) está en la lista.

    Si MEDIA_ALLOWED_HOSTS está vacío NO se permite nada: por defecto se
    cierra el grifo (el estudiante no debe ver enlaces de terceros).
    """
    permitidos = _hosts_permitidos()
    if not permitidos:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = parsed.hostname or ""
    host = host.lower()
    for entry in permitidos:
        if entry.startswith("*."):
            dominio = entry[2:].lstrip(".")
            if host == dominio or host.endswith("." + dominio):
                return True
        elif host == entry:
            return True
    return False


def media_read(m: SubtopicMedia) -> MediaRead:
    return MediaRead(id=m.id, url=m.url, kind=m.kind, order=m.order)


def add_media(db: Session, subtopic_id: int, payload: MediaCreate) -> SubtopicMedia:
    subtopic = db.get(Subtopic, subtopic_id)
    if subtopic is None:
        raise NotFoundError("Subtema no encontrado.")
    if payload.kind not in MEDIA_KINDS:
        raise ServiceError(f"kind debe ser uno de: {', '.join(sorted(MEDIA_KINDS))}")
    if not url_con_host_permitido(payload.url):
        permitidos = settings.MEDIA_ALLOWED_HOSTS or "(vacía)"
        raise ServiceError(
            f"Host no permitido para medios. MEDIA_ALLOWED_HOSTS = {permitidos}"
        )
    m = SubtopicMedia(
        subtopic_id=subtopic_id,
        url=str(payload.url),
        kind=payload.kind,
        order=payload.order,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def list_media(db: Session, subtopic_id: int) -> list[SubtopicMedia]:
    return list(
        db.execute(
            select(SubtopicMedia)
            .where(SubtopicMedia.subtopic_id == subtopic_id)
            .order_by(SubtopicMedia.order, SubtopicMedia.id)
        ).scalars()
    )


def delete_media(db: Session, subtopic_id: int, media_id: int) -> None:
    m = db.get(SubtopicMedia, media_id)
    if m is None or m.subtopic_id != subtopic_id:
        raise NotFoundError("Medio no encontrado en este subtema.")
    db.delete(m)
    db.commit()


def set_validated_subtopic(db: Session, subtopic_id: int, validated: bool) -> Subtopic:
    subtopic = db.get(Subtopic, subtopic_id)
    if subtopic is None:
        raise NotFoundError("Subtema no encontrado.")
    subtopic.validated = validated
    db.commit()
    db.refresh(subtopic)
    return subtopic


def set_validated_topic(db: Session, topic_id: int, validated: bool) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise NotFoundError("Unidad no encontrada.")
    topic.validated = validated
    db.commit()
    db.refresh(topic)
    return topic


def filtrar_visibles(subtemas: list[dict], config_flag: bool) -> list[dict]:
    """Si SHOW_ONLY_VALIDATED=True, oculta subtemas no validados."""
    if not config_flag:
        return subtemas
    return [s for s in subtemas if s.get("validated", True)]
