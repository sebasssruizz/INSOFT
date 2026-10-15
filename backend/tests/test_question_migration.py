"""Tests de la migración de preguntas (source/status/created_by) y del filtro
de preguntas aprobadas para estudiantes.

Cubre:
- La migración agrega las columnas y es idempotente (correrla 2 veces).
- Las filas preexistentes quedan official/approved/created_by NULL.
- Un estudiante no ve preguntas pending/rejected en el quiz del subtema.
- El importador de Markdown no borra ni modifica preguntas teacher/ai.
"""
import os

os.environ["DEV_AUTH_ENABLED"] = "true"

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.session import SessionLocal
from app.main import app
from app.models.content import Question, Subtopic, Topic
from app.models.question_meta import QuestionSource, QuestionStatus


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # El lifespan ya corrió ensure_schema_compatibility + create_all + seed.
        yield c


def auth_headers(client: TestClient, email: str, name: str, role: str) -> dict:
    resp = client.post("/api/auth/dev", json={"email": email, "name": name, "role": role})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _any_subtopic_id() -> int:
    with SessionLocal() as s:
        return s.scalar(select(Subtopic).order_by(Subtopic.id).limit(1)).id


def test_migracion_columnas_existentes(client):
    """Tras el arranque, las columnas nuevas existen con defaults correctos."""
    with SessionLocal() as s:
        subtopic_id = _any_subtopic_id()
        q = Question(
            subtopic_id=subtopic_id,
            prompt="¿Migración aplica defaults?",
            options=["a", "b", "c", "d"],
            correct_index=0,
            explanation="sí",
            order=100,
        )
        s.add(q)
        s.commit()
        s.refresh(q)
        # El modelo aplica defaults de Python; el servidor los aplicó en DDL.
        assert q.source == QuestionSource.OFFICIAL
        assert q.status == QuestionStatus.APPROVED
        assert q.created_by is None


def test_migracion_idempotente(client):
    """Correr ensure_schema_compatibility dos veces no falla ni duplica índices."""
    from app.database.migrations import ensure_schema_compatibility

    ensure_schema_compatibility()
    ensure_schema_compatibility()

    from sqlalchemy import inspect

    from app.database.session import engine

    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("questions")}
    assert {"source", "status", "created_by"} <= cols
    idx = {i["name"] for i in inspector.get_indexes("questions")}
    assert "ix_questions_subtopic_status" in idx


def test_filas_preexistentes_quedan_official_approved(client):
    """Filas creadas por el seed quedan official/approved/created_by NULL."""
    with SessionLocal() as s:
        questions = s.scalars(select(Question).limit(5)).all()
        assert questions, "El seed debería haber creado preguntas oficiales"
        for q in questions:
            assert q.source == QuestionSource.OFFICIAL
            assert q.status == QuestionStatus.APPROVED
            assert q.created_by is None


def test_estudiante_no_ve_pending_ni_rejected(client):
    """El quiz del subtema solo lista approved; pending/rejected invisibles."""
    subtopic_id = _any_subtopic_id()
    with SessionLocal() as s:
        for i, status in enumerate([QuestionStatus.PENDING, QuestionStatus.REJECTED]):
            s.add(
                Question(
                    subtopic_id=subtopic_id,
                    prompt=f"Pregunta oculta {i} ({status})",
                    options=["a", "b", "c", "d"],
                    correct_index=0,
                    explanation="",
                    order=200 + i,
                    source=QuestionSource.AI,
                    status=status,
                )
            )
        approved_count = len(
            [
                q
                for q in s.scalars(select(Question).where(Question.subtopic_id == subtopic_id)).all()
                if q.status == QuestionStatus.APPROVED
            ]
        )
        assert approved_count > 0, "El seed debería dar al menos una aprobada"

    student = auth_headers(client, "qm-est@example.com", "QM Est", "STUDENT")
    # El curso General es el primero del estudiante
    courses = client.get("/api/courses", headers=student).json()
    general = next(c for c in courses if c["type"] == "GENERAL")
    resp = client.get(
        f"/api/subtopics/{subtopic_id}?course_id={general['id']}", headers=student
    )
    assert resp.status_code == 200, resp.text
    questions = resp.json()["questions"]
    assert all("Pregunta oculta" not in q["prompt"] for q in questions)
    assert all(q["prompt"] != "" for q in questions)
    assert len(questions) == approved_count


