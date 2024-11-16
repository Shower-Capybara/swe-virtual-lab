from fastapi import APIRouter

from server.authentication.utils import User, protected_route
from server.db import DbSession

from . import services
from .schemas import UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema)
@protected_route
async def get_me(db_session: DbSession, user: User):
    return services.get_user(db_session=db_session, username=user.username)
