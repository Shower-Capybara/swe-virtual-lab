from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import User as UserTable

from .schemas import UserSchema


async def get_user(db_session: AsyncSession, username: str) -> UserSchema:
    query = (
        sql.select(
            UserTable.id,
            UserTable.username,
            UserTable.name,
            UserTable.role,
            UserTable.created_at,
        )
        .where(UserTable.username == username)
        .limit(1)
    )
    cursor_result = await db_session.execute(query)
    return UserSchema.model_validate(cursor_result.mappings().one())
