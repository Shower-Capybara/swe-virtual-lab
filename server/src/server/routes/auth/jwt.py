from datetime import datetime, timedelta, timezone
from typing import TypedDict, cast

from jose import JWTError, jwt


class InvalidJwtTokenException(Exception):
    pass


class JwtPayload(TypedDict):
    username: str
    exp: int


def generate_jwt(username: str, jwt_secret: str) -> str:
    payload: JwtPayload = {
        "username": username,
        "exp": int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp()),
    }
    return jwt.encode(claims=payload, key=jwt_secret, algorithm="HS256")  # type: ignore[reportArgumentType]


def validate_jwt_token(token: str, jwt_secret: str) -> JwtPayload:
    try:
        payload = cast(
            JwtPayload,
            jwt.decode(token=token, key=jwt_secret, algorithms=["HS256"]),
        )
    except JWTError as e:
        raise InvalidJwtTokenException("Invalid JWT token") from e

    if payload["exp"] <= int(
        (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
    ):
        raise InvalidJwtTokenException("JWT token has expired")

    return payload
