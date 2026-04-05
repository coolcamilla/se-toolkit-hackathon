"""Tutor Backend — Personal Exam Tutor API."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.openapi.models import APIKey, APIKeyIn

from tutor_backend.database import init_db
from tutor_backend.routers.questions import router as questions_router
from tutor_backend.settings import settings

security = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="Personal Exam Tutor",
    security=[{"apiKey": []}] if settings.api_key else [],
    swagger_ui_init_oauth={"persistAuthorization": True},
)

# Register the API key scheme in OpenAPI
if settings.api_key:
    app.openapi_schema = None  # Force regeneration

    async def verify_api_key(api_key: str | None = Security(security)):
        if not api_key or api_key != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key",
            )
        return api_key

    app.dependency_overrides[security] = verify_api_key


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


app.include_router(questions_router)


# Add custom OpenAPI schema for API key auth
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    if settings.api_key:
        schema["components"]["securitySchemes"] = {
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Enter the TUTOR_API_KEY to access protected endpoints",
            }
        }

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
