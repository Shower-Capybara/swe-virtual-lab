from sqlalchemy import Float, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import (
    QuizQuestionOption,
    QuizSubmission,
    QuizSubmissionAnswer,
    User,
)
from server.db.utils import json_build_object

from .schemas import StudentStats


async def get_student_stats(
    db_session: AsyncSession,
    success_threshold: float = 0.2,
) -> StudentStats:
    correct_answers_per_submission = (
        select(
            QuizSubmission.user_id,
            func.sum(
                case(
                    (QuizQuestionOption.is_correct.is_(True), 1),
                    else_=0,
                )
            ).label("correct_count"),
            func.count(QuizQuestionOption.id).label("total_count"),
        )
        .join(User, QuizSubmission.user_id == User.id)
        .join(
            QuizSubmissionAnswer,
            QuizSubmission.id == QuizSubmissionAnswer.submission_id,
        )
        .join(
            QuizQuestionOption,
            QuizSubmissionAnswer.selected_option_id == QuizQuestionOption.id,
        )
        .group_by(QuizSubmission.user_id, QuizSubmission.id)
        .subquery()
    )

    top_students = (
        select(
            correct_answers_per_submission.c.user_id,
            func.count().label("total_submissions"),
            func.count()
            .filter(
                (
                    correct_answers_per_submission.c.correct_count.cast(Float)
                    / correct_answers_per_submission.c.total_count.cast(Float)
                )
                > success_threshold
            )
            .label("successful_submissions"),
        )
        .group_by(correct_answers_per_submission.c.user_id)
        .order_by(desc("successful_submissions"))
        .limit(3)
        .subquery()
    )

    query = select(
        (
            select(func.count(func.distinct(QuizSubmission.user_id)))
            .scalar_subquery()
            .label("total_students")
        ),
        (
            select(
                func.array_agg(
                    json_build_object(
                        {
                            "id": User.id,
                            "username": User.username,
                            "name": User.name,
                            "successful_submissions": top_students.c.successful_submissions,
                            "total_submissions": top_students.c.total_submissions,
                        }
                    )
                )
            )
            .select_from(top_students)
            .join(User, User.id == top_students.c.user_id)
            .scalar_subquery()
            .label("top_students")
        ),
    )

    result = await db_session.execute(query)
    return StudentStats.model_validate(result.mappings().one())
