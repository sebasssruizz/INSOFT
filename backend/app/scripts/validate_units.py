"""Validador de calidad para documentos de unidades antes de importarlos.

Uso:

    python -m app.scripts.validate_units ../docs/importacion/units_v2/unidad6.md ...

Comprueba, para cada subtema del documento:
- mínimo de palabras (default 715, -25% de la mediana de las unidades 1–5);
- al menos 3 preguntas oficiales;
- cada pregunta con exactamente 4 opciones únicas y no vacías, y
  `correct_index` en 0..3 con explicación no vacía;
- sin preguntas duplicadas (mismo enunciado) dentro del subtema;
- sin marcadores TODO/XXX;
- lista (sin bloquear) las marcas [PENDIENTE CLAUDIA].

Devuelve el código 1 si hay errores de calidad (no por los PENDIENTE CLAUDIA).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from app.services.content_import import parse_document

MIN_WORDS_DEFAULT = 715
MIN_QUESTIONS_DEFAULT = 3
N_OPTIONS = 4


def validate_topic(topic: dict, *, min_words: int, min_questions: int) -> list[str]:
    errors: list[str] = []
    for subtopic in topic["subtopics"]:
        name = subtopic["name"]
        words = len(subtopic["content"].split())
        if words < min_words:
            errors.append(
                f"{name}: subtema con {words} palabras (< {min_words})"
            )
        questions = subtopic["questions"]
        if len(questions) < min_questions:
            errors.append(
                f"{name}: {len(questions)} preguntas (< {min_questions})"
            )
        seen_prompts: set[str] = set()
        for i, q in enumerate(questions, 1):
            options = [str(o).strip() for o in q["options"]]
            if len(options) != N_OPTIONS:
                errors.append(f"{name} · P{i}: {len(options)} opciones (deben ser {N_OPTIONS})")
            if any(not o for o in options):
                errors.append(f"{name} · P{i}: opciones vacías")
            if len({o.lower() for o in options}) != len(options):
                errors.append(f"{name} · P{i}: opciones duplicadas")
            ci = q["correct_index"]
            if not (0 <= ci < len(options)):
                errors.append(f"{name} · P{i}: correct_index {ci} fuera de rango")
            if not str(q.get("explanation", "")).strip():
                errors.append(f"{name} · P{i}: sin explicación")
            prompt_key = q["prompt"].strip().lower()
            if prompt_key in seen_prompts:
                errors.append(f"{name} · P{i}: enunciado duplicado")
            seen_prompts.add(prompt_key)
    return errors


def validate_document(text: str, *, min_words: int, min_questions: int) -> tuple[list[str], list[str]]:
    """Devuelve (errores, pendientes). Los PENDIENTE CLAUDIA no son errores."""
    errors: list[str] = []
    pending: list[str] = []
    topics = parse_document(text)
    if not topics:
        return ["El documento no contiene ninguna unidad (`# UNIDAD N. …`)"], []
    for topic in topics:
        if "TODO" in topic["name"] or "XXX" in topic["name"]:
            errors.append(f"Título de unidad con marcador TODO/XXX: {topic['name']}")
        errors.extend(validate_topic(topic, min_words=min_words, min_questions=min_questions))
        for subtopic in topic["subtopics"]:
            full_text = subtopic["content"] + "\n" + "\n".join(
                q["prompt"] + " " + " ".join(q["options"]) + " " + str(q.get("explanation", ""))
                for q in subtopic["questions"]
            )
            if re.search(r"\b(TODO|XXX)\b", full_text):
                errors.append(f"{subtopic['name']}: contiene marcador TODO/XXX")
            for line in full_text.splitlines():
                if "PENDIENTE CLAUDIA" in line:
                    pending.append(f"{subtopic['name']}: {line.strip()}")
    return errors, pending


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivos", type=Path, nargs="+", help="Documentos .md de unidades")
    parser.add_argument("--min-words", type=int, default=MIN_WORDS_DEFAULT)
    parser.add_argument("--min-questions", type=int, default=MIN_QUESTIONS_DEFAULT)
    args = parser.parse_args(argv)

    ok = True
    for path in args.archivos:
        if not path.exists():
            print(f"[validate] ERROR: no existe {path}", file=sys.stderr)
            ok = False
            continue
        text = path.read_text(encoding="utf-8")
        errors, pending = validate_document(
            text, min_words=args.min_words, min_questions=args.min_questions
        )
        print(f"[validate] {path.name}: {len(errors)} errores, {len(pending)} pendientes")
        for error in errors:
            print(f"  ERROR: {error}")
            ok = False
        for item in pending:
            print(f"  PENDIENTE CLAUDIA: {item}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
