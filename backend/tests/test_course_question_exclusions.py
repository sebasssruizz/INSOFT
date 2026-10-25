"""Retirada por curso: conserva el banco compartido y las respuestas históricas."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.auth.jwt import create_access_token
from app.database.session import SessionLocal
from app.main import app
from app.models import Course, CourseMembership, CourseTopic, Question, QuestionAnswer, Subtopic, Topic, User, UserRole
from app.models.course_question_exclusion import CourseQuestionExclusion


@pytest.fixture
def scenario():
    key = uuid4().hex[:8]
    with SessionLocal() as db:
        users = [User(google_id=f'{key}-{i}', name=f'Demo {i}', email=f'{key}-{i}@example.com', role=role)
                 for i, role in enumerate([UserRole.TEACHER, UserRole.TEACHER, UserRole.STUDENT])]
        db.add_all(users)
        topic = Topic(name='Unidad de prueba', order=0)
        db.add(topic)
        db.flush()
        subtopic = Subtopic(topic_id=topic.id, name='Subtema de prueba', content='Contenido de prueba', order=0)
        db.add(subtopic)
        courses = [Course(name=f'Curso {i}', teacher_id=users[i].id) for i in range(2)]
        db.add_all(courses)
        db.flush()
        for course in courses:
            db.add(CourseTopic(course_id=course.id, topic_id=topic.id, order=0))
            db.add(CourseMembership(course_id=course.id, user_id=users[2].id))
        questions = [Question(subtopic_id=subtopic.id, prompt=f'Pregunta {i}', options=['A', 'B', 'C', 'D'],
                              correct_index=0, explanation='Explicación', order=i, source='official', status='approved')
                     for i in range(2)]
        db.add_all(questions)
        db.commit()
        data = dict(course=courses[0].id, other_course=courses[1].id,
                    subtopic=subtopic.id, topic=topic.id, question=questions[0].id,
                    remaining=questions[1].id)
        data['headers'] = [{'Authorization': f'Bearer {create_access_token(user.id, user.role.value)}'}
                           for user in users]
    return data


def test_retira_solo_del_curso_y_conserva_historial(scenario, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'PRACTICE_AI_RATIO', 0)
    s = scenario
    teacher, other_teacher, student = s['headers']
    client = TestClient(app)  # Sin lifespan: conftest ya creó la base aislada.
    answer = dict(question_id=s['question'], selected_index=1, attempt_id=str(uuid4()), course_id=s['course'])
    assert client.post('/api/quiz/answers', json=answer, headers=student).status_code == 200
    endpoint = f"/api/courses/{s['course']}/questions/{s['question']}"
    assert client.delete(endpoint, headers=teacher).status_code == 200
    assert client.delete(endpoint, headers=teacher).status_code == 200
    for course_id, headers, expected in [(s['course'], teacher, False), (s['other_course'], other_teacher, True)]:
        bank = client.get(f"/api/content/subtopics/{s['subtopic']}/questions/bank?course_id={course_id}", headers=headers)
        assert bank.status_code == 200
        assert (s['question'] in [q['id'] for q in bank.json()]) is expected
        for url in [f"/api/subtopics/{s['subtopic']}?course_id={course_id}",
                    f"/api/topics/{s['topic']}/questions?course_id={course_id}"]:
            result = client.get(url, headers=student)
            assert result.status_code == 200
            questions = result.json()['questions'] if isinstance(result.json(), dict) else result.json()
            assert (s['question'] in [q['id'] for q in questions]) is expected
        content = client.get(f'/api/courses/{course_id}/topics', headers=student).json()
        assert content[0]['subtopics'][0]['question_count'] == (2 if expected else 1)
        summary = client.get(f"/api/content/topics/{s['topic']}/questions/summary?course_id={course_id}", headers=headers).json()
        assert summary[0]['approved'] == (2 if expected else 1)
    assert client.post('/api/quiz/answers', json={**answer, 'attempt_id': str(uuid4())}, headers=student).status_code == 404
    assert client.post('/api/quiz/answers', json={**answer, 'course_id': s['other_course'], 'attempt_id': str(uuid4())}, headers=student).status_code == 200
    practice = client.post('/api/practice/sessions', json=dict(subtopic_id=s['subtopic'], course_id=s['course'], count=1), headers=student)
    assert practice.status_code == 200, practice.text
    assert [q['id'] for q in practice.json()['questions']] == [s['remaining']]
    with SessionLocal() as db:
        assert db.get(Question, s['question']) is not None
        assert db.scalar(select(func.count()).select_from(QuestionAnswer).where(QuestionAnswer.question_id == s['question'])) == 2
        assert db.get(CourseQuestionExclusion, (s['course'], s['question'])) is not None


def test_solo_el_docente_dueno_puede_retirar(scenario):
    s = scenario
    teacher, other_teacher, student = s['headers']
    client = TestClient(app)
    endpoint = f"/api/courses/{s['course']}/questions/{s['question']}"
    assert client.delete(endpoint).status_code == 401
    assert client.delete(endpoint, headers=student).status_code == 403
    assert client.delete(endpoint, headers=other_teacher).status_code == 403
    bank = f"/api/content/subtopics/{s['subtopic']}/questions/bank?course_id={s['course']}"
    assert client.get(bank, headers=other_teacher).status_code == 403
    with SessionLocal() as db:
        assert db.get(CourseQuestionExclusion, (s['course'], s['question'])) is None
