"""Tests del indexado de contenido (app.seed.index_content).

Usan SQLite en memoria de fichero temporal y el modelo local de embeddings
(ya cacheado), de modo que no requieren PostgreSQL ni credenciales.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/opencode/index_content_test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["TEACHER_EMAILS"] = ""

import pytest
from sqlalchemy import select

import app.models  # noqa: F401 - registra todos los modelos en la metadata
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.content import Subtopic, Topic
from app.models.subtopic_chunk import SubtopicChunk
from app.repositories import subtopic_chunk_repository as chunk_repo
from app.seed.index_content import chunk_subtopic_content, index_all_content


@pytest.fixture(scope="module")
def db():
    if os.path.exists("/tmp/opencode/index_content_test.db"):
        os.remove("/tmp/opencode/index_content_test.db")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        yield session


def _paragraph(words: int) -> str:
    return " ".join(f"palabra{i}" for i in range(words))


def _create_subtopic(db, name: str, content: str) -> Subtopic:
    topic = Topic(name=f"Tema {name}", description="desc", order=1)
    db.add(topic)
    db.flush()
    subtopic = Subtopic(topic_id=topic.id, name=name, content=content, order=1)
    db.add(subtopic)
    db.commit()
    return subtopic


def test_chunk_subtopic_content_agrupa_parrafos_completos():
    # 5 párrafos de 120 palabras: caben 2 por chunk (240) -> 2+2+1 = 3 chunks.
    content = "\n\n".join(_paragraph(120) for _ in range(5))
    chunks = chunk_subtopic_content(content)
    assert len(chunks) == 3
    assert all(1 <= len(c.split()) <= 300 for c in chunks)


def test_chunk_subtopic_content_corto_devuelve_un_solo_chunk():
    content = "La córnea es la ventana transparente del ojo. " * 5
    assert chunk_subtopic_content(content) == [content.strip()]


def test_indexar_dos_veces_no_duplica_chunks(db):
    subtopic = _create_subtopic(db, "Subtema idempotente", _paragraph(150))
    assert chunk_repo.list_chunks_for_subtopic(db, subtopic.id) == []

    index_all_content(db)
    tras_primera = chunk_repo.list_chunks_for_subtopic(db, subtopic.id)
    count1 = len(tras_primera)

    index_all_content(db)
    count2 = len(chunk_repo.list_chunks_for_subtopic(db, subtopic.id))

    assert count1 == count2 > 0


def test_cada_chunk_insertado_tiene_embedding_384(db):
    subtopic = _create_subtopic(db, "Subtema embeddings", _paragraph(150))
    index_all_content(db)

    chunks = chunk_repo.list_chunks_for_subtopic(db, subtopic.id)
    assert chunks
    for chunk in chunks:
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 384