def test_importador_no_toca_preguntas_teacher_ni_ai(client):
    """Reimportar el documento no borra ni modifica teacher/ai del mismo subtema."""
    doc = (
        "# UNIDAD TEST MIGRACION. Unidad de prueba\n"
        "Descripción.\n\n"
        "## Subtema de prueba migración\n"
        "Contenido de prueba.\n\n"
        "### Preguntas\n"
        "1. **¿Pregunta oficial de prueba?**\n"
        "   - [ ] Incorrecta\n"
        "   - [x] Correcta\n"
        "   Explicación.\n"
    )

    teacher = auth_headers(client, "qm-profe@example.com", "QM Profe", "TEACHER")
    resp = client.post("/api/content/import", json={"document": doc}, headers=teacher)
    assert resp.status_code == 200, resp.text

    with SessionLocal() as s:
        subtopic = s.scalar(
            select(Subtopic).where(Subtopic.name == "Subtema de prueba migración")
        )
        assert subtopic is not None

        # Crea una pregunta teacher y una ai a mano en ese subtema.
        s.add(
            Question(
                subtopic=subtopic,
                prompt="¿Pregunta del profesor?",
                options=["a", "b", "c", "d"],
                correct_index=1,
                explanation="",
                order=50,
                source=QuestionSource.TEACHER,
                status=QuestionStatus.APPROVED,
            )
        )
        s.add(
            Question(
                subtopic=subtopic,
                prompt="¿Pregunta de la IA?",
                options=["a", "b", "c", "d"],
                correct_index=2,
                explanation="",
                order=51,
                source=QuestionSource.AI,
                status=QuestionStatus.PENDING,
            )
        )
        s.commit()
        teacher_q = s.scalar(select(Question).where(Question.prompt == "¿Pregunta del profesor?"))
        ai_q = s.scalar(select(Question).where(Question.prompt == "¿Pregunta de la IA?"))
        teacher_q_id, ai_q_id = teacher_q.id, ai_q.id
        subtopic_id = subtopic.id

    # Reimporta el mismo documento (sin esas preguntas)
    resp = client.post("/api/content/import", json={"document": doc}, headers=teacher)
    assert resp.status_code == 200, resp.text

    with SessionLocal() as s:
        teacher_q = s.get(Question, teacher_q_id)
        ai_q = s.get(Question, ai_q_id)
        assert teacher_q is not None, "El importador borró una pregunta teacher"
        assert teacher_q.prompt == "¿Pregunta del profesor?"
        assert teacher_q.options == ["a", "b", "c", "d"]
        assert teacher_q.correct_index == 1
        assert ai_q is not None, "El importador borró una pregunta ai"
        assert ai_q.status == QuestionStatus.PENDING

        # Las oficiales siguen siendo exactamente 1 (la del documento)
        officials = [
            q
            for q in s.scalars(select(Question).where(Question.subtopic_id == subtopic_id)).all()
            if q.source == QuestionSource.OFFICIAL
        ]
        assert len(officials) == 1


def test_reimportar_reordena_tras_oficiales(client):
    """Tras reimportar, las preguntas teacher/ai quedan con order después de las oficiales.

    Auto-contenido (orden-independiente): importa su propio documento, agrega
    teacher/ai a mano, reimporta y verifica el reordenamiento. Antes dependía
    del reimport realizado por test_importador_no_toca_preguntas_teacher_ni_ai.
    """
    doc = (
        "# UNIDAD TEST MIGRACION. Unidad de prueba\n"
        "Descripción.\n\n"
        "## Subtema de prueba reordena\n"
        "Contenido de prueba.\n\n"
        "### Preguntas\n"
        "1. **¿Pregunta oficial del reorden?**\n"
        "   - [ ] Incorrecta\n"
        "   - [x] Correcta\n"
        "   Explicación.\n"
    )
    teacher = auth_headers(client, "qm-profe2@example.com", "QM Profe 2", "TEACHER")
    resp = client.post("/api/content/import", json={"document": doc}, headers=teacher)
    assert resp.status_code == 200, resp.text

    with SessionLocal() as s:
        subtopic = s.scalar(select(Subtopic).where(Subtopic.name == "Subtema de prueba reordena"))
        assert subtopic is not None
        s.add(
            Question(
                subtopic=subtopic,
                prompt="¿Pregunta extra del reorden?",
                options=["a", "b", "c", "d"],
                correct_index=0,
                explanation="",
                order=200,
                source=QuestionSource.TEACHER,
                status=QuestionStatus.APPROVED,
            )
        )
        s.commit()

    # Reimporta: el importador debe empujar las no-oficiales después de las oficiales
    resp = client.post("/api/content/import", json={"document": doc}, headers=teacher)
    assert resp.status_code == 200, resp.text

    with SessionLocal() as s:
        subtopic = s.scalar(select(Subtopic).where(Subtopic.name == "Subtema de prueba reordena"))
        assert subtopic is not None
        questions = sorted(subtopic.questions, key=lambda q: q.order)
        officials = [q for q in questions if q.source == QuestionSource.OFFICIAL]
        extras = [q for q in questions if q.source != QuestionSource.OFFICIAL]
        assert officials and extras
        assert all(q.order < extras[0].order for q in officials)
