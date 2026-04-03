"""Entry point for running mcp_obs as a module: python -m mcp_obs"""

from mcp_obs.server import mcp

if __name__ == "__main__":
    mcp.run()
