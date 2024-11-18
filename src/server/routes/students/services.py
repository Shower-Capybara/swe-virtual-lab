from pydantic import TypeAdapter
from sqlalchemy import Float, case, cast, desc, func, select, sql, true
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import (
    QuizQuestionOption,
    QuizSubmission,
    QuizSubmissionAnswer,
    User,
)
from server.db.utils import empty_array, json_build_object

from .schemas import StudentSchema, StudentStats


async def list_students(
    db_session: AsyncSession,
    usernames: list[str] | None = None,
    success_threshold: float = 0.2,
    limit: int = 20,
    offset: int = 0,
    out_type: type[StudentSchema] = StudentSchema,
) -> list[StudentSchema]:
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

    submission_stats = (
        select(
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
        .where(correct_answers_per_submission.c.user_id == User.id)
        .group_by(correct_answers_per_submission.c.user_id)
        .scalar_subquery()
        .lateral()
    )

    quiz_question_answers = (
        select(
            QuizSubmission.quiz_id,
            QuizSubmission.user_id,
            (
                func.count(QuizQuestionOption.id)
                .filter(QuizQuestionOption.is_correct)
                .label("correct_count")
            ),
            func.count(QuizQuestionOption.id).label("total_count"),
            func.sum(QuizSubmissionAnswer.spent_time_seconds).label(
                "spent_time_seconds"
            ),
        )
        .select_from(QuizSubmissionAnswer)
        .join(
            QuizQuestionOption,
            QuizSubmissionAnswer.selected_option_id == QuizQuestionOption.id,
        )
        .join(
            QuizSubmission,
            QuizSubmissionAnswer.submission_id == QuizSubmission.id,
        )
        .group_by(
            QuizSubmission.quiz_id,
            QuizSubmission.user_id,
            QuizSubmissionAnswer.submission_id,
        )
        .subquery()
    )

    quiz_correct_submissions = (
        select(
            quiz_question_answers.c.quiz_id,
            quiz_question_answers.c.user_id,
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
            func.avg(quiz_question_answers.c.spent_time_seconds).label(
                "avg_spent_time_seconds"
            ),
        )
        .group_by(
            quiz_question_answers.c.quiz_id,
            quiz_question_answers.c.user_id,
        )
        .subquery()
    )

    query = (
        select(
            User.username,
            User.name,
            func.coalesce(submission_stats.c.successful_submissions, 0).label(
                "successful_submissions"
            ),
            func.coalesce(submission_stats.c.total_submissions, 0).label(
                "total_submissions"
            ),
            (
                select(
                    func.coalesce(
                        func.sum(QuizSubmissionAnswer.spent_time_seconds),
                        0,
                    ).label("spent_time_seconds")
                )
                .select_from(QuizSubmission)
                .join(
                    QuizSubmissionAnswer,
                    QuizSubmission.id == QuizSubmissionAnswer.submission_id,
                )
                .where(QuizSubmission.user_id == User.id)
                .scalar_subquery()
                .label("total_time_spent_sec")
            ),
            (
                sql.select(
                    func.coalesce(
                        func.array_agg(
                            json_build_object(
                                {
                                    "id": quiz_correct_submissions.c.quiz_id,
                                    "successful_submissions_count": quiz_correct_submissions.c.successful_submissions_count,
                                    "total_submissions_count": quiz_correct_submissions.c.total_submissions_count,
                                    "avg_spent_time_seconds": quiz_correct_submissions.c.avg_spent_time_seconds,
                                }
                            )
                        ),
                        empty_array(),
                    )
                )
                .where(quiz_correct_submissions.c.user_id == User.id)
                .scalar_subquery()
                .label("quizes")
            ),
        )
        .join(submission_stats, true(), isouter=True)
        .where(User.role == "student")
        .order_by(desc("successful_submissions"))
        .limit(limit)
        .offset(offset)
    )

    if usernames:
        query = query.where(User.username.in_(usernames))

    result = await db_session.execute(query)
    ta = TypeAdapter(list[out_type])
    return ta.validate_python(result.mappings().all())


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
            select(func.count("*"))
            .where(User.role == "student")
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
