from datetime import datetime, timedelta, timezone
from typing import TypedDict, cast

from jose import JWTError, jwt


class InvalidJwtTokenException(Exception):
    pass


class JwtPayload(TypedDict):
    username: str
    exp: datetime


def generate_jwt(username: str, jwt_secret: str) -> str:
    payload: JwtPayload = {
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }
    return jwt.encode(claims=payload, key=jwt_secret, algorithm="HS256")  # type: ignore[reportArgumentType]


def validate_jwt_token(token: str, jwt_secret: str) -> JwtPayload:
    try:
        return cast(
            JwtPayload,
            jwt.decode(token=token, key=jwt_secret, algorithms=["HS256"]),
        )
    except JWTError as e:
        raise InvalidJwtTokenException from e
