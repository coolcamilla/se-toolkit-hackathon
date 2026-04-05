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
