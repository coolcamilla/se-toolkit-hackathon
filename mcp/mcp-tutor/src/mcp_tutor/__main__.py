"""Allow running as `python -m mcp_tutor`."""

import asyncio

from mcp_tutor.server import main

if __name__ == "__main__":
    asyncio.run(main())
