from pydantic import BaseModel, ConfigDict


class QuestionRead(BaseModel):
    """Pregunta de repaso para el estudiante (sin la respuesta correcta).

    El enunciado y las opciones viajan al cliente; la calificación ocurre en
    el servidor (POST /api/quiz/answers), que devuelve is_correct, la correcta
    y la explicación tras responder. NO expone source/status/created_by:
    los estudiantes solo reciben preguntas aprobadas.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    subtopic_id: int
    prompt: str
    options: list[str]
    order: int


class QuestionTeacherRead(BaseModel):
    """Pregunta vista desde el panel del profesor (banco de preguntas).

    Incluye procedencia, estado y autoría para los flujos de revisión.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    subtopic_id: int
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str
    order: int
    source: str
    status: str
    created_by: int | None
    is_owner: bool = False


class TeacherQuestionCreate(BaseModel):
    """Creación manual de una pregunta por el profesor."""

    prompt: str
    options: list[str]
    correct_index: int
    explanation: str | None = None


class TeacherQuestionUpdate(BaseModel):
    """Edición parcial de una pregunta propia."""

    prompt: str | None = None
    options: list[str] | None = None
    correct_index: int | None = None
    explanation: str | None = None


class QuestionReviewAction(BaseModel):
    """Aprobar o rechazar una pregunta IA pendiente."""

    action: str  # "approve" | "reject" (validado en el servicio)


class DeleteQuestionResponse(BaseModel):
    """Resultado del borrado (puede archivarse si tiene respuestas)."""

    deleted: bool
    archived: bool
    detail: str | None = None


class SubtopicListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    name: str
    order: int
    completed: bool = False
    estimated_minutes: int = 0
    question_count: int = 0


class TopicWithSubtopics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    order: int
    completed_subtopics: int = 0
    total_subtopics: int = 0
    estimated_minutes: int = 0
    question_count: int = 0
    subtopics: list[SubtopicListItem] = []


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    order: int


class SubtopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    name: str
    content: str
    order: int
    completed: bool = False
    estimated_minutes: int = 0
    questions: list[QuestionRead] = []
