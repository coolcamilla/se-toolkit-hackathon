"""Settings for the MCP tutor server."""

from __future__ import annotations

import os


def get_db_url() -> str:
    """Return PostgreSQL connection URL."""
    host = os.environ.get("TUTOR_DB_HOST", "postgres")
    port = os.environ.get("TUTOR_DB_PORT", "5432")
    dbname = os.environ.get("TUTOR_DB_NAME", "tutor")
    user = os.environ.get("TUTOR_DB_USER", "postgres")
    password = os.environ.get("TUTOR_DB_PASSWORD", "postgres")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


def get_llm_api_key() -> str:
    return os.environ.get("TUTOR_LLM_API_KEY", "")


def get_llm_api_base() -> str:
    return os.environ.get("TUTOR_LLM_API_BASE_URL", "http://qwen-code-api:8080/v1")


def get_llm_model() -> str:
    return os.environ.get("TUTOR_LLM_MODEL", "coder-model")
