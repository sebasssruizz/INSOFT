"""Interruptores de la IA: apagado general y tope diario GLOBAL de llamadas al proveedor.

- `AI_ENABLED=false`: no se llama al proveedor. El asistente usa el modo respaldo
  (fragmentos oficiales) si hay contexto; si no, se responde 503 "[asistente-desactivado]".
- `AI_GLOBAL_DAILY_CALLS=N`: como máximo N llamadas al proveedor por día UTC, sumando
  todas las funciones (consultas, normalización y generación). El contador vive en la
  tabla `ai_calls_daily`, así que sobrevive a reinicios. La reserva es atómica
  (`INSERT … ON CONFLICT … WHERE`), válida en PostgreSQL y SQLite.

Cuando el tope se agota no se degrada a "error": el asistente responde con el modo
respaldo (sin gastar créditos) y, si no hay fragmentos, 429 "[asistente-tope-global]".
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.config import settings


class AiDisabledError(Exception):
    """La IA está apagada por configuración (AI_ENABLED=false)."""


class AiBudgetExceededError(Exception):
    """Se agotó el tope global diario de llamadas al proveedor."""


def ia_habilitada() -> bool:
    return bool(settings.AI_ENABLED)


def segundos_hasta_manana_utc(ahora: datetime | None = None) -> int:
    """Segundos hasta el próximo día UTC (cuándo se reinicia el tope)."""
    ahora = ahora or datetime.now(timezone.utc)
    manana = (ahora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60, int((manana - ahora).total_seconds()))


def reservar_llamada(session_factory=None) -> bool:
    """Reserva una llamada del día. Devuelve False si el tope global ya se agotó.

    Sin tope configurado (0) siempre devuelve True y no toca la base.
    """
    limite = int(settings.AI_GLOBAL_DAILY_CALLS or 0)
    if limite <= 0:
        return True

    if session_factory is None:
        from app.database.session import SessionLocal as session_factory  # noqa: N814

    hoy = datetime.now(timezone.utc).date()
    with session_factory() as db:
        fila = db.execute(
            text(
                """
                INSERT INTO ai_calls_daily (day, calls) VALUES (:dia, 1)
                ON CONFLICT (day) DO UPDATE SET calls = ai_calls_daily.calls + 1
                WHERE ai_calls_daily.calls < :limite
                RETURNING calls
                """
            ),
            {"dia": hoy, "limite": limite},
        ).first()
        db.commit()
    return fila is not None
