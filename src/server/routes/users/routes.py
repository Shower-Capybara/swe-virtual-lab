from fastapi import APIRouter
from sqlalchemy import sql

from server.authentication.utils import User, protected_route
from server.db import DbSession
from server.db.models import User as UserTable

router = APIRouter()


@router.get("/me")
@protected_route
async def get_me(db_session: DbSession, user: User):
    query = (
        sql.select(
            UserTable.id,
            UserTable.username,
            UserTable.name,
            UserTable.role,
            UserTable.created_at,
        )
        .where(UserTable.username == user.username)
        .limit(1)
    )
    cursor_result = await db_session.execute(query)
    return cursor_result.mappings().one()
