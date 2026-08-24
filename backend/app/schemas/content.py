from pydantic import BaseModel, ConfigDict


class SubtopicListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    name: str
    order: int
    completed: bool = False


class TopicWithSubtopics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    order: int
    completed_subtopics: int = 0
    total_subtopics: int = 0
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
