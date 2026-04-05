"""Settings for the tutor backend."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = "Personal Exam Tutor"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # PostgreSQL connection
    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "tutor"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # API key for endpoint auth
    api_key: str = ""

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_prefix": "TUTOR_"}


settings = Settings()
