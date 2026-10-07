"""Exporta el contenido oficial (desde la base de datos) a un Word de revisión
para la docente.

Uso (desde backend/, con el venv activo y la BD local de Docker levantada):

    DATABASE_URL='postgresql+psycopg2://oftallearn:oftallearn@localhost:5433/oftallearn' \
        python -m app.scripts.export_content_docx ../docs/revision/Contenido_INSOFT_para_revision.docx

Dentro del contenedor del backend:

    docker compose exec backend python -m app.scripts.export_content_docx /docs/revision/Contenido_INSOFT_para_revision.docx

El documento usa estilos reales de Word (Título 1/Título 2) para que funcione
el panel de navegación, tabla de contenido como campo (clic derecho →
Actualizar campo), casillas de revisión por subtema y por pregunta, y resalta
los marcadores [PENDIENTE CLAUDIA]. Se puede volver a correr tras correcciones:
sobrescribe el archivo de salida.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import docx
from sqlalchemy import select
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.database.session import SessionLocal
from app.models.content import Topic, Subtopic, Question

CHECK = "☐"
MARK = "✔"

# Unidades nuevas (borrador pendiente de validación) por `order`.
BORRADOR_ORDERS = {5, 6, 7}

ESTADO_CARGADA = "Cargada por el equipo"
ESTADO_BORRADOR = "Borrador redactado por el equipo a partir del compendio, pendiente de validación"

PENDIENTE_RE = re.compile(r"^\s*>\s*\[PENDIENTE CLAUDIA:?.*$", re.I | re.M)
FUENTE_RE = re.compile(r"^\s*Fuente:\s*(.+)$", re.I)


# ── Utilidades de formato Word ──────────────────────────────────────────────

def set_run_bold(run: docx.text.run.Run, bold: bool = True) -> None:
    run.bold = bold


def add_inline_runs(paragraph, text: str) -> None:
    """Añade runs con **negritas** interpretadas."""
    parts = re.split(r"(\*\*.+?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        else:
            paragraph.add_run(part)


def shade_paragraph(paragraph, fill: str = "FFF3CD") -> None:
    """Sombreado amarillo suave (para PENDIENTE CLAUDIA)."""
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_toc_field(paragraph) -> None:
    """Inserta un campo TOC de Word (requiere 'Actualizar campo')."""
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), 'TOC \\o "1-3" \\h \\z \\u')
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = "(Índice: clic derecho sobre aquí → Actualizar campo)"
    run.append(text)
    fld.append(run)
    paragraph._p.append(fld)


def add_page_number(paragraph) -> None:
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def add_review_table(document, cells: list[str], widths: list[float] | None = None) -> None:
    table = document.add_table(rows=1, cols=len(cells))
    table.style = "Table Grid"
    for i, text in enumerate(cells):
        cell = table.rows[0].cells[i]
        cell.text = ""
        paragraph = cell.paragraphs[0]
        add_inline_runs(paragraph, text)
        for run in paragraph.runs:
            run.font.size = Pt(10)


def add_markdown_content(document, content: str) -> None:
    """Renderiza el markdown del subtema a elementos reales de Word."""
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # PENDIENTE CLAUDIA (resaltado)
        if PENDIENTE_RE.match(line):
            paragraph = document.add_paragraph()
            add_inline_runs(paragraph, stripped.lstrip("> ").strip())
            shade_paragraph(paragraph)
            i += 1
            continue

        # Línea de fuente: se omite (no debe aparecer en el documento)
        if FUENTE_RE.match(line):
            i += 1
            continue

        # Título interno ### del subtema
        if stripped.startswith("### "):
            heading = document.add_heading(stripped[4:], level=3)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x5C)
            i += 1
            continue

        # Tabla GFM
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-|:]+\|$", lines[i + 1].strip()):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            rows: list[list[str]] = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            table = document.add_table(rows=1 + len(rows), cols=len(header))
            table.style = "Table Grid"
            for col, text in enumerate(header):
                cell = table.rows[0].cells[col]
                paragraph = cell.paragraphs[0]
                run = paragraph.add_run(text)
                run.bold = True
                run.font.size = Pt(10)
            for r, row in enumerate(rows, 1):
                for col, text in enumerate(row[: len(header)]):
                    cell = table.rows[r].cells[col]
                    paragraph = cell.paragraphs[0]
                    add_inline_runs(paragraph, text)
                    for run in paragraph.runs:
                        run.font.size = Pt(10)
            i = j
            continue

        # Listas
        if re.match(r"^[-*]\s+", stripped):
            paragraph = document.add_paragraph(style="List Bullet")
            add_inline_runs(paragraph, re.sub(r"^[-*]\s+", "", stripped))
            i += 1
            continue
        m_num = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)
        if m_num:
            # Se conserva el número literal (List Number continuaría la
            # numeración entre listas distintas del documento).
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.5)
            add_inline_runs(paragraph, f"{m_num.group(1)}. {m_num.group(2)}")
            i += 1
            continue

        # Bloque de cita genérico (no PENDIENTE)
        if stripped.startswith(">"):
            paragraph = document.add_paragraph()
            add_inline_runs(paragraph, stripped.lstrip("> ").strip())
            paragraph.paragraph_format.left_indent = Cm(0.5)
            i += 1
            continue

        # Párrafo normal
        if stripped:
            paragraph = document.add_paragraph()
            add_inline_runs(paragraph, stripped)
        i += 1


# ── Exportación ─────────────────────────────────────────────────────────────

def export(db, output_path: Path, version: str = "1.0", unit_numbers: set[int] | None = None) -> dict:
    """Exporta las unidades al Word de revisión.

    `unit_numbers`: si se indica (p. ej. {6,7,8,9}), exporta solo esas unidades
    (número de UNIDAD según el título); siempre incluye portada, instrucciones,
    resumen y la sección de pendientes.
    """
    document = docx.Document()

    # Página y estilo base
    section = document.sections[0]
    section.page_width = Cm(21.59)  # Carta
    section.page_height = Cm(27.94)
    for margin in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(section, margin, Cm(2.5))

    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    header = section.header
    header.text = ""
    hp = header.paragraphs[0]
    hp.text = "INSOFT — Revisión de contenido"
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number(fp)

    # ── Portada ──
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("INSOFT — Plataforma educativa de Instrumentación Quirúrgica (Oftalmología)")
    run.bold = True
    run.font.size = Pt(20)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Documento de revisión de contenido")
    run.bold = True
    run.font.size = Pt(16)

    for line in [
        f"Destinataria: Claudia Romero (docente revisora)",
        f"Fecha de generación: {date.today().strftime('%d/%m/%Y')}",
        f"Versión: {version}",
        "Equipo: Sebastián Ruiz, Eddy Lara, Samuel Muniz",
    ]:
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(line)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ── Instrucciones de revisión ──
    document.add_heading("Instrucciones de revisión", level=1)
    for text in [
        "Este documento contiene el contenido completo de las 9 unidades de la "
        "plataforma, tomado directamente de la base de datos (fuente de verdad). "
        "Sírvase revisar cada subtema y cada pregunta.",
        "Para marcar su revisión, deje la casilla que corresponda tachada o marcada "
        "(☐ → ☑), o reemplace la marca por su observación en la línea de comentarios.",
        "También puede usar las herramientas de comentario de Word (Revisar → "
        "Nuevo comentario) sobre el texto específico.",
        "Por favor devuelva este archivo por el mismo medio por el que lo recibió.",
        "Leyenda: la marca ✔ indica la opción correcta de cada pregunta; los párrafos "
        "sombreados en amarillo corresponden a marcadores [PENDIENTE CLAUDIA], "
        "espacios que el equipo no redactó por no encontrar cobertura en las fuentes.",
    ]:
        document.add_paragraph(text)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ── Tabla de contenido + resumen por unidad ──
    document.add_heading("Tabla de contenido", level=1)
    toc_paragraph = document.add_paragraph()
    add_toc_field(toc_paragraph)
    note = document.add_paragraph()
    note_run = note.add_run("Nota: haga clic derecho sobre el índice y elija «Actualizar campo» para llenarlo.")
    note_run.italic = True

    document.add_heading("Resumen por unidad", level=2)
    topics = list(db.scalars(select(Topic).order_by(Topic.order)).all())
    summary_rows = []
    for topic in topics:
        subtopics = sorted(topic.subtopics, key=lambda s: s.order)
        n_questions = sum(
            1 for s in subtopics for q in s.questions
            if q.source == "official" and q.status == "approved"
        )
        summary_rows.append((topic.name, len(subtopics), n_questions, estado_for(topic)))
    table = document.add_table(rows=1 + len(summary_rows), cols=4)
    table.style = "Table Grid"
    for col, text in enumerate(["Unidad", "Subtemas", "Preguntas", "Estado"]):
        cell = table.rows[0].cells[col]
        run = cell.paragraphs[0].add_run(text)
        run.bold = True
        run.font.size = Pt(10)
    for r, (name, n_sub, n_q, estado) in enumerate(summary_rows, 1):
        values = [name, str(n_sub), str(n_q), estado]
        for col, text in enumerate(values):
            run = table.rows[r].cells[col].paragraphs[0].add_run(text)
            run.font.size = Pt(9 if col == 3 else 10)
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ── Contenido por unidad ──
    totals = {"unidades": 0, "subtemas": 0, "preguntas": 0, "pendientes": 0}
    for topic in topics:
        if unit_numbers is not None:
            m = re.match(r"^UNIDAD\s+(\d+)", topic.name, re.I)
            if not m or int(m.group(1)) not in unit_numbers:
                continue
        document.add_heading(topic.name, level=1)
        if topic.description:
            paragraph = document.add_paragraph()
            add_inline_runs(paragraph, topic.description)
        estado = document.add_paragraph()
        run = estado.add_run("Estado: ")
        run.bold = True
        estado.add_run(estado_for(topic))
        totals["unidades"] += 1

        for subtopic in sorted(topic.subtopics, key=lambda s: s.order):
            document.add_heading(subtopic.name, level=2)
            totals["subtemas"] += 1
            content = subtopic.content or ""
            totals["pendientes"] += len(PENDIENTE_RE.findall(content))
            add_markdown_content(document, content)

            add_review_table(
                document,
                [f"{CHECK} Correcto", f"{CHECK} Corregir", "Comentarios: ______"],
            )
            document.add_paragraph()

            questions = [q for q in sorted(subtopic.questions, key=lambda q: q.order)
                         if q.source == "official" and q.status == "approved"]
            if questions:
                document.add_heading("Preguntas de repaso", level=3)
            for n, question in enumerate(questions, 1):
                totals["preguntas"] += 1
                paragraph = document.add_paragraph()
                add_inline_runs(paragraph, f"{n}. {question.prompt}")
                for letter, option, index in (
                    (chr(ord("A") + idx), opt, idx)
                    for idx, opt in enumerate(question.options)
                ):
                    paragraph = document.add_paragraph()
                    paragraph.paragraph_format.left_indent = Cm(0.75)
                    correct = index == question.correct_index
                    mark = f"{letter}) {option}" + (f"  {MARK}" if correct else "")
                    add_inline_runs(paragraph, mark)
                    if correct:
                        for run in paragraph.runs:
                            run.bold = True
                if question.explanation:
                    paragraph = document.add_paragraph()
                    paragraph.paragraph_format.left_indent = Cm(0.75)
                    run = paragraph.add_run("Explicación: ")
                    run.bold = True
                    add_inline_runs(paragraph, question.explanation)
                review = document.add_paragraph()
                review.paragraph_format.left_indent = Cm(0.75)
                review.add_run(
                    f"{CHECK} Correcta   {CHECK} Corregir   {CHECK} Eliminar   Comentarios: ______"
                )
                for run in review.runs:
                    run.font.size = Pt(10)

    # ── Pendientes para la docente ──
    pendientes_path = Path(__file__).resolve().parents[3] / "docs" / "contenido" / "PENDIENTES_CLAUDIA.md"
    if pendientes_path.exists():
        document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        document.add_heading("Pendientes para la docente", level=1)
        for line in pendientes_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                if stripped.startswith("## "):
                    document.add_heading(stripped[3:], level=2)
                continue
            paragraph = document.add_paragraph()
            add_inline_runs(paragraph, stripped)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return totals


def estado_for(topic: Topic) -> str:
    return ESTADO_BORRADOR if topic.order in BORRADOR_ORDERS else ESTADO_CARGADA


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path, help="Ruta del .docx de salida")
    parser.add_argument("--version", default="1.0")
    parser.add_argument(
        "--units",
        type=str,
        default="",
        help="Unidades a exportar, separadas por comas (p. ej. 6,7,8,9). Vacío = todas.",
    )
    args = parser.parse_args(argv)

    unit_numbers = (
        {int(n.strip()) for n in args.units.split(",") if n.strip()}
        if args.units.strip()
        else None
    )

    db = SessionLocal()
    try:
        totals = export(db, args.salida, version=args.version, unit_numbers=unit_numbers)
    finally:
        db.close()
    print(f"[export] LISTO: {args.salida}")
    for key, value in totals.items():
        print(f"  {key:12} {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
