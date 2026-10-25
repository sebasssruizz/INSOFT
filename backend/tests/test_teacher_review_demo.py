from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.database.session import SessionLocal
from app.models import Course, CourseMembership, Question, QuestionAnswer, Subtopic, Topic, User, UserRole
from app.seed.teacher_review_demo import seed_teacher_review_demo
from app.services.auth_service import authenticate_with_google


def test_demo_idempotente_con_dos_docentes_y_cinco_estudiantes(monkeypatch):
    key = uuid4().hex[:8]
    emails = [f'{key}-new@example.com', f'{key}-existing@example.com']
    monkeypatch.setattr(settings, 'TEACHER_EMAILS', ','.join(emails))
    monkeypatch.setattr(settings, 'REVIEW_DEMO_TEACHER_EMAILS', ','.join(emails))
    with SessionLocal() as db:
        existing = User(name='Nombre existente', email=emails[1], google_id=f'old-{key}', role=UserRole.STUDENT)
        db.add(existing)
        topic = Topic(name='Unidad demo', order=0)
        db.add(topic)
        db.flush()
        for index in range(5):
            subtopic = Subtopic(topic_id=topic.id, name=f'Subtema {index}', content='Contenido', order=index)
            db.add(subtopic)
            db.flush()
            for number in range(3):
                db.add(Question(subtopic_id=subtopic.id, prompt=f'Pregunta {index}-{number}',
                                options=['A','B','C','D'], correct_index=number % 4,
                                explanation='Explicación', source='official', status='approved'))
        db.commit()
        result = seed_teacher_review_demo(db)
        assert result['new_courses'] == 2
        assert existing.role == UserRole.TEACHER
        assert existing.name == 'Nombre existente'
        courses = list(db.scalars(select(Course)))
        assert len(courses) == 2
        for course in courses:
            assert db.scalar(select(func.count()).select_from(CourseMembership).where(CourseMembership.course_id == course.id)) == 5
        before = db.scalar(select(func.count()).select_from(QuestionAnswer))
        assert before >= 45
        assert seed_teacher_review_demo(db)['new_courses'] == 0
        assert db.scalar(select(func.count()).select_from(QuestionAnswer)) == before
        new_teacher = db.scalar(select(User).where(User.email == emails[0]))
        monkeypatch.setattr('app.services.auth_service.google_auth.verify_google_credential', lambda _: {
            'google_id': f'verified-{key}', 'email': emails[0], 'name': 'Docente verificado', 'profile_image': None,
        })
        logged_in = authenticate_with_google(db, 'mocked-id-token')
        assert logged_in.id == new_teacher.id
        assert logged_in.name == 'Docente verificado'
        assert logged_in.role == UserRole.TEACHER


def test_no_crea_demo_sin_autorizacion(monkeypatch):
    monkeypatch.setattr(settings, 'REVIEW_DEMO_TEACHER_EMAILS', 'unauthorized@example.com')
    monkeypatch.setattr(settings, 'TEACHER_EMAILS', '')
    with SessionLocal() as db, pytest.raises(ValueError):
        seed_teacher_review_demo(db)
