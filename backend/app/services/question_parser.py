"""Parser puro de preguntas generadas por el LLM.

Función testeable sin dependencias de red ni de la BD: limpia fences de
markdown, extrae el primer objeto JSON balanceado y valida cada pregunta
con las mismas reglas del formulario del profesor (4 opciones, correct_index
0-3, enunciado 5-500, explicación <=1000). Las preguntas inválidas se
descartan individualmente.
"""
from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError


class GeneratedQuestion(BaseModel):
    """Pregunta validada salida del LLM (antes de persistir)."""

    prompt: str
    options: list[str]
    correct_index: int
    explanation: str = ""


def _strip_markdown_fences(raw: str) -> str:
    """Quita cercos ```json ... ``` si el modelo los agrega."""
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        return fence.group(1)
    return raw


def _extract_first_json_object(raw: str) -> str | None:
    """Extrae el primer objeto JSON balanceado del texto (llaves contadas)."""
    start = raw.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(raw)):
        char = raw[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw[start : index + 1]
    return None


def _coerce_correct_index(value) -> int | None:
    """Acepta int o string de dígitos (los modelos suelen devolver strings).

    Decisión documentada: castear "2" → 2; cualquier otra cosa → inválida.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def parse_generated_questions(raw: str, expected_max: int) -> list[GeneratedQuestion]:
    """Parsea la respuesta del LLM y devuelve las preguntas válidas.

    - Quita fences de markdown y extrae el primer objeto JSON balanceado.
    - Descarta preguntas individuales inválidas (4 opciones no vacías y sin
      duplicados, correct_index 0-3, enunciado 5-500, explicación <=1000).
    - Recorta a `expected_max` si llegaron de más.
    """
    if not raw or not raw.strip():
        return []

    candidate = _extract_first_json_object(_strip_markdown_fences(raw))
    if candidate is None:
        return []
    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        return []

    valid: list[GeneratedQuestion] = []
    seen_prompts: set[str] = set()
    for item in data["questions"]:
        if not isinstance(item, dict) or len(valid) >= expected_max:
            break
        try:
            question = GeneratedQuestion(
                prompt=str(item.get("prompt", "")).strip(),
                options=[str(option).strip() for option in item.get("options", [])],
                correct_index=_coerce_correct_index(item.get("correct_index")),
                explanation=str(item.get("explanation", "")).strip(),
            )
        except (ValidationError, TypeError):
            continue

        # Reglas de negocio compartidas con el formulario del profesor.
        if not 5 <= len(question.prompt) <= 500:
            continue
        if len(question.options) != 4:
            continue
        if any(len(option) < 1 or len(option) > 300 for option in question.options):
            continue
        if len({option.casefold() for option in question.options}) != 4:
            continue
        if question.correct_index is None or not 0 <= question.correct_index <= 3:
            continue
        if len(question.explanation) > 1000:
            continue

        # Duplicados entre las propias preguntas generadas.
        key = re.sub(r"\s+", " ", question.prompt.strip().lower()).strip("¿?.!¡:;, ")
        if key in seen_prompts:
            continue
        seen_prompts.add(key)

        question.correct_index = int(question.correct_index)
        valid.append(question)

    return valid
