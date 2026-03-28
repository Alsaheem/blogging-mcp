"""ASGI app for Uvicorn / Gunicorn (production-style HTTP).

See https://gofastmcp.com/deployment/http — same pattern as ``mcp.http_app()`` in the FastMCP docs.
The MCP endpoint defaults to ``/mcp`` on whatever host/port Uvicorn binds to.
"""

from __future__ import annotations

from blogging_mcp.request_settings import mcp_http_middleware
from blogging_mcp.server import mcp

app = mcp.http_app(middleware=mcp_http_middleware())
