#!/usr/bin/env python3
"""
Entrypoint script for nanobot Docker container.

Reads config.json, injects environment variable values, writes config.resolved.json,
then execs into nanobot gateway.
"""

import json
import os
import sys


def main():
    # Paths
    config_path = "/app/nanobot/config.json"
    # Write resolved config to /tmp to avoid permission issues when
    # container runs as host user but image files are owned by appuser
    resolved_path = "/tmp/nanobot/config.resolved.json"
    workspace = "/app/nanobot/workspace"

    # Ensure directory exists
    os.makedirs(os.path.dirname(resolved_path), exist_ok=True)

    # Read base config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Override provider settings from env vars
    if llm_api_key := os.environ.get("LLM_API_KEY"):
        config["providers"]["custom"]["apiKey"] = llm_api_key

    if llm_api_base_url := os.environ.get("LLM_API_BASE_URL"):
        config["providers"]["custom"]["apiBase"] = llm_api_base_url

    # Override agent defaults
    if llm_api_model := os.environ.get("LLM_API_MODEL"):
        config["agents"]["defaults"]["model"] = llm_api_model

    # Override gateway settings
    if nanobot_gateway_host := os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS"):
        config["gateway"]["host"] = nanobot_gateway_host

    if nanobot_gateway_port := os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT"):
        config["gateway"]["port"] = int(nanobot_gateway_port)

    # Override LMS MCP server settings
    if nanobot_lms_backend_url := os.environ.get("NANOBOT_LMS_BACKEND_URL"):
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = (
            nanobot_lms_backend_url
        )

    if nanobot_lms_api_key := os.environ.get("NANOBOT_LMS_API_KEY"):
        config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = (
            nanobot_lms_api_key
        )

    # Enable webchat channel from env vars
    if nanobot_webchat_host := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS"):
        config["channels"]["webchat"]["host"] = nanobot_webchat_host

    if nanobot_webchat_port := os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT"):
        config["channels"]["webchat"]["port"] = int(nanobot_webchat_port)

    # Configure mcp_webchat MCP server for structured UI messages
    config["tools"]["mcpServers"]["webchat"] = {
        "command": "/app/.venv/bin/python",
        "args": ["-m", "mcp_webchat"],
        "env": {
            "NANOBOT_WEBCHAT_UI_RELAY_URL": os.environ.get(
                "NANOBOT_WEBCHAT_UI_RELAY_URL", "ws://localhost:8080/ws/chat"
            ),
            "NANOBOT_WEBCHAT_UI_RELAY_TOKEN": os.environ.get(
                "NANOBOT_ACCESS_KEY", ""
            ),
        },
    }

    # Configure mcp_obs MCP server for observability tools
    config["tools"]["mcpServers"]["obs"] = {
        "command": "/app/.venv/bin/python",
        "args": ["-m", "mcp_obs"],
        "env": {
            "VICTORIALOGS_URL": os.environ.get(
                "VICTORIALOGS_URL", "http://victorialogs:9428"
            ),
            "VICTORIATRACES_URL": os.environ.get(
                "VICTORIATRACES_URL", "http://victoriatraces:10428"
            ),
        },
    }

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}", file=sys.stderr)

    # Exec into nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            resolved_path,
            "--workspace",
            workspace,
        ],
    )


if __name__ == "__main__":
    main()
