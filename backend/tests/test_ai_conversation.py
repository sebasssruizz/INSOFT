"""Memoria, contexto y valoración: API real, SQLite y proveedor/embeddings simulados."""
import os
from uuid import uuid4
from unittest.mock import AsyncMock

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DEV_AUTH_ENABLED"] = "true"
os.environ["AI_ASK_RATE_LIMIT"] = "1000/hour"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.ai_query import AiQuery
from app.models.content import CourseTopic, Topic, Subtopic
from app.models.subtopic_chunk import SubtopicChunk
from app.services import ai_service


def login(client, email, role="STUDENT"):
    response = client.post("/api/auth/dev", json={"email": email, "name": email, "role": role})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def study(client):
    teacher = login(client, "memory-teacher@example.com", "TEACHER")
    response = client.post("/api/courses", headers=teacher, json={"name": "Curso de memoria"})
    assert response.status_code == 201, response.text
    course = response.json()
    student = login(client, "memory-student@example.com")
    joined = client.post("/api/courses/join", headers=student, json={"code": course["code"]})
    assert joined.status_code == 200, joined.text
    with SessionLocal() as db:
        topic = Topic(name="UNIDAD 20. Pterigión", order=20)
        other_topic = Topic(name="UNIDAD 21. Glaucoma", order=21)
        db.add_all([topic, other_topic])
        db.flush()
        subtopic = Subtopic(topic_id=topic.id, name="Instrumentación del pterigión", content="### Instrumental\nSe utiliza **Westcott** para disección.\n\n### Cuidados\nEvitar traumatismos.")
        other = Subtopic(topic_id=other_topic.id, name="Glaucoma", content="Contenido ajeno a la unidad.")
        db.add_all([subtopic, other])
        db.flush()
        for item in (topic, other_topic):
            db.add(CourseTopic(course_id=course["id"], topic_id=item.id, enabled=True))
        for i in range(8):
            db.add(SubtopicChunk(subtopic_id=subtopic.id, content=f"Sección {i}: instrumental Westcott y cuidados del pterigión.", embedding=[1.0] * 384))
        db.add(SubtopicChunk(subtopic_id=other.id, content="SOLO_GLAUCOMA", embedding=[1.0] * 384))
        db.commit()
        return {"teacher": teacher, "student": student, "course_id": course["id"], "subtopic_id": subtopic.id,
                "topic_id": topic.id, "other_id": other.id, "other_topic_id": other_topic.id}


@pytest.fixture(autouse=True)
def provider(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "AI_DAILY_LIMIT_PER_USER", 0)
    monkeypatch.setattr(ai_service, "embed_text", lambda text: [1.0] * 384)
    llm = AsyncMock(return_value="Se utilizan tijeras Westcott [1].")
    monkeypatch.setattr(ai_service, "call_gemini", llm)
    return llm


def ask(client, study, question, **extra):
    return client.post("/api/ai/ask", headers=study["student"], json={
        "question": question, "course_id": study["course_id"], "subtopic_id": study["subtopic_id"], **extra,
    })


def test_follow_up_uses_history_and_verified_page(client, study, provider):
    session = str(uuid4())
    first = ask(client, study, "¿Para qué sirve Westcott?", session_id=session)
    assert first.status_code == 200, first.text
    response = ask(client, study, "¿Y qué cuidados debo tener?", session_id=session)
    assert response.status_code == 200, response.text
    prompt = provider.await_args.kwargs["user_content"]
    assert "Instrumentación del pterigión" in prompt
    assert "¿Para qué sirve Westcott?" in prompt
    assert "Se utilizan tijeras Westcott" in prompt
    assert response.json()["session_id"] == session
    assert response.json()["sources"][0]["subtopic_id"] == study["subtopic_id"]
    history = client.get(f"/api/ai/history?session_id={session}", headers=study["student"])
    assert len(history.json()) == 2


def test_new_conversation_and_other_user_have_no_previous_history(client, study, provider):
    session = str(uuid4())
    ask(client, study, "MARCADOR_PRIVADO", session_id=session)
    other = login(client, "memory-other@example.com")
    assert client.get(f"/api/ai/history?session_id={session}", headers=other).json() == []
    response = client.post("/api/ai/ask", headers=other, json={"question": "¿Qué es el ojo?", "session_id": session})
    assert response.status_code == 200, response.text
    assert "MARCADOR_PRIVADO" not in provider.await_args.kwargs["user_content"]
    ask(client, study, "Nueva pregunta", session_id=str(uuid4()))
    assert "MARCADOR_PRIVADO" not in provider.await_args.kwargs["user_content"]


