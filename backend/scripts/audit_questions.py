"""Auditoría SOLO LECTURA del banco de preguntas.

Reporta conteos por `source` y `status`, desglose por unidad/subtema, y
marca preguntas sospechosas (relleno de pruebas, datos degenerados o
duplicados). Genera docs/auditoria-preguntas.md con el resumen y la lista
(id, enunciado, motivos). NO modifica nada.

Criterios de sospecha:
- Enunciado que empieza por "Pregunta banco" o contiene un id hexadecimal.
- Opciones de una sola letra, muy cortas (<= 2 caracteres) o repetidas.
- correct_index fuera de rango.
- Explicación vacía.
- Enunciados duplicados (misma subtema, texto normalizado).

Uso:
    python backend/scripts/audit_questions.py [--db-url URL] [--output RUTA]

Sin --db-url usa DATABASE_URL del entorno; si no, la Settings de la app
(útil si se corre dentro del contenedor del backend).
"""
import argparse
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.session import SessionLocal  # noqa: E402
from app.models.content import Question, Subtopic, Topic  # noqa: E402
from app.services.question_service import normalize_prompt  # noqa: E402

HEX_ID = re.compile(r"\b[0-9a-f]{6,}\b", re.IGNORECASE)
PLACEHOLDER_PREFIX = "pregunta banco"


def suspicious_reasons(question: Question, seen_prompts: set[str]) -> list[str]:
    """Motivos por los que una pregunta parece de relleno o degenerada."""
    reasons: list[str] = []
    prompt = (question.prompt or "").strip()
    lowered = prompt.lower()

    if lowered.startswith(PLACEHOLDER_PREFIX):
        reasons.append("Enunciado de relleno ('Pregunta banco …')")
    if question.id is not None and HEX_ID.search(prompt):
        reasons.append("Enunciado contiene un id hexadecimal")

    options = question.options or []
    if any(len(option.strip()) == 1 for option in options):
        reasons.append("Opciones de una sola letra (a, b, c, d)")
    if any(0 < len(option.strip()) <= 2 for option in options):
        reasons.append("Opciones demasiado cortas (<= 2 caracteres)")
    if len({option.strip().casefold() for option in options}) < len(
        [o for o in options if o.strip()]
    ):
        reasons.append("Opciones repetidas")
    if len(options) != 4:
        reasons.append(f"No tiene 4 opciones ({len(options)})")

    if not isinstance(question.correct_index, int) or not (
        0 <= question.correct_index < len(options)
    ):
        reasons.append("correct_index fuera de rango")

    if not (question.explanation or "").strip():
        reasons.append("Explicación vacía")

    key = (question.subtopic_id, normalize_prompt(prompt))
    if key in seen_prompts:
        reasons.append("Enunciado duplicado en el subtema")
    seen_prompts.add(key)

    return reasons


def classify_severity(reasons: list[str]) -> str:
    """Sospecha fuerte = casi seguro relleno; leve = revisar a mano."""
    strong = {
        "Enunciado de relleno ('Pregunta banco …')",
        "Enunciado contiene un id hexadecimal",
        "Opciones de una sola letra (a, b, c, d)",
        "correct_index fuera de rango",
        "No tiene 4 opciones (0)",
    }
    return "fuerte" if any(r in strong for r in reasons) else "leve"


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoría solo lectura de questions")
    parser.add_argument("--db-url", default=None, help="URL SQLAlchemy (por defectoDATABASE_URL env)")
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta del markdown (por defecto docs/auditoria-preguntas.md relativo al repo)",
    )
    args = parser.parse_args()

    if args.db_url:
        engine = __import__("sqlalchemy").create_engine(args.db_url)
        db = Session(bind=engine)
    else:
        db = SessionLocal()

    try:
        rows = db.execute(
            select(Question, Topic.name, Subtopic.name)
            .join(Subtopic, Question.subtopic_id == Subtopic.id)
            .join(Topic, Subtopic.topic_id == Topic.id)
            .order_by(Topic.order, Subtopic.order, Question.order)
        ).all()

        by_source = Counter(r[0].source for r in rows)
        by_status = Counter(r[0].status for r in rows)
        by_source_status = Counter((r[0].source, r[0].status) for r in rows)
        per_topic: dict[str, Counter] = {}

        seen: set = set()
        flagged: list = []
        for question, topic_name, subtopic_name in rows:
            per_topic.setdefault(topic_name, Counter())[subtopic_name] += 1
            reasons = suspicious_reasons(question, seen)
            if reasons:
                flagged.append((question, topic_name, subtopic_name, reasons))

        repo_root = BACKEND_DIR.parent
        out_path = (
            Path(args.output)
            if args.output
            else repo_root / "docs" / "auditoria-preguntas.md"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Auditoría del banco de preguntas",
            "",
            f"Generado: {datetime.now(timezone.utc).isoformat(timespec='seconds')} (UTC) · "
            "script backend/scripts/audit_questions.py (solo lectura)",
            "",
            "## Totales",
            "",
            f"- Preguntas totales: **{len(rows)}**",
            "- Por source: " + ", ".join(f"`{k}` {v}" for k, v in sorted(by_source.items())),
            "- Por status: " + ", ".join(f"`{k}` {v}" for k, v in sorted(by_status.items())),
            "- Por combinación source/status: "
            + ", ".join(
                f"`{s}/{t}` {c}" for (s, t), c in sorted(by_source_status.items())
            ),
            "",
            "## Desglose por unidad y subtema",
            "",
        ]
        for topic_name, subtopics in per_topic.items():
            lines.append(f"- **{topic_name}**: {sum(subtopics.values())} preguntas")
            for subtopic_name, count in subtopics.items():
                lines.append(f"  - {subtopic_name}: {count}")
        lines += [
            "",
            f"## Preguntas sospechosas ({len(flagged)})",
            "",
        ]
        strong = [f for f in flagged if classify_severity(f[3]) == "fuerte"]
        lines += [
            f"- Sospecha fuerte (casi seguro relleno): {len(strong)}",
            f"- Sospecha leve (revisar a mano): {len(flagged) - len(strong)}",
            "",
            "| id | source | status | unidad › subtema | enunciado | motivos |",
            "|----|--------|--------|------------------|-----------|---------|",
        ]
        for question, topic_name, subtopic_name, reasons in flagged:
            prompt_short = question.prompt.replace("|", "\\|")[:70]
            reasons_cell = "; ".join(reasons).replace("|", "/")
            lines.append(
                f"| {question.id} | {question.source} | {question.status} "
                f"| {topic_name} › {subtopic_name} | {prompt_short} | {reasons_cell} |"
            )
        lines += ["", ""]

        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Reporte escrito en {out_path}")
        print(
            f"Total {len(rows)} preguntas; sospechosas {len(flagged)} "
            f"(fuertes {len(strong)})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
