from typing import Annotated

from fastapi import APIRouter, Path
from starlette import status
from starlette.responses import JSONResponse

from server.authentication.utils import protected_route
from server.db import DbSession

from . import services
from .schemas import StudentDetailSchema, StudentSchema, StudentStats

router = APIRouter()


@router.get("", response_model=list[StudentSchema])
@protected_route
async def list_students(
    db_session: DbSession,
    limit: int = 20,
    offset: int = 0,
):
    return await services.list_students(
        db_session=db_session,
        limit=limit,
        offset=offset,
    )


@router.get("/{username}", response_model=StudentDetailSchema)
@protected_route
async def get_student(db_session: DbSession, username: Annotated[str, Path()]):
    students = await services.list_students(
        db_session=db_session,
        usernames=[username],
        out_type=StudentDetailSchema,
    )

    if not students:
        return JSONResponse(
            {"detail": "No student matches given ID"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return students[0]


@router.get("/stats", response_model=StudentStats)
@protected_route
async def get_student_stats(db_session: DbSession):
    return await services.get_student_stats(db_session=db_session)
