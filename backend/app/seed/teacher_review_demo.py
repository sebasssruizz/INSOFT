"""Cursos de evaluación con datos ficticios, activados solo por configuración privada."""
import random
from datetime import datetime, timedelta, timezone
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Course, CourseMembership, CourseTopic, CourseType, Progress
from app.models import Question, QuestionAnswer, Subtopic, Topic, User, UserRole


def seed_teacher_review_demo(db: Session) -> dict:
    emails = list(dict.fromkeys(
        email.strip().lower() for email in settings.REVIEW_DEMO_TEACHER_EMAILS.split(",")
        if email.strip()
    ))
    if not emails:
        return {"courses": 0}
    if not set(emails) <= set(settings.teacher_emails):
        raise ValueError("Los docentes de demostración deben estar autorizados previamente.")
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7142002)"))

    new_courses = []
    for email in emails:
        teacher = db.scalar(select(User).where(User.email == email))
        if teacher is None:
            teacher = User(google_id=f"review-demo:{uuid4()}", email=email,
                           name="Docente", role=UserRole.TEACHER)
            db.add(teacher)
            db.flush()
        else:
            teacher.role = UserRole.TEACHER
        course = db.scalar(select(Course).where(
            Course.teacher_id == teacher.id, Course.code.like("DEMO-%")
        ))
        if course is None:
            course = Course(
                teacher_id=teacher.id, type=CourseType.TEACHER,
                code=f"DEMO-{uuid4().hex[:8].upper()}",
                name="Demostración · 5 estudiantes de prueba",
                description="Curso con estudiantes ficticios y respuestas simuladas para evaluar INSOFT. No son resultados académicos reales.",
            )
            db.add(course)
            db.flush()
            new_courses.append(course)
    if not new_courses:
        db.commit()
        return {"teachers": len(emails), "new_courses": 0}

    topics = list(db.scalars(select(Topic).order_by(Topic.order, Topic.id)))
    subtopics = list(db.scalars(select(Subtopic).join(Topic).order_by(
        Topic.order, Topic.id, Subtopic.order, Subtopic.id
    )))
    questions = list(db.scalars(select(Question).where(
        Question.source == "official", Question.status == "approved"
    ).order_by(Question.order, Question.id)))
    by_subtopic = {}
    for question in questions:
        by_subtopic.setdefault(question.subtopic_id, []).append(question)
    if not topics:
        raise ValueError("Falta contenido oficial para preparar la demostración.")
    first = [subtopic for subtopic in subtopics if subtopic.topic_id == topics[0].id][:3]
    if len(first) != 3 or any(subtopic.id not in by_subtopic for subtopic in first):
        raise ValueError("Se requieren los tres primeros cuestionarios oficiales.")
    others = [subtopic for subtopic in subtopics if subtopic not in first and subtopic.id in by_subtopic]
    for course in new_courses:
        for topic in topics:
            db.add(CourseTopic(course_id=course.id, topic_id=topic.id, order=topic.order))

    rng = random.Random(20261025)
    answer_count = attempt_count = 0
    for number in range(1, 6):
        email = f"insoft-review-student-{number}@example.com"
        student = db.scalar(select(User).where(User.email == email))
        if student is None:
            student = User(google_id=f"review-demo:student:{number}", email=email,
                           name=f"Estudiante de prueba {number}", role=UserRole.STUDENT)
            db.add(student)
            db.flush()
        existing_answers = set(db.execute(select(
            QuestionAnswer.attempt_id, QuestionAnswer.question_id
        ).where(QuestionAnswer.user_id == student.id)).all())
        chosen = first + rng.sample(others, min(rng.randint(2, 6), len(others)))
        for course in new_courses:
            db.add(CourseMembership(course_id=course.id, user_id=student.id))
        for subtopic in chosen:
            attempt = str(uuid5(NAMESPACE_URL, f"insoft-review:{email}:{subtopic.id}"))
            answered_at = datetime.now(timezone.utc) - timedelta(days=rng.randint(0, 6))
            attempt_count += 1
            for question in by_subtopic[subtopic.id]:
                selected = rng.randrange(len(question.options))
                if (attempt, question.id) not in existing_answers:
                    db.add(QuestionAnswer(
                        user_id=student.id, question_id=question.id, subtopic_id=subtopic.id,
                        attempt_id=attempt, selected_index=selected,
                        is_correct=selected == question.correct_index, answered_at=answered_at,
                    ))
                    answer_count += 1
            for course in new_courses:
                db.add(Progress(user_id=student.id, course_id=course.id,
                                subtopic_id=subtopic.id, completed=True, updated_at=answered_at))
    db.commit()
    return {"teachers": len(emails), "new_courses": len(new_courses),
            "students": 5, "attempts": attempt_count, "new_answers": answer_count}
