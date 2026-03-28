from __future__ import annotations

import logging
import sys


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
    from blogging_mcp.config import Settings
    from blogging_mcp.request_settings import mcp_http_middleware
    from blogging_mcp.server import mcp

    settings = Settings()
    if settings.mcp_transport == "http":
        mcp.run(
            transport="http",
            host=settings.mcp_http_host,
            port=settings.mcp_http_port,
            middleware=mcp_http_middleware(),
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