def test_unit_scope_excludes_other_units_and_summary_has_more_coverage(client, study, provider):
    response = ask(client, study, "Resúmeme lo que estoy viendo", subtopic_id=None, topic_id=study["topic_id"])
    assert response.status_code == 200, response.text
    assert response.json()["chunks_usados"] == 6
    assert "SOLO_GLAUCOMA" not in provider.await_args.kwargs["user_content"]


def test_navigation_updates_location_but_keeps_conversation(client, study, provider):
    session = str(uuid4())
    ask(client, study, "Pregunta sobre pterigión", session_id=session)
    response = ask(client, study, "Explícame esto", session_id=session, subtopic_id=study["other_id"])
    assert response.status_code == 200, response.text
    prompt = provider.await_args.kwargs["user_content"]
    location, rest = prompt.split("HISTORIAL", 1)
    assert "Glaucoma" in location and "Instrumentación del pterigión" not in location
    assert "Pregunta sobre pterigión" in rest
    assert response.json()["sources"][0]["subtopic_id"] == study["other_id"]


def test_selection_is_grounded_and_forged_selection_is_rejected(client, study, provider):
    response = ask(client, study, "Explícame este fragmento", selected_text="Se utiliza Westcott para disección.")
    assert response.status_code == 200, response.text
    assert "fragmento seleccionado" in response.json()["sources"][0]["title"]
    provider.reset_mock()
    invalid = ask(client, study, "Explícame esto", selected_text="Texto que no está en el material")
    assert invalid.status_code == 403
    provider.assert_not_awaited()


def test_mismatched_unit_is_rejected_before_provider(client, study, provider):
    response = ask(client, study, "Explícame esto", topic_id=study["other_topic_id"])
    assert response.status_code == 403
    provider.assert_not_awaited()


def test_feedback_can_be_updated_and_teacher_can_filter(client, study):
    response = ask(client, study, "Pregunta para valorar")
    query_id = response.json()["query_id"]
    url = f"/api/ai/answers/{query_id}/feedback"
    feedback = client.put(url, headers=study["student"], json={"helpful": False, "reason": "context", "comment": "No entendió mi pregunta"})
    assert feedback.status_code == 200, feedback.text
    review = client.get("/api/ai/history/all?feedback_only=true&feedback_reason=context", headers=study["teacher"])
    assert query_id in [row["id"] for row in review.json()]
    updated = client.put(url, headers=study["student"], json={"helpful": True})
    assert updated.json()["feedback"] == {"helpful": True, "reason": None, "comment": None}
    other = login(client, "memory-feedback-other@example.com")
    assert client.put(url, headers=other, json={"helpful": False}).status_code == 404
    other_teacher = login(client, "memory-other-teacher@example.com", "TEACHER")
    assert client.get("/api/ai/history/all", headers=other_teacher).json() == []


def test_memory_bounded_and_scoped_to_course(client, study, provider):
    session = uuid4()
    response = ask(client, study, "Primera", session_id=str(session))
    with SessionLocal() as db:
        user_id = db.get(AiQuery, response.json()["query_id"]).user_id
        for i in range(8):
            db.add(AiQuery(user_id=user_id, session_id=session, course_id=study["course_id"], subtopic_id=study["subtopic_id"],
                           question_original=f"MEMORIA_{i}", respuesta="respuesta", status="ok"))
        db.add(AiQuery(user_id=user_id, session_id=session, course_id=None,
                       question_original="OTRO_CURSO_PRIVADO", respuesta="respuesta", status="ok"))
        db.commit()
    ask(client, study, "¿Y ahora?", session_id=str(session))
    prompt = provider.await_args.kwargs["user_content"]
    assert "MEMORIA_7" in prompt and "MEMORIA_0" not in prompt
    assert "OTRO_CURSO_PRIVADO" not in prompt


def test_provider_failure_keeps_degraded_response(client, study, provider):
    provider.side_effect = ai_service.GeminiCallError("Sin conexión")
    response = ask(client, study, "¿Qué instrumental necesito?")
    assert response.status_code == 200, response.text
    assert response.json()["degraded"] is True
    assert response.json()["query_id"]


def test_whitespace_question_is_invalid(client, study, provider):
    assert ask(client, study, "   ").status_code == 422
    provider.assert_not_awaited()


