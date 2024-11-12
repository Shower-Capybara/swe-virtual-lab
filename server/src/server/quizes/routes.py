from typing import Annotated

from fastapi import APIRouter, Path
from sqlalchemy import func, sql
from starlette import status
from starlette.responses import JSONResponse

from server.authentication.utils import protected_route

from ..db import DbSession
from ..db.models import Quiz, QuizQuestion, QuizQuestionOption
from ..db.utils import empty_array, json_build_object

router = APIRouter()


@router.get("")
@protected_route
async def list_quizes(
    db_session: DbSession,
    limit: int = 20,
    offset: int = 0,
):
    cursor_result = await db_session.execute(
        sql.select(
            Quiz.id,
            Quiz.title,
            Quiz.description,
            Quiz.image,
            Quiz.created_at,
            (
                func.count(QuizQuestion.id)
                .filter(QuizQuestion.id.is_not(None))
                .label("questions_count")
            ),
        )
        .join(QuizQuestion, QuizQuestion.quiz_id == Quiz.id, isouter=True)
        .group_by(Quiz.id)
        .order_by(Quiz.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return cursor_result.mappings().all()


@router.get("/{id}")
@protected_route
async def get_quiz(db_session: DbSession, id: Annotated[int, Path()]):
    questions_subquery = (
        sql.select(
            QuizQuestion.quiz_id,
            QuizQuestion.id,
            QuizQuestion.title,
            QuizQuestion.description,
            QuizQuestion.image,
            QuizQuestion.created_at,
            func.coalesce(
                func.array_agg(
                    json_build_object(
                        {
                            "id": QuizQuestionOption.id,
                            "text": QuizQuestionOption.text,
                            "image": QuizQuestionOption.image,
                        }
                    )
                ).filter(QuizQuestionOption.id.is_not(None)),
                empty_array(),
            ).label("options"),
        )
        .join(
            QuizQuestionOption,
            QuizQuestion.id == QuizQuestionOption.question_id,
            isouter=True,
        )
        .group_by(QuizQuestion.id)
        .subquery()
    )

    questions_list = (
        sql.select(
            questions_subquery.c.quiz_id,
            func.coalesce(
                func.array_agg(
                    json_build_object(
                        {name: column for name, column in questions_subquery.c.items()}
                    ),
                ).filter(questions_subquery.c.id.is_not(None)),
                empty_array(),
            ).label("questions"),
        )
        .where(questions_subquery.c.quiz_id == Quiz.id)
        .group_by(questions_subquery.c.quiz_id)
        .subquery()
        .lateral()
    )

    cursor_result = await db_session.execute(
        sql.select(
            Quiz.id,
            Quiz.title,
            Quiz.description,
            Quiz.image,
            Quiz.created_at,
            func.coalesce(
                questions_list.c.questions,
                empty_array(),
            ).label("questions"),
        )
        .join(
            questions_list,
            questions_list.c.quiz_id == Quiz.id,
            isouter=True,
        )
        .where(Quiz.id == id)
    )
    data = cursor_result.mappings().one_or_none()
    if data is None:
        return JSONResponse(
            {"detail": "No quiz matches given ID"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return data
