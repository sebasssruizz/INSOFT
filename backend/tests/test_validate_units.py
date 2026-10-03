"""Tests del validador de unidades (app.scripts.validate_units)."""
import pytest

from app.scripts.validate_units import validate_document

GOOD_DOC = """\
# UNIDAD 6. Corrección de estrabismo
Descripción.

## Técnicas para Corrección de estrabismo
{content}

### Preguntas
1. ¿Cuál de los siguientes es un grupo de técnicas de cirugía de estrabismo?
   - [ ] Cirugía de músculos horizontales
   - [ ] Cirugía de músculos verticales
   - [ ] Cirugía de músculos oblicuos
   - [x] Ninguna de las opciones
   En la fuente se agrupan en horizontales, verticales y oblicuos.
"""


def _content(words: int) -> str:
    return " ".join(f"palabra{i}" for i in range(words)) + "\n\nFuente: manual, p. 13."


@pytest.mark.parametrize(
    "words, min_words, ok",
    [(200, 715, False), (720, 715, True)],
)
def test_min_words(words, min_words, ok):
    doc = GOOD_DOC.format(content=_content(words))
    errors, _ = validate_document(doc, min_words=min_words, min_questions=1)
    has_words_error = any("palabras" in e for e in errors)
    assert has_words_error is not ok


def test_duplicate_options_and_prompts():
    doc = GOOD_DOC.format(content=_content(720)).replace(
        "Ninguna de las opciones", "Cirugía de músculos horizontales"
    ).replace(
        "1. ¿Cuál de los siguientes es un grupo de técnicas",
        "1. ¿Cuál de los siguientes es un grupo de técnicas",
    )
    # duplicar el enunciado con una segunda pregunta idéntica
    doc += "\n\n2. ¿Cuál de los siguientes es un grupo de técnicas de cirugía de estrabismo?\n" + "\n".join(
        ["   - [ ] a", "   - [ ] b", "   - [ ] c", "   - [x] d"]
    )
    errors, _ = validate_document(doc, min_words=0, min_questions=1)
    assert any("duplicado" in e for e in errors)


def test_exencion_preguntas_unidad_9():
    """Unidad exenta (default: 9) no exige mínimo de preguntas ni opciones."""
    doc = """\
# UNIDAD 9. Cirugía de Pterigión paso a paso
Descripción.

## Definición y generalidades
Contenido sin preguntas, solo texto.

## Complicaciones
Texto sin preguntas.
"""
    errors, _ = validate_document(doc, min_words=0, min_questions=3)
    assert not errors
    # Sin exención, sí falla.
    errors, _ = validate_document(
        doc, min_words=0, min_questions=3, exempt_questions_units=set()
    )
    assert any("preguntas" in e for e in errors)


def test_pending_claudia_not_error():
    doc = GOOD_DOC.format(content=_content(720) + "\n\n> [PENDIENTE CLAUDIA: falta X]")
    errors, pending = validate_document(doc, min_words=0, min_questions=1)
    assert not errors
    assert any("PENDIENTE CLAUDIA" in p for p in pending)


def test_empty_document():
    errors, _ = validate_document("hola mundo", min_words=0, min_questions=0)
    assert errors and "no contiene ninguna unidad" in errors[0]
