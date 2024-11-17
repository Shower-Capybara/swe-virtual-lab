from typing import Self

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    JWT_SECRET: str
    REDIS_URL: str

    def __new__(cls: type[Self], *args, **kwargs) -> Self:
        if getattr(cls, "_instance", None) is None:
            setattr(cls, "_instance", super().__new__(cls, *args, **kwargs))
        return getattr(cls, "_instance")

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env", usecwd=True),
        extra="ignore",
    )


try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    print(f"Failed to init settings: {e!r}")
