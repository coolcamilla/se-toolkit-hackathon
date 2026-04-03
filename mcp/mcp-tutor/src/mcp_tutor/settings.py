"""Settings for the MCP tutor server."""

import os
from pathlib import Path


def get_db_path() -> Path:
    """Return the path to the SQLite database file."""
    return Path(os.environ.get("TUTOR_DB_PATH", "tutor.db"))
