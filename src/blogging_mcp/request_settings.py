"""Per-request Settings overrides from HTTP headers (Streamable HTTP only).

Clients (e.g. Cursor) can send:

- ``X-DEVTO-API-KEY``
- ``X-HASHNODE-TOKEN``
- ``X-HASHNODE-PUBLICATION-HOST``

Values may be **Base64-encoded** (standard alphabet, UTF-8 payload). Each value is
decoded when valid Base64; otherwise the raw string is used (plain text still works).

When at least one header is present, values override process env for that request only.
stdio transport does not use this path.
"""

from __future__ import annotations

import base64
import binascii
from contextvars import ContextVar
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from blogging_mcp.config import Settings

if TYPE_CHECKING:
    from starlette.middleware import Middleware

_request_settings: ContextVar[Settings | None] = ContextVar(
    "blogging_mcp_request_settings", default=None
)


def decode_header_secret(value: str) -> str:
    """Decode Base64 (UTF-8) credential strings; fall back to the original if not valid Base64."""
    value = value.strip()
    if not value:
        return value
    try:
        pad = (-len(value)) % 4
        raw = base64.b64decode(value + ("=" * pad), validate=True)
    except (binascii.Error, ValueError):
        return value
    try:
        return raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        return value


def effective_settings() -> Settings:
    """Process env Settings, or per-request override when middleware set it."""
    override = _request_settings.get()
    if override is not None:
        return override
    return Settings()


def merge_settings_from_request_headers(request: Request) -> Settings | None:
    """Return a copy of process ``Settings`` with credential headers applied, or ``None``."""
    base = Settings()
    updates: dict[str, str] = {}
    h = request.headers
    if "x-devto-api-key" in h:
        updates["devto_api_key"] = decode_header_secret(h["x-devto-api-key"])
    if "x-hashnode-token" in h:
        updates["hashnode_token"] = decode_header_secret(h["x-hashnode-token"])
    if "x-hashnode-publication-host" in h:
        updates["hashnode_publication_host"] = decode_header_secret(
            h["x-hashnode-publication-host"]
        )
    if not updates:
        return None
    return base.model_copy(update=updates)


class CredentialHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        merged = merge_settings_from_request_headers(request)
        if merged is None:
            return await call_next(request)
        token = _request_settings.set(merged)
        try:
            return await call_next(request)
        finally:
            _request_settings.reset(token)


def mcp_http_middleware() -> list[Middleware]:
    """Middleware list for ``FastMCP.http_app(..., middleware=...)``."""
    from starlette.middleware import Middleware

    return [Middleware(CredentialHeadersMiddleware)]
