from collections.abc import Callable
from typing import Annotated, ParamSpec, TypeVar

from fastapi import Depends, Request
from fastapi.security.utils import get_authorization_scheme_param

from .schemas import AutheticatedUser

T = TypeVar("T")
P = ParamSpec("P")
Func = Callable[P, T]


def protected_route[**P, T](route_func: Callable[P, T]) -> Callable[P, T]:
    route_func._protected = True
    return route_func


def is_route_protected(route_func: Callable) -> bool:
    return getattr(route_func, "_protected", False)


def process_header(value: str) -> tuple[str, str]:
    scheme, token = get_authorization_scheme_param(value)

    if not token or " " in token:
        raise Exception("Header value should follow a format: " + r"{scheme} {token}")

    if scheme.lower() != "bearer":
        raise Exception("Invalid authentication scheme")

    return scheme, token


def set_user(request: Request, user: AutheticatedUser) -> None:
    request.state.user = user


def get_user(request: Request) -> AutheticatedUser:
    return request.state.user


User = Annotated[AutheticatedUser, Depends(get_user)]
