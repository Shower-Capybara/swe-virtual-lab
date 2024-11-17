from fastapi import APIRouter

from server.authentication.utils import protected_route
from server.db import DbSession

from . import services
from .schemas import StudentStats

router = APIRouter()


@router.get("/stats", response_model=StudentStats)
@protected_route
async def get_student_stats(db_session: DbSession):
    return await services.get_student_stats(db_session=db_session)
