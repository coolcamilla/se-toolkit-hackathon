"""Tutor Backend — Personal Exam Tutor API."""

from __future__ import annotations

from fastapi import FastAPI

from tutor_backend.database import init_db
from tutor_backend.routers.questions import router as questions_router
from tutor_backend.settings import settings

app = FastAPI(title="Personal Exam Tutor")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(questions_router)
