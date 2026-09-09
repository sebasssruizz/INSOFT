"""Estimación del tiempo de estudio de un subtema.

Vive aparte para que tanto el servicio de contenido como el de cursos puedan
usarla sin importarse entre sí.
"""
import math

# Ritmo de lectura de estudio (más lento que la lectura corriente por tratarse
# de contenido técnico) y tiempo dedicado a razonar cada pregunta de repaso.
STUDY_WORDS_PER_MINUTE = 90
MINUTES_PER_QUESTION = 1.5
MIN_SUBTOPIC_MINUTES = 4


def estimate_minutes(subtopic) -> int:
    """Minutos estimados para leer un subtema y resolver sus preguntas."""
    words = len(subtopic.content.split())
    reading = words / STUDY_WORDS_PER_MINUTE
    quiz = len(subtopic.questions) * MINUTES_PER_QUESTION
    return max(MIN_SUBTOPIC_MINUTES, math.ceil(reading + quiz))