def test_openrouter_also_receives_conversation(client, study, monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    llm = AsyncMock(side_effect=["Westcott", "Respuesta inicial", "Cuidados de Westcott", "Respuesta final"])
    monkeypatch.setattr(ai_service, "call_openrouter", llm)
    session = str(uuid4())
    assert ask(client, study, "¿Para qué sirve Westcott?", session_id=session).status_code == 200
    assert ask(client, study, "¿Y sus cuidados?", session_id=session).status_code == 200
    prompt = llm.await_args.kwargs["user_content"]
    assert "Respuesta inicial" in prompt
    assert "Instrumentación del pterigión" in prompt


def test_hidden_content_is_not_reintroduced_by_memory(client, study, provider):
    session = str(uuid4())
    assert ask(client, study, "MARCADOR_DESHABILITADO", session_id=session).status_code == 200
    with SessionLocal() as db:
        link = db.scalar(select(CourseTopic).where(CourseTopic.course_id == study["course_id"], CourseTopic.topic_id == study["topic_id"]))
        link.enabled = False
        db.commit()
    try:
        response = ask(client, study, "Explícame esto", session_id=session, subtopic_id=study["other_id"])
        assert response.status_code == 200, response.text
        assert "MARCADOR_DESHABILITADO" not in provider.await_args.kwargs["user_content"]
    finally:
        with SessionLocal() as db:
            link = db.scalar(select(CourseTopic).where(CourseTopic.course_id == study["course_id"], CourseTopic.topic_id == study["topic_id"]))
            link.enabled = True
            db.commit()


def test_unindexed_lesson_still_supplies_authoritative_context(client, study, provider):
    with SessionLocal() as db:
        subtopic = Subtopic(topic_id=study["topic_id"], name="Lección nueva", content="Se utiliza una pinza Castroviejo para la fijación.")
        db.add(subtopic)
        db.commit()
        subtopic_id = subtopic.id
    response = ask(client, study, "Explícame esto", subtopic_id=subtopic_id)
    assert response.status_code == 200, response.text
    assert "Castroviejo" in provider.await_args.kwargs["user_content"]
    assert response.json()["sources"][0]["subtopic_id"] == subtopic_id


def test_course_question_gets_syllabus_even_when_retrieval_is_empty(client, study, provider, monkeypatch):
    monkeypatch.setattr(ai_service, "_retrieve_chunks", AsyncMock(return_value=[]))
    response = ask(client, study, "¿Qué voy a aprender en el curso?", subtopic_id=None)
    assert response.status_code == 200, response.text
    prompt = provider.await_args.kwargs['user_content']
    assert 'TEMARIO' in prompt and 'Curso de memoria' in prompt
    assert 'Instrumentación del pterigión' in prompt
    assert '(sin contexto disponible)' not in prompt
    assert response.json()['sources'][0]['course_id'] == study['course_id']


def test_dashboard_question_gets_accessible_course_syllabus(client, provider, monkeypatch):
    monkeypatch.setattr(ai_service, "_retrieve_chunks", AsyncMock(return_value=[]))
    student = login(client, 'dashboard-syllabus@example.com')
    response = client.post('/api/ai/ask', headers=student, json={'question': '¿Qué voy a aprender en el curso?'})
    assert response.status_code == 200, response.text
    prompt = provider.await_args.kwargs['user_content']
    assert 'Curso General de Oftalmología' in prompt
    assert 'TEMARIO' in prompt
    assert 'Curso de memoria' not in prompt
    assert response.json()['sources']


@pytest.mark.parametrize('scope', ['course', 'unit', 'global'])
def test_empty_index_recovers_official_text_for_every_scope(client, study, provider, monkeypatch, scope):
    from app.repositories import subtopic_chunk_repository as chunks
    monkeypatch.setattr(chunks, 'list_chunks_for_course', lambda *args: [])
    monkeypatch.setattr(chunks, 'list_chunks_for_course_ids', lambda *args: [])
    response = ask(client, study, '¿Para qué sirve Westcott?', subtopic_id=None,
                   course_id=None if scope == 'global' else study['course_id'],
                   topic_id=study['topic_id'] if scope == 'unit' else None)
    assert response.status_code == 200, response.text
    assert response.json()['chunks_usados'] > 0
    prompt = provider.await_args.kwargs['user_content']
    context = prompt.split('CONTEXTO:\n', 1)[1].split('\n\nPREGUNTA DEL ESTUDIANTE:', 1)[0]
    assert 'westcott' in context.lower()
    if scope == 'unit':
        assert 'Contenido ajeno a la unidad' not in prompt


def test_syllabus_does_not_include_disabled_units(client, study, provider, monkeypatch):
    monkeypatch.setattr(ai_service, "_retrieve_chunks", AsyncMock(return_value=[]))
    with SessionLocal() as db:
        link = db.scalar(select(CourseTopic).where(CourseTopic.course_id == study['course_id'], CourseTopic.topic_id == study['other_topic_id']))
        link.enabled = False
        db.commit()
    try:
        response = ask(client, study, '¿Qué voy a aprender en el curso?', subtopic_id=None)
        assert response.status_code == 200, response.text
        assert 'UNIDAD 21. Glaucoma' not in provider.await_args.kwargs['user_content']
    finally:
        with SessionLocal() as db:
            link = db.scalar(select(CourseTopic).where(CourseTopic.course_id == study['course_id'], CourseTopic.topic_id == study['other_topic_id']))
            link.enabled = True
            db.commit()
