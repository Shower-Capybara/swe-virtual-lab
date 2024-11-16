from sqlalchemy import Float, case, cast, func, select, sql
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import (
    Quiz,
    QuizQuestionOption,
    QuizSubmission,
    QuizSubmissionAnswer,
)

from .schemas import QuizStats


async def get_quiz_stats(
    db_session: AsyncSession,
    success_threshold: float = 0.2,
) -> QuizStats:
    quiz_question_answers = (
        select(
            QuizSubmissionAnswer.submission_id,
            (
                func.count(QuizQuestionOption.id)
                .filter(QuizQuestionOption.is_correct)
                .label("correct_count")
            ),
            func.count(QuizQuestionOption.id).label("total_count"),
        )
        .join(
            QuizQuestionOption,
            QuizSubmissionAnswer.selected_option_id == QuizQuestionOption.id,
        )
        .group_by(QuizSubmissionAnswer.submission_id)
        .subquery()
    )

    query = select(
        sql.select(func.count(Quiz.id)).scalar_subquery().label("quizzes_count"),
        (
            sql.select(func.count(QuizSubmission.id))
            .scalar_subquery()
            .label("submissions_count")
        ),
        (
            sql.select(
                func.sum(
                    case(
                        (
                            quiz_question_answers.c.correct_count
                            / cast(quiz_question_answers.c.total_count, Float)
                            > success_threshold,
                            1,
                        ),
                        else_=0,
                    )
                )
            )
            .scalar_subquery()
            .label("successful_submissions_count")
        ),
        (
            sql.select(func.avg(QuizSubmissionAnswer.spent_time_seconds))
            .scalar_subquery()
            .label("avg_time_spent_sec")
        ),
    )

    result = await db_session.execute(query)
    stats = result.mappings().one()
    return QuizStats.model_validate(stats)
