from typing import Literal

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class RealSettings(BaseSettings):
    ENV: Literal["real"] = "real"
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    JWT_SECRET: str
    REDIS_URL: str

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env", usecwd=True),
        extra="ignore",
    )
