"""Limpieza de preguntas de relleno — borrado suave reversible.

Por defecto DRY-RUN: solo muestra qué cambiaría y escribe el respaldo.
Con --apply: guarda un respaldo JSON con TODA la fila afectada y luego
cambia status → 'rejected' en la base de datos. Nunca borra filas.

Reutiliza EXACTAMENTE los mismos criterios y pesos que
backend/scripts/audit_questions.py (flag: "Pregunta banco"/hex id) para
evitar divergencias entre lo que se audita y lo que se limpia.

Uso:
    python backend/scripts/cleanup_placeholder_questions.py                 # dry-run
    python backend/scripts/cleanup_placeholder_questions.py --apply        # NO ejecutar salvo decisión explícita
    python backend/scripts/cleanup_placeholder_questions.py --db-url ... --respaldo respaldo.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal  # noqa: E402
from app.models.content import Question  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from audit_questions import classify_severity, suspicious_reasons  # noqa: E402


def placeholder_reasons(question: Question, seen: set) -> list[str]:
    """Motivos de sospecha FUERTE (los que autorizan la limpieza)."""
    reasons = suspicious_reasons(question, seen)
    if reasons and classify_severity(reasons) == "fuerte":
        return reasons
    return []


def serialize(question: Question) -> dict:
    """Respaldo JSON de la fila (sin dependencia del ORM del app)."""
    return {
        "id": question.id,
        "subtopic_id": question.subtopic_id,
        "prompt": question.prompt,
        "options": question.options,
        "correct_index": question.correct_index,
        "explanation": question.explanation,
        "order": question.order,
        "source": question.source,
        "previous_status": question.status,
        "new_status": "rejected",
        "created_by": question.created_by,
        "created_at": question.created_at.isoformat() if question.created_at else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Marcar placeholder questions como rejected")
    parser.add_argument("--db-url", default=None, help="URL SQLAlchemy (por defecto DATABASE_URL env)")
    parser.add_argument("--apply", action="store_true", help="EJECUTAR el cambio (status→rejected)")
    parser.add_argument(
        "--respaldo",
        default=None,
        help="Ruta del archivo JSON de respaldo (por defecto docs/respaldo-limpieza-preguntas-<fecha>.json)",
    )
    args = parser.parse_args()

    if args.db_url:
        engine = __import__("sqlalchemy").create_engine(args.db_url)
        db = Session(bind=engine)
    else:
        db = SessionLocal()

    try:
        seen: set = set()
        flagged: list[Question] = []
        for question in db.scalars(select(Question).order_by(Question.id)):
            if placeholder_reasons(question, seen):
                flagged.append(question)

        print(f"Encontradas {len(flagged)} preguntas con sospecha FUERTE.")
        for question in flagged:
            print(f"  - id={question.id} status={question.status} {question.prompt[:60]!r}")

        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        repo_root = BACKEND_DIR.parent
        backup_path = (
            Path(args.respaldo)
            if args.respaldo
            else repo_root / "docs" / f"respaldo-limpieza-preguntas-{now}.json"
        )

        backup = {"generated_at": now, "questions": [serialize(q) for q in flagged]}
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(
            json.dumps(backup, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Respaldo escrito en {backup_path}")

        if not args.apply:
            print(
                "DRY-RUN: no se cambió nada en la base de datos. "
                "Para ejecutarlo de verdad añade --apply (requiere decisión manual)."
            )
            return

        print("Cambiando status a 'rejected'…")
        for question in flagged:
            question.status = "rejected"
        db.commit()
        print("Listo: respaldo guardado y filas marcadas rejected (borrado suave, reversible).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
