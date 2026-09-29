"""Constantes de procedencia y estado de las preguntas.

Fuente única de verdad para `Question.source` y `Question.status`, usada por
el modelo, los schemas y los servicios. No se definen CHECK constraints en la
base (el proyecto no los usa): la validación vive aquí y en Pydantic.
"""


class QuestionSource:
    """Quién creó la pregunta."""

    OFFICIAL = "official"  # Importada del compendio oficial (importador Markdown)
    AI = "ai"  # Generada por el asistente de IA
    TEACHER = "teacher"  # Creada manualmente por un profesor

    ALL = (OFFICIAL, AI, TEACHER)


class QuestionStatus:
    """Ciclo de vida de la pregunta frente a los estudiantes."""

    APPROVED = "approved"  # Visible en quizzes
    PENDING = "pending"  # Esperando revisión del profesor (preguntas IA)
    REJECTED = "rejected"  # Descartada; se conserva para historial/auditoría

    ALL = (APPROVED, PENDING, REJECTED)
