from __future__ import annotations

import base64

from starlette.requests import Request

from blogging_mcp.request_settings import (
    decode_header_secret,
    merge_settings_from_request_headers,
)


def _req(raw: list[tuple[bytes, bytes]]) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": raw,
    }
    return Request(scope)


def test_merge_none_when_no_credential_headers() -> None:
    r = merge_settings_from_request_headers(_req([]))
    assert r is None


def test_merge_devto_only() -> None:
    req = _req([(b"x-devto-api-key", b"abc")])
    merged = merge_settings_from_request_headers(req)
    assert merged is not None
    assert merged.devto_api_key == "abc"


def test_merge_all_three() -> None:
    req = _req(
        [
            (b"x-devto-api-key", b"d"),
            (b"x-hashnode-token", b"h"),
            (b"x-hashnode-publication-host", b"x.hashnode.dev"),
        ]
    )
    merged = merge_settings_from_request_headers(req)
    assert merged is not None
    assert merged.devto_api_key == "d"
    assert merged.hashnode_token == "h"
    assert merged.hashnode_publication_host == "x.hashnode.dev"


def test_asgi_header_keys_are_lowercase() -> None:
    """ASGI requires lowercased header names in ``scope["headers"]``."""
    req = _req([(b"x-devto-api-key", b"v")])
    merged = merge_settings_from_request_headers(req)
    assert merged is not None
    assert merged.devto_api_key == "v"


def test_decode_header_secret_base64() -> None:
    assert decode_header_secret(base64.b64encode(b"my-api-key").decode()) == "my-api-key"


def test_merge_devto_base64_header() -> None:
    token = base64.b64encode(b"real-devto-key").decode()
    req = _req([(b"x-devto-api-key", token.encode())])
    merged = merge_settings_from_request_headers(req)
    assert merged is not None
    assert merged.devto_api_key == "real-devto-key"


def test_merge_all_three_base64() -> None:
    req = _req(
        [
            (b"x-devto-api-key", base64.b64encode(b"d").decode().encode()),
            (b"x-hashnode-token", base64.b64encode(b"h").decode().encode()),
            (
                b"x-hashnode-publication-host",
                base64.b64encode(b"x.hashnode.dev").decode().encode(),
            ),
        ]
    )
    merged = merge_settings_from_request_headers(req)
    assert merged is not None
    assert merged.devto_api_key == "d"
    assert merged.hashnode_token == "h"
    assert merged.hashnode_publication_host == "x.hashnode.dev"
