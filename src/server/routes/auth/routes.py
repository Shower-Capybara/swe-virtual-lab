import hashlib

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import sql
from starlette import status

from server.authentication.utils import User, protected_route
from server.config import settings
from server.db import DbSession
from server.db.models import User as UserTable
from server.state import redis

from .jwt import generate_jwt
from .schemas import LoginBody, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(db_session: DbSession, body: LoginBody):
    query = (
        sql.select(UserTable.password, UserTable.role)
        .where(UserTable.username == body.username)
        .limit(1)
    )
    cursor_result = await db_session.execute(query)
    data = cursor_result.tuples().one_or_none()
    if data is None:
        return JSONResponse(
            {"detail": "Invalid username"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    (password, role) = data
    if hashlib.sha256(body.password.encode()).hexdigest() != password:
        return JSONResponse(
            {"detail": "Invalid password"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if role != "editor":
        return JSONResponse(
            {"detail": "Only editors are allowed to login"},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return LoginResponse(
        access_token=generate_jwt(
            username=body.username,
            jwt_secret=settings.JWT_SECRET,
        )
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@protected_route
async def logout(user: User):
    await redis.set(name=f"revoked:{user.token}", value="1", ex=86400)
