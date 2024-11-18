from datetime import date

from fastapi import APIRouter
from starlette import status
from starlette.responses import JSONResponse

from server.authentication.utils import protected_route
from server.db import DbSession

from . import services
from .schemas import DailyPlatformStats, PlatformStats

router = APIRouter()


@router.get("")
@protected_route
async def get_platform_stats(db_session: DbSession) -> PlatformStats:
    return await services.get_platform_stats(db_session)


@router.get("/daily_distribution", response_model=list[DailyPlatformStats])
@protected_route
async def get_daily_platform_stats_distribution(
    db_session: DbSession,
    start_date: date,
    end_date: date,
    limit: int = 50,
    offset: int = 0,
):
    if start_date >= end_date:
        return JSONResponse(
            content={"detail": "Start date should be less than the end date"},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return await services.get_daily_platform_stats_distribution(
        db_session=db_session,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
