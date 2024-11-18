from typing import Literal

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    ENV: Literal["testing"] = "testing"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5477"
    DB_NAME: str = "politeh"
    JWT_SECRET: str = "12345678"
    REDIS_URL: str = "redis://localhost:6379"
