from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration from environment and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    devto_api_key: str = Field(default="", description="dev.to API key")

    hashnode_token: str = Field(
        default="",
        description="Hashnode Personal Access Token (hashnode.com/settings/developer)",
    )
    hashnode_publication_host: str = Field(
        default="",
        description="Blog hostname, e.g. username.hashnode.dev or your custom domain",
    )

    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_http_host: str = Field(
        default="127.0.0.1",
        description="Bind address for HTTP MCP (use 0.0.0.0 when reachable from another machine)",
    )
    mcp_http_port: int = 8765
    mcp_http_timeout: float = 30.0
