"""Entry point for `python -m tutor_backend.run`."""

from __future__ import annotations

import uvicorn

from tutor_backend.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "tutor_backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
