# Adapted from https://github.com/astral-sh/uv-docker-example/blob/fa761744819c05f4ce207bde1f0a396f6be3915f/multistage.Dockerfile
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files for dependency resolution
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy mcp-tutor source (required for tutor MCP tool)
COPY --from=workspace mcp/mcp-tutor /app/mcp/mcp-tutor

# Copy nanobot-websocket-channel packages (required for webchat)
COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol /app/nanobot-websocket-channel/nanobot-channel-protocol
COPY --from=workspace nanobot-websocket-channel/nanobot-webchat /app/nanobot-websocket-channel/nanobot-webchat
COPY --from=workspace nanobot-websocket-channel/mcp-webchat /app/nanobot-websocket-channel/mcp-webchat

# Copy nanobot package files
COPY pyproject.toml /app/nanobot/pyproject.toml

# Sync dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# Copy the rest of the nanobot package
COPY . /app/nanobot

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

ARG APP_UID=999
ARG APP_GID=999

RUN groupadd --system --gid ${APP_GID} appgroup \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

COPY --from=builder --chown=appuser:appgroup /app /app

RUN mkdir -p /app/nanobot/workspace/cron /app/nanobot/workspace/memory \
    && chmod -R 777 /app/nanobot/workspace

ENV PATH="/app/.venv/bin:$PATH"

USER appuser
WORKDIR /app

CMD ["python", "/app/nanobot/entrypoint.py"]
