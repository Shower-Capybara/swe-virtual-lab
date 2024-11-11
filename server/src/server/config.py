from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env", usecwd=True),
        extra="ignore",
    )


try:
    settings = Settings()  # type: ignore[call-arg]
except Exception as e:
    print(f"Failed to init settings: {e!r}")
