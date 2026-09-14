from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_teacher
from app.database.session import get_db
from app.models.user import User
from app.schemas.content import QuestionRead, SubtopicRead, TopicWithSubtopics
from app.schemas.content_import import ImportDocumentRequest, ImportDocumentResponse
from app.services import content_service
from app.services.content_import import import_document

router = APIRouter(tags=["content"])


@router.post("/content/import", response_model=ImportDocumentResponse)
def import_content(
    payload: ImportDocumentRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Solo profesores. Importa un documento Markdown como contenido centralizado.

    Actualiza por nombre de unidad/subtema y crea lo que falte. Al terminar,
    indexa el contenido en el RAG y lo enlaza a todos los cursos. Nunca borra
    contenido que el documento no mencione.
    """
    try:
        return import_document(db, payload.document)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/courses/{course_id}/topics", response_model=list[TopicWithSubtopics])
def get_course_topics(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Temas y subtemas del contenido oficial habilitados en el curso."""
    return content_service.get_course_content(db, current_user, course_id)


@router.get("/topics/{topic_id}/questions", response_model=list[QuestionRead])
def get_topic_questions(
    topic_id: int,
    course_id: int = Query(..., description="Curso desde el que se consulta el contenido"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Preguntas de repaso de todos los subtemas de una unidad."""
    return content_service.get_topic_questions(db, current_user, course_id, topic_id)


@router.get("/subtopics/{subtopic_id}", response_model=SubtopicRead)
def get_subtopic(
    subtopic_id: int,
    course_id: int = Query(..., description="Curso desde el que se consulta el contenido"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return content_service.get_subtopic_detail(db, current_user, course_id, subtopic_id)
