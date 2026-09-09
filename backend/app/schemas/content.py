from pydantic import BaseModel, ConfigDict


class QuestionRead(BaseModel):
    """Pregunta de repaso de un subtema, con su respuesta y explicación.

    La corrección se resuelve en el cliente para dar retroalimentación
    inmediata: son preguntas formativas de autoevaluación, no un examen
    calificado.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    subtopic_id: int
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str
    order: int


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
