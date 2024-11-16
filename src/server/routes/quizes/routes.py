from typing import Annotated

from fastapi import APIRouter, Path
from starlette import status
from starlette.responses import JSONResponse

from server.authentication.utils import protected_route
from server.db import DbSession

from . import services
from .schemas import QuizDetailSchema, QuizSchema, QuizStats

router = APIRouter()


@router.get("", response_model=list[QuizSchema])
@protected_route
async def list_quizes(
    db_session: DbSession,
    limit: int = 20,
    offset: int = 0,
):
    return await services.list_quizes(
        db_session=db_session,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=QuizStats)
@protected_route
async def get_quiz_stats(db_session: DbSession):
    return await services.get_quiz_stats(db_session=db_session)


@router.get("/{id}", response_model=QuizDetailSchema)
@protected_route
async def get_quiz(db_session: DbSession, id: Annotated[int, Path()]):
    quizes = await services.list_quizes(
        db_session=db_session,
        ids=[id],
        out_type=QuizDetailSchema,
    )

    if not quizes:
        return JSONResponse(
            {"detail": "No quiz matches given ID"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return quizes[0]
