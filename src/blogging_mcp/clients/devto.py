from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEVTO_API_BASE = "https://dev.to/api"


class DevtoApiError(Exception):
    """dev.to REST API failure."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class DevtoClient:
    """dev.to REST API (async)."""

    def __init__(self, api_key: str, *, timeout: float) -> None:
        if not api_key:
            raise ValueError("dev.to API key is empty")
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_me(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{DEVTO_API_BASE}/users/me", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def _raise_for_status(self, r: httpx.Response, *, label: str) -> None:
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            body = ""
            try:
                body = e.response.text[:2000]
            except Exception:  # noqa: BLE001
                pass
            code = e.response.status_code
            raise DevtoApiError(
                f"{label} HTTP {code}: {body or e!s}",
                status_code=code,
            ) from e

    async def create_article(
        self,
        *,
        title: str,
        body_markdown: str,
        published: bool,
        tags: list[str],
        canonical_url: str | None,
        cover_image: str | None,
        description: str | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "article": {
                "title": title,
                "body_markdown": body_markdown,
                "published": published,
                "tags": tags,
            }
        }
        if canonical_url:
            payload["article"]["canonical_url"] = canonical_url
        if cover_image:
            payload["article"]["cover_image"] = cover_image
        if description:
            payload["article"]["description"] = description

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(
                f"{DEVTO_API_BASE}/articles",
                headers=self._headers(),
                json=payload,
            )
            if r.status_code == 429:
                logger.warning("dev.to rate limited: %s", r.text[:500])
            await self._raise_for_status(r, label="dev.to create article")
            return r.json()

    async def get_article(self, article_id: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(
                f"{DEVTO_API_BASE}/articles/{article_id}",
                headers=self._headers(),
            )
            await self._raise_for_status(r, label="dev.to get article")
            return r.json()

    async def list_my_articles(
        self,
        *,
        scope: str = "published",
        page: int = 1,
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        path = {
            "published": "/articles/me/published",
            "unpublished": "/articles/me/unpublished",
            "all": "/articles/me/all",
        }.get(scope, "/articles/me/published")
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(
                f"{DEVTO_API_BASE}{path}",
                headers=self._headers(),
                params={"page": page, "per_page": per_page},
            )
            await self._raise_for_status(r, label="dev.to list my articles")
            data = r.json()
            if not isinstance(data, list):
                raise DevtoApiError("dev.to list expected a JSON array")
            return data

    async def update_article(
        self,
        article_id: int,
        *,
        title: str | None = None,
        body_markdown: str | None = None,
        published: bool | None = None,
        tags: list[str] | None = None,
        canonical_url: str | None = None,
        cover_image: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        article: dict[str, Any] = {}
        if title is not None:
            article["title"] = title
        if body_markdown is not None:
            article["body_markdown"] = body_markdown
        if published is not None:
            article["published"] = published
        if tags is not None:
            article["tags"] = tags
        if canonical_url is not None:
            article["canonical_url"] = canonical_url
        if cover_image is not None:
            article["cover_image"] = cover_image
        if description is not None:
            article["description"] = description
        if not article:
            raise DevtoApiError("update_article: provide at least one field to change")
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.put(
                f"{DEVTO_API_BASE}/articles/{article_id}",
                headers=self._headers(),
                json={"article": article},
            )
            await self._raise_for_status(r, label="dev.to update article")
            return r.json()

    async def delete_article(self, article_id: int) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.delete(
                f"{DEVTO_API_BASE}/articles/{article_id}",
                headers=self._headers(),
            )
            await self._raise_for_status(r, label="dev.to delete article")
