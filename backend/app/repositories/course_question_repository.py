from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.models.content import Question
from app.models.course_question_exclusion import CourseQuestionExclusion


def available_in_course(course_id: int | None):
    if course_id is None:
        return true()
    return Question.id.not_in(
        select(CourseQuestionExclusion.question_id).where(
            CourseQuestionExclusion.course_id == course_id
        )
    )


def excluded_ids(db: Session, course_id: int | None) -> set[int]:
    if course_id is None:
        return set()
    return set(db.scalars(select(CourseQuestionExclusion.question_id).where(
        CourseQuestionExclusion.course_id == course_id
    )))


def exclude(db: Session, course_id: int, question_id: int) -> None:
    if db.get(CourseQuestionExclusion, (course_id, question_id)) is None:
        db.add(CourseQuestionExclusion(course_id=course_id, question_id=question_id))
        db.commit()
