import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from server.authentication.utils import protected_route
from server.config import settings
from server.middlewares import AuthenticationMiddleware
from server.routes.auth.jwt import generate_jwt

from .settings import BASE_URL

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="function", name="client")
async def client():
    redis = FakeRedis()
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware, redis=redis)

    @app.get("/public")
    def public_endpoint():
        return "hello world"

    @app.get("/protected")
    @protected_route
    def protected_endpoint():
        return "hello world"

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url=BASE_URL,
    ) as client:
        yield client


async def test_authentication_middleware_public_endpoint(client: AsyncClient):
    response = await client.get(f"{BASE_URL}/public")
    assert response.status_code == 200
    assert response.json() == "hello world"


async def test_authentication_middleware_protected_endpoint_unauthorized(
    client: AsyncClient,
):
    response = await client.get(f"{BASE_URL}/protected")
    assert response.status_code == 401


async def test_authentication_middleware_protected_endpoint_authorized(
    client: AsyncClient,
):
    jwt_token = generate_jwt(username="abc", jwt_secret=settings.JWT_SECRET)
    response = await client.get(
        f"{BASE_URL}/protected",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert response.status_code == 200
    assert response.json() == "hello world"
