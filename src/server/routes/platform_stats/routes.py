from fastapi import APIRouter

from server.authentication.utils import protected_route
from server.db import DbSession

from . import services
from .schemas import PlatformStats

router = APIRouter()


@router.get("")
@protected_route
async def get_platform_stats(db_session: DbSession) -> PlatformStats:
    return await services.get_platform_stats(db_session)
