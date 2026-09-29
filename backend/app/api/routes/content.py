from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_teacher
from app.database.session import get_db
from app.models.user import User
from app.schemas.content import (
    DeleteQuestionResponse,
    QuestionRead,
    QuestionReviewAction,
    QuestionTeacherRead,
    SubtopicRead,
    TeacherQuestionCreate,
    TeacherQuestionUpdate,
    TopicWithSubtopics,
)
from app.schemas.content_import import ImportDocumentRequest, ImportDocumentResponse
from app.services import content_service, question_service
from app.services.content_import import import_document
from app.services.content_service import serialize_question_for_teacher

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


@router.post(
    "/content/subtopics/{subtopic_id}/questions",
    response_model=QuestionTeacherRead,
    status_code=201,
    tags=["content"],
    summary="Creación manual de una pregunta por el profesor",
    responses={401: {"description": "Sin token"}, 403: {"description": "Sin acceso al subtema"},
               404: {"description": "Subtema no encontrado"}, 409: {"description": "Enunciado duplicado"},
               422: {"description": "Validación de campos"}},
)
def create_teacher_question(
    subtopic_id: int,
    payload: TeacherQuestionCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Crea una pregunta docente (approved: visible de inmediato para estudiantes)."""
    question = question_service.create_teacher_question(
        db,
        current_user,
        subtopic_id,
        prompt=payload.prompt,
        options=payload.options,
        correct_index=payload.correct_index,
        explanation=payload.explanation,
    )
    return serialize_question_for_teacher(question, current_user.id)


@router.get(
    "/content/subtopics/{subtopic_id}/questions/bank",
    response_model=list[QuestionTeacherRead],
    tags=["content"],
    summary="Banco de preguntas de un subtema (profesor)",
    responses={401: {"description": "Sin token"}, 403: {"description": "Sin acceso al subtema"},
               404: {"description": "Subtema no encontrado"}, 422: {"description": "Filtro inválido"}},
)
def get_subtopic_question_bank(
    subtopic_id: int,
    status: str | None = Query(default=None, description="Filtro por estado (approved|pending|rejected)"),
    source: str | None = Query(default=None, description="Filtro por origen (official|ai|teacher)"),
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Todas las preguntas del subtema (oficiales, docentes e IA) con su estado."""
    questions = question_service.get_subtopic_bank(
        db, current_user, subtopic_id, status=status, source=source
    )
    return [
        serialize_question_for_teacher(q, current_user.id) for q in questions
    ]


@router.get(
    "/content/topics/{topic_id}/questions/summary",
    response_model=list[dict],
    tags=["content"],
    summary="Resumen de conteos de preguntas por subtema (profesor)",
    responses={401: {"description": "Sin token"}, 403: {"description": "Sin acceso a la unidad"},
               404: {"description": "Unidad no encontrada"}},
)
def get_topic_question_summary(
    topic_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Conteos por subtema (total, approved, pending, rejected, official, teacher, ai)."""
    return question_service.get_topic_bank_summary(db, current_user, topic_id)


@router.patch(
    "/content/questions/{question_id}",
    response_model=QuestionTeacherRead,
    tags=["content"],
    summary="Edición parcial de una pregunta propia",
    responses={401: {"description": "Sin token"}, 403: {"description": "No es el autor / oficial"},
               404: {"description": "Pregunta no encontrada"}, 409: {"description": "Enunciado duplicado"},
               422: {"description": "Validación de campos"}},
)
def update_teacher_question(
    question_id: int,
    payload: TeacherQuestionUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Edita una pregunta propia. Editar una IA pendiente no la aprueba."""
    question = question_service.update_question(
        db,
        current_user,
        question_id,
        prompt=payload.prompt,
        options=payload.options,
        correct_index=payload.correct_index,
        explanation=payload.explanation,
    )
    return serialize_question_for_teacher(question, current_user.id)


@router.delete(
    "/content/questions/{question_id}",
    response_model=DeleteQuestionResponse,
    tags=["content"],
    summary="Borrado de una pregunta propia (o archivado si tiene respuestas)",
    responses={401: {"description": "Sin token"}, 403: {"description": "No es el autor / oficial"},
               404: {"description": "Pregunta no encontrada"}},
)
def delete_teacher_question(
    question_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Borra una pregunta propia; si tiene respuestas asociadas, la archiva."""
    return question_service.delete_question(db, current_user, question_id)


@router.post(
    "/content/questions/{question_id}/review",
    response_model=QuestionTeacherRead,
    tags=["content"],
    summary="Aprobación o rechazo de una pregunta IA pendiente",
    responses={401: {"description": "Sin token"}, 403: {"description": "No es el autor"},
               404: {"description": "Pregunta no encontrada"}, 409: {"description": "No es IA pendiente"},
               422: {"description": "action inválido"}},
)
def review_teacher_question(
    question_id: int,
    payload: QuestionReviewAction,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """Aprobar (approved) o rechazar (rejected) una pregunta IA pendiente."""
    question = question_service.review_ai_question(db, current_user, question_id, payload.action)
    return serialize_question_for_teacher(question, current_user.id)
