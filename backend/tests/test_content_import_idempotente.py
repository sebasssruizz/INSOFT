"""Importación idempotente del documento de unidades 6–8.

Verifica contra la BD de pruebas que correr el importador dos veces no
duplique unidades, subtemas ni preguntas, y que el RAG quede indexado.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.main import app
from app.database.session import SessionLocal
from app.models.content import Topic, Subtopic, Question
from app.models.subtopic_chunk import SubtopicChunk

DOC = """\
# UNIDAD 6. Corrección de estrabismo
Prueba de importación.

## Técnicas para Corrección de estrabismo
Contenido de prueba extenso. """ + " ".join(f"palabra{i}" for i in range(750)) + """

### Preguntas
1. ¿Primera pregunta de prueba?
   - [ ] Uno
   - [x] Dos
   - [ ] Tres
   - [ ] Cuatro
   Explicación de la primera.
2. ¿Segunda pregunta de prueba?
   - [x] Uno
   - [ ] Dos
   - [ ] Tres
   - [ ] Cuatro
   Explicación de la segunda.
"""


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _import() -> dict:
    from app.services.content_import import import_document
    db = SessionLocal()
    try:
        return import_document(db, DOC)
    finally:
        db.close()


def _counts() -> tuple[int, int, int, int]:
    db = SessionLocal()
    try:
        topics = db.scalar(select(func.count(Topic.id)).where(Topic.name == "UNIDAD 6. Corrección de estrabismo"))
        subtopics = db.scalar(
            select(func.count(Subtopic.id)).where(Subtopic.name == "Técnicas para Corrección de estrabismo")
        )
        questions = db.scalar(
            select(func.count(Question.id))
            .join(Subtopic, Question.subtopic_id == Subtopic.id)
            .where(Subtopic.name == "Técnicas para Corrección de estrabismo", Question.source == "official")
        )
        chunks = db.scalar(
            select(func.count(SubtopicChunk.id))
            .join(Subtopic, SubtopicChunk.subtopic_id == Subtopic.id)
            .where(Subtopic.name == "Técnicas para Corrección de estrabismo")
        )
        return topics, subtopics, questions, chunks
    finally:
        db.close()


def test_import_idempotente(client: TestClient):
    # El lifespan del TestClient ya corrió el seed oficial (6 preguntas para
    # este subtema). Baseline ANTES de importar:
    _, _, q0, _ = _counts()
    assert q0 > 0

    _import()
    t1, s1, q1, c1 = _counts()
    assert (t1, s1) == (1, 1)
    # no destructivo: conserva las preguntas oficiales del seed y no agrega
    # las que no superan las existentes por posición
    assert q1 == q0
    assert c1 > 0

    _import()  # segunda pasada: no duplica
    t2, s2, q2, c2 = _counts()
    assert (t2, s2, q2) == (t1, s1, q1)
    assert c2 == c1
