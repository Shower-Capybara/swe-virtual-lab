from pydantic import TypeAdapter
from sqlalchemy import Float, case, cast, desc, func, select, sql, true
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import (
    Quiz,
    QuizQuestion,
    QuizQuestionOption,
    QuizSubmission,
    QuizSubmissionAnswer,
)
from server.db.utils import empty_array, json_build_object

from .schemas import QuizSchema, QuizStats


async def list_quizes(
    db_session: AsyncSession,
    ids: list[int] | None = None,
    success_threshold: float = 0.2,
    limit: int = 20,
    offset: int = 0,
    out_type: type[QuizSchema] = QuizSchema,
):
    quiz_question_answers = (
        select(
            QuizSubmission.quiz_id,
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
        .join(
            QuizSubmission,
            QuizSubmissionAnswer.submission_id == QuizSubmission.id,
        )
        .group_by(QuizSubmission.quiz_id, QuizSubmissionAnswer.submission_id)
        .subquery()
    )

    quiz_correct_submissions = (
        sql.select(
            quiz_question_answers.c.quiz_id,
            func.count("*").label("total_submissions_count"),
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
            ).label("successful_submissions_count"),
        )
        .group_by(quiz_question_answers.c.quiz_id)
        .subquery()
    )

    quiz_questions = (
        sql.select(
            QuizQuestion.quiz_id,
            json_build_object(
                {
                    "id": QuizQuestion.id,
                    "title": QuizQuestion.title,
                    "description": QuizQuestion.description,
                    "image": QuizQuestion.image,
                    "created_at": QuizQuestion.created_at,
                    "total_answers": func.count("*"),
                    "correct_answers": func.sum(
                        case(
                            (QuizQuestionOption.is_correct.is_(True), 1),
                            else_=0,
                        )
                    ),
                    "avg_time_spent_sec": func.avg(
                        QuizSubmissionAnswer.spent_time_seconds
                    ),
                }
            ).label("question"),
        )
        .join(
            QuizSubmissionAnswer,
            QuizQuestion.id == QuizSubmissionAnswer.question_id,
        )
        .join(
            QuizQuestionOption,
            QuizSubmissionAnswer.selected_option_id == QuizQuestionOption.id,
        )
        .group_by(QuizQuestion.id)
        .subquery()
    )

    quiz_questions_list = (
        sql.select(
            quiz_questions.c.quiz_id,
            func.array_agg(quiz_questions.c.question).label("questions"),
        )
        .where(quiz_questions.c.quiz_id == Quiz.id)
        .group_by(quiz_questions.c.quiz_id)
        .subquery()
        .lateral()
    )

    query = (
        sql.select(
            Quiz.id,
            Quiz.title,
            Quiz.description,
            Quiz.image,
            Quiz.created_at,
            (
                sql.select(func.count(QuizQuestion.id))
                .where(QuizQuestion.quiz_id == Quiz.id)
                .scalar_subquery()
                .label("questions_count")
            ),
            func.coalesce(quiz_correct_submissions.c.total_submissions_count, 0).label(
                "total_submissions_count"
            ),
            func.coalesce(
                quiz_correct_submissions.c.successful_submissions_count, 0
            ).label("successful_submissions_count"),
            (
                sql.select(
                    func.coalesce(func.avg(QuizSubmissionAnswer.spent_time_seconds), 0)
                )
                .join(
                    QuizSubmission,
                    QuizSubmissionAnswer.submission_id == QuizSubmission.id,
                )
                .where(QuizSubmission.quiz_id == Quiz.id)
                .scalar_subquery()
                .label("avg_time_spent_sec")
            ),
            func.coalesce(quiz_questions_list.c.questions, empty_array()).label(
                "questions"
            ),
        )
        .select_from(Quiz)
        .join(
            quiz_correct_submissions,
            quiz_correct_submissions.c.quiz_id == Quiz.id,
            isouter=True,
        )
        .join(quiz_questions_list, true(), isouter=True)
        .order_by(
            desc("total_submissions_count"),
            desc("successful_submissions_count"),
        )
        .limit(limit)
        .offset(offset)
    )

    if ids:
        query = query.where(Quiz.id.in_(ids))

    cursor_result = await db_session.execute(query)
    return TypeAdapter(list[out_type]).validate_python(cursor_result.mappings().all())


async def get_quiz_stats(
    db_session: AsyncSession,
    ids: list[int] | None = None,
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

    if ids:
        query = query.where(Quiz.id.in_(ids))

    result = await db_session.execute(query)
    stats = result.mappings().one()
    return QuizStats.model_validate(stats)
