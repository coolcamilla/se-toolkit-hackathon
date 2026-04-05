"""Settings for the tutor backend."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    name: str = "Personal Exam Tutor"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    db_path: str = "tutor.db"

    model_config = {"env_prefix": "TUTOR_"}


settings = Settings()
