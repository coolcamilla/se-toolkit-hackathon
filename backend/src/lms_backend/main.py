"""LMS Backend main application — stub until the src/ module is restored."""

from fastapi import FastAPI

app = FastAPI(title="LMS Backend (stub)")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "note": "stub — src/ not yet restored"}
