"""Tutor Backend — Personal Exam Tutor API."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from tutor_backend.database import init_db
from tutor_backend.routers.questions import router as questions_router
from tutor_backend.settings import settings

api_key_scheme = APIKeyHeader(name="X-API-Key")


async def require_api_key(key: str = Security(api_key_scheme)):
    if not settings.api_key:
        return key
    if key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return key


app = FastAPI(title="Personal Exam Tutor")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(questions_router)
