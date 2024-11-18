from datetime import datetime, timedelta

import pytest
import time_machine
from jose import jwt

from server.config import settings
from server.routes.auth.jwt import generate_jwt, validate_jwt_token


def test_generate_jwt_token():
    now = int(datetime.now().timestamp())
    username = "abc"

    with time_machine.travel(now):
        jwt_token = generate_jwt(username=username, jwt_secret=settings.JWT_SECRET)
        assert jwt.decode(token=jwt_token, key=settings.JWT_SECRET) == {
            "username": username,
            "exp": now + int(timedelta(days=1).total_seconds()),
        }


@pytest.mark.parametrize(
    "token",
    [
        "",  # empty
        "abcd",  # random
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFiYyIsImV4cCI6MTczMTg4NDQ2Mn0.-hkPgMx0dTAWZdMNCpQj9_7l4_zJ13i5dv9K_m1g054",  # expired
    ],
)
def test_generate_validate_jwt_token_invalid_token(token: str):
    with pytest.raises(Exception):
        validate_jwt_token(token=token, jwt_secret=settings.JWT_SECRET)


def test_generate_validate_jwt_token_valid_token():
    now = int(datetime.now().timestamp())
    username = "abc"

    with time_machine.travel(now):
        jwt_token = generate_jwt(username=username, jwt_secret=settings.JWT_SECRET)
        assert validate_jwt_token(
            token=jwt_token,
            jwt_secret=settings.JWT_SECRET,
        ) == {
            "username": username,
            "exp": now + int(timedelta(days=1).total_seconds()),
        }
