import csv
import io
from typing import Literal

from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.api.routes.ai import limiter
from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.core.config import settings
from app.models.user import User
from app.models.feedback import Feedback, UsabilityEvaluation
from app.repositories import feedback_repository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, EvaluationCreate, HEURISTIC_IDS

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
@limiter.limit("5/minute")
def create_feedback(
    request: Request,
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return feedback_repository.create(db, current_user.id, payload)


@router.post("/evaluations", response_model=FeedbackResponse, status_code=201)
@limiter.limit("5/minute")
def create_evaluation(
    request: Request,
    payload: EvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return feedback_repository.create_evaluation(db, current_user.id, payload)
    except ValueError:
        raise HTTPException(409, "No se pudo registrar esta entrega. Abre una nueva evaluación.") from None


def can_review(user: User) -> bool:
    reviewers = {email.strip().lower() for email in settings.FEEDBACK_REVIEWER_EMAILS.split(",") if email.strip()}
    return user.email.lower() in reviewers


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    if not can_review(user):
        raise HTTPException(403, "La revisión de opiniones requiere autorización del equipo investigador.")
    return user


@router.get("/access")
def feedback_access(user: User = Depends(get_current_user)):
    return {"can_review": can_review(user)}


@router.get("/review")
def review_feedback(
    response: Response,
    kind: Literal["pqrs", "evaluacion"] = "pqrs",
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    reviewer: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    model = Feedback if kind == "pqrs" else UsabilityEvaluation
    total = db.scalar(select(func.count()).select_from(model))
    records = db.scalars(select(model).order_by(model.creado_en.desc(), model.id.desc()).offset(offset).limit(limit))
    items = []
    for row in records:
        item = {"id": row.id, "participante": f"P{row.user_id}", "creado_en": row.creado_en,
                "pagina": row.pagina, "comentario": row.comentario}
        if kind == "pqrs":
            item.update(tipo=row.tipo, categoria=row.categoria)
        else:
            item.update(version=row.version, dispositivo=row.dispositivo, respuestas=row.respuestas)
        items.append(item)
    response.headers["Cache-Control"] = "no-store"
    return {"items": items, "total": total, "offset": offset, "limit": limit}


def csv_cell(value):
    value = str(value or "")
    # Evita que Excel/Sheets interpreten comentarios como fórmulas al abrir el CSV.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value


@router.get("/export.csv")
@limiter.limit("10/hour")
def export_feedback(
    request: Request,
    reviewer: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["tipo_registro", "id", "participante", "fecha_utc", "pagina", "version", "dispositivo", "tipo_pqrs", "categoria", *HEURISTIC_IDS, "comentario"])
    for model, kind in ((Feedback, "pqrs"), (UsabilityEvaluation, "evaluacion")):
        for item in db.scalars(select(model).order_by(model.id).execution_options(yield_per=200)):
            answers = getattr(item, "respuestas", {})
            writer.writerow([kind, item.id, f"P{item.user_id}", item.creado_en.isoformat(), csv_cell(item.pagina),
                             getattr(item, "version", ""), getattr(item, "dispositivo", ""),
                             getattr(item, "tipo", ""), getattr(item, "categoria", ""),
                             *[answers.get(key) for key in HEURISTIC_IDS], csv_cell(item.comentario)])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": 'attachment; filename="insoft-opiniones.csv"',
        "Cache-Control": "no-store",
    })
