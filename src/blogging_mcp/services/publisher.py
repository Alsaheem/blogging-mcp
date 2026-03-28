from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from blogging_mcp.clients.devto import DevtoApiError, DevtoClient
from blogging_mcp.clients.hashnode import HashnodeApiError, HashnodeClient
from blogging_mcp.config import Settings
from blogging_mcp.models.article import PublishArticleInput
from blogging_mcp.models.results import (
    PlatformOutcome,
    PublishArticleResult,
    VerifyCredentialsResult,
)

logger = logging.getLogger(__name__)


def _hashnode_not_configured_message() -> str:
    return (
        "Hashnode not configured: set HASHNODE_TOKEN and HASHNODE_PUBLICATION_HOST "
        "(see https://docs.hashnode.com/quickstart/introduction)."
    )


def _devto_article_url(payload: dict[str, Any]) -> str | None:
    if not isinstance(payload, dict):
        return None
    u = payload.get("url")
    return str(u) if u else None


class Publisher:
    """Orchestrates dev.to REST + Hashnode GraphQL."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _devto(self) -> DevtoClient:
        return DevtoClient(self._settings.devto_api_key, timeout=self._settings.mcp_http_timeout)

    def _hashnode(self) -> HashnodeClient:
        return HashnodeClient(
            self._settings.hashnode_token,
            self._settings.hashnode_publication_host,
            timeout=self._settings.mcp_http_timeout,
        )

    async def verify_credentials(self) -> VerifyCredentialsResult:
        async def check_devto() -> PlatformOutcome:
            if not self._settings.devto_api_key:
                return PlatformOutcome(ok=False, error="DEVTO_API_KEY is not set")
            try:
                await self._devto().get_me()
                return PlatformOutcome(ok=True)
            except httpx.HTTPStatusError as e:
                return PlatformOutcome(
                    ok=False,
                    error=_format_http_error("dev.to", e),
                    raw_status_code=e.response.status_code,
                )
            except Exception as e:  # noqa: BLE001
                logger.exception("dev.to verify failed")
                return PlatformOutcome(ok=False, error=str(e))

        async def check_hashnode() -> PlatformOutcome:
            hn_host = self._settings.hashnode_publication_host.strip()
            if not self._settings.hashnode_token or not hn_host:
                return PlatformOutcome(ok=False, error=_hashnode_not_configured_message())
            try:
                await self._hashnode().verify_publication()
                return PlatformOutcome(ok=True)
            except HashnodeApiError as e:
                return PlatformOutcome(ok=False, error=str(e))
            except Exception as e:  # noqa: BLE001
                logger.exception("Hashnode verify failed")
                return PlatformOutcome(ok=False, error=str(e))

        dev_to, hashnode = await asyncio.gather(check_devto(), check_hashnode())
        return VerifyCredentialsResult(dev_to=dev_to, hashnode=hashnode)

    async def publish_article(self, data: PublishArticleInput) -> PublishArticleResult:
        async def run_devto() -> PlatformOutcome:
            if not self._settings.devto_api_key:
                return PlatformOutcome(ok=False, error="DEVTO_API_KEY is not set")
            try:
                client = self._devto()
                resp = await client.create_article(
                    title=data.title,
                    body_markdown=data.body_markdown,
                    published=data.devto_published,
                    tags=data.tags,
                    canonical_url=data.canonical_url,
                    cover_image=data.cover_image,
                    description=data.description,
                )
                return PlatformOutcome(ok=True, url=_devto_article_url(resp))
            except DevtoApiError as e:
                return PlatformOutcome(
                    ok=False,
                    error=str(e),
                    raw_status_code=e.status_code,
                )
            except httpx.HTTPStatusError as e:
                return PlatformOutcome(
                    ok=False,
                    error=_format_http_error("dev.to", e),
                    raw_status_code=e.response.status_code,
                )
            except Exception as e:  # noqa: BLE001
                logger.exception("dev.to publish failed")
                return PlatformOutcome(ok=False, error=str(e))

        async def run_hashnode() -> PlatformOutcome:
            hn_host = self._settings.hashnode_publication_host.strip()
            if not self._settings.hashnode_token or not hn_host:
                return PlatformOutcome(ok=False, error=_hashnode_not_configured_message())
            try:
                client = self._hashnode()
                draft_id, slug = await client.create_draft(
                    title=data.title,
                    content_markdown=data.body_markdown,
                    tags=data.tags,
                    subtitle=data.description,
                    canonical_url=data.canonical_url,
                )
                if data.hashnode_published:
                    url = await client.publish_draft(draft_id)
                    return PlatformOutcome(ok=True, url=url)
                return PlatformOutcome(
                    ok=True,
                    url=None,
                    note=f"Hashnode draft created (slug={slug!r}); open Hashnode to publish.",
                )
            except HashnodeApiError as e:
                return PlatformOutcome(ok=False, error=str(e))
            except Exception as e:  # noqa: BLE001
                logger.exception("Hashnode publish failed")
                return PlatformOutcome(ok=False, error=str(e))

        dev_to, hashnode = await asyncio.gather(run_devto(), run_hashnode())
        return PublishArticleResult(dev_to=dev_to, hashnode=hashnode)


def _format_http_error(label: str, exc: httpx.HTTPStatusError) -> str:
    try:
        body = exc.response.text[:2000]
    except Exception:  # noqa: BLE001
        body = ""
    return f"{label} HTTP {exc.response.status_code}: {body or exc!s}"
