import hashlib

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import sql
from starlette import status

from server.config import settings
from server.db import DbSession
from server.db.models import User

from .jwt import generate_jwt
from .schemas import LoginBody

router = APIRouter(tags=["auth"])


@router.post("/login")
async def login(db_session: DbSession, body: LoginBody):
    query = (
        sql.select(User.password, User.role)
        .where(User.username == body.username)
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

    return JSONResponse(
        {
            "access_token": generate_jwt(
                username=body.username, jwt_secret=settings.JWT_SECRET
            )
        }
    )
