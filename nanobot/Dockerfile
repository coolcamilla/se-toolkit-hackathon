# Adapted from https://github.com/astral-sh/uv-docker-example/blob/fa761744819c05f4ce207bde1f0a396f6be3915f/multistage.Dockerfile
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files for dependency resolution
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy mcp-lms source (required for editable install)
COPY --from=workspace mcp/mcp-lms /app/mcp/mcp-lms

# Copy nanobot-websocket-channel packages (required for webchat)
COPY --from=workspace nanobot-websocket-channel/nanobot-channel-protocol /app/nanobot-websocket-channel/nanobot-channel-protocol
COPY --from=workspace nanobot-websocket-channel/nanobot-webchat /app/nanobot-websocket-channel/nanobot-webchat
COPY --from=workspace nanobot-websocket-channel/mcp-webchat /app/nanobot-websocket-channel/mcp-webchat

# Copy mcp-obs package (required for observability tools)
COPY --from=workspace mcp/mcp-obs /app/mcp/mcp-obs

# Copy nanobot package files
COPY pyproject.toml /app/nanobot/pyproject.toml

# Sync dependencies (install workspace packages without --no-install-workspace)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package nanobot

# Copy the rest of the nanobot package
COPY . /app/nanobot

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Make sure we use UTF-8 encoding
ENV LANG=C.UTF-8

# Accept build args for non-root user
ARG APP_UID=999
ARG APP_GID=999

# Setup a non-root user with configurable UID/GID
RUN groupadd --system --gid ${APP_GID} appgroup \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy the application from the builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Create writable workspace directories for cron and other runtime data
# Make them writable by any user since container may run as host UID
RUN mkdir -p /app/nanobot/workspace/cron /app/nanobot/workspace/memory \
    && chmod -R 777 /app/nanobot/workspace

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Use the non-root user to run our application
USER appuser

# Use `/app` as the working directory
WORKDIR /app

CMD ["python", "/app/nanobot/entrypoint.py"]
