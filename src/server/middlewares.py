from copy import copy
from types import FunctionType
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from redis.asyncio import Redis
from starlette import status
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    DispatchFunction,
    RequestResponseEndpoint,
)
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Match
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Scope

from .authentication.schemas import AutheticatedUser
from .authentication.utils import (
    is_route_protected,
    process_header,
    set_user,
)
from .config import settings
from .routes.auth.jwt import InvalidJwtTokenException, validate_jwt_token


def match_routes(routes: list[BaseRoute], scope: Scope) -> FunctionType | None:
    """Find route function by given routes list and request's scope"""

    for route in routes:
        match, child_scope = route.matches(scope)
        if match != Match.FULL:
            continue

        scope.update(child_scope)
        endpoint: FastAPI | FunctionType = scope["endpoint"]

        if isinstance(endpoint, FunctionType):
            return endpoint
        elif isinstance(endpoint, StaticFiles):
            continue
        else:
            return match_routes(endpoint.routes, scope)


def _resolve_route(request: Request) -> Callable[..., Any] | None:
    """
    Find an endpoint function based on the request based.
    It's mainly useful in middlewares where endpoint function is not available
    right away.
    """

    app: FastAPI = request.app
    try:
        return request.state._route
    except AttributeError:
        request.state._route = match_routes(app.routes, copy(request.scope))
        return request.state._route


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        redis: Redis,
        dispatch: DispatchFunction | None = None,
    ) -> None:
        self._redis = redis
        super().__init__(app, dispatch)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        route = _resolve_route(request)
        if route is None or not is_route_protected(route):
            return await call_next(request)

        auth_header_value = request.headers.get("Authorization")
        if auth_header_value is None:
            return JSONResponse(
                {"detail": "No authorization value provided"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            _, token = process_header(auth_header_value)
        except Exception as e:
            return JSONResponse(
                {"detail": str(e)},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = validate_jwt_token(token=token, jwt_secret=settings.JWT_SECRET)
        except InvalidJwtTokenException as e:
            return JSONResponse(
                {"detail": str(e)},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if await self._redis.get(f"revoked:{token}") is not None:
            return JSONResponse(
                {"detail": "JWT token is revoked"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        set_user(
            request=request,
            user=AutheticatedUser(username=payload["username"], token=token),
        )

        return await call_next(request)
