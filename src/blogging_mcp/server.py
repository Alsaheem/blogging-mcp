from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from blogging_mcp.clients.devto import DevtoApiError, DevtoClient
from blogging_mcp.clients.hashnode import HashnodeApiError, HashnodeClient
from blogging_mcp.config import Settings
from blogging_mcp.models.article import PublishArticleInput
from blogging_mcp.services.publisher import Publisher

mcp = FastMCP(
    "Blogging MCP",
    instructions=(
        "Publish Markdown articles to dev.to and Hashnode (GraphQL API). "
        "Use verify_credentials to test configuration. "
        "Use publish_article to create on both platforms. "
        "CRUD: devto_get/list/update/delete_article; "
        "hashnode_get_post/draft, list_posts/drafts, update/remove_post. "
        "Create remains publish_article. "
        "Hashnode has no public updateDraft API—edit drafts in the UI or use hashnode_update_post "
        "after publish."
    ),
)


def _settings() -> Settings:
    return Settings()


def _devto() -> DevtoClient:
    s = _settings()
    if not s.devto_api_key:
        raise DevtoApiError("DEVTO_API_KEY is not set")
    return DevtoClient(s.devto_api_key, timeout=s.mcp_http_timeout)


def _hashnode() -> HashnodeClient:
    s = _settings()
    if not s.hashnode_token or not s.hashnode_publication_host.strip():
        raise HashnodeApiError(
            "HASHNODE_TOKEN and HASHNODE_PUBLICATION_HOST must be set for Hashnode tools"
        )
    return HashnodeClient(
        s.hashnode_token,
        s.hashnode_publication_host,
        timeout=s.mcp_http_timeout,
    )


def _ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def _fail(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


@mcp.tool
async def publish_article(
    title: str,
    body_markdown: str,
    tags: list[str] | None = None,
    devto_published: bool = True,
    hashnode_published: bool = True,
    canonical_url: str | None = None,
    cover_image: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Create and publish one article to dev.to and Hashnode from the same Markdown body.

    Returns a dict with `dev_to` and `hashnode` outcomes (ok, url, error, note).
    If hashnode_published is false, Hashnode stays a draft (see `note`).
    """
    data = PublishArticleInput(
        title=title,
        body_markdown=body_markdown,
        tags=tags or [],
        devto_published=devto_published,
        hashnode_published=hashnode_published,
        canonical_url=canonical_url,
        cover_image=cover_image,
        description=description,
    )
    publisher = Publisher(_settings())
    result = await publisher.publish_article(data)
    return result.model_dump()


@mcp.tool
async def verify_credentials() -> dict[str, Any]:
    """Check dev.to API key and Hashnode publication access (no publishing)."""
    publisher = Publisher(_settings())
    result = await publisher.verify_credentials()
    return result.model_dump()


@mcp.tool
async def devto_get_article(article_id: int) -> dict[str, Any]:
    """Fetch one dev.to article by numeric id (GET /api/articles/{id})."""
    try:
        data = await _devto().get_article(article_id)
        return _ok(data)
    except DevtoApiError as e:
        return _fail(str(e))


@mcp.tool
async def devto_list_my_articles(
    scope: str = "published",
    page: int = 1,
    per_page: int = 30,
) -> dict[str, Any]:
    """List your dev.to articles. scope: published | unpublished | all (paginated)."""
    if scope not in ("published", "unpublished", "all"):
        return _fail("scope must be one of: published, unpublished, all")
    try:
        data = await _devto().list_my_articles(scope=scope, page=page, per_page=per_page)
        return _ok(data)
    except DevtoApiError as e:
        return _fail(str(e))


@mcp.tool
async def devto_update_article(
    article_id: int,
    title: str | None = None,
    body_markdown: str | None = None,
    published: bool | None = None,
    tags: list[str] | None = None,
    canonical_url: str | None = None,
    cover_image: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update a dev.to article you own. Pass only fields to change. Max 4 tags."""
    if tags is not None and len(tags) > 4:
        return _fail("dev.to allows at most 4 tags")
    try:
        data = await _devto().update_article(
            article_id,
            title=title,
            body_markdown=body_markdown,
            published=published,
            tags=tags,
            canonical_url=canonical_url,
            cover_image=cover_image,
            description=description,
        )
        return _ok(data)
    except DevtoApiError as e:
        return _fail(str(e))


@mcp.tool
async def devto_delete_article(article_id: int) -> dict[str, Any]:
    """Permanently delete a dev.to article you own (DELETE /api/articles/{id})."""
    try:
        await _devto().delete_article(article_id)
        return _ok({"article_id": article_id, "deleted": True})
    except DevtoApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_get_post(post_id: str) -> dict[str, Any]:
    """Fetch one published Hashnode post by id (GraphQL `post`)."""
    try:
        data = await _hashnode().get_post(post_id)
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_get_draft(draft_id: str) -> dict[str, Any]:
    """Fetch one Hashnode draft by id (GraphQL `draft`)."""
    try:
        data = await _hashnode().get_draft(draft_id)
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_list_posts(first: int = 20, after: str | None = None) -> dict[str, Any]:
    """List posts for your publication (cursor pagination; `after` from previous pageInfo)."""
    try:
        data = await _hashnode().list_posts(first=first, after=after)
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_list_drafts(first: int = 20) -> dict[str, Any]:
    """List drafts for your publication."""
    try:
        data = await _hashnode().list_drafts(first=first)
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_update_post(
    post_id: str,
    title: str | None = None,
    subtitle: str | None = None,
    content_markdown: str | None = None,
    slug: str | None = None,
    canonical_url: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Update a published Hashnode post. Pass only fields to change."""
    try:
        data = await _hashnode().update_post(
            post_id,
            title=title,
            subtitle=subtitle,
            content_markdown=content_markdown,
            slug=slug,
            canonical_url=canonical_url,
            tags=tags,
        )
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))


@mcp.tool
async def hashnode_remove_post(post_id: str) -> dict[str, Any]:
    """Delete a published Hashnode post by id (`removePost`)."""
    try:
        data = await _hashnode().remove_post(post_id)
        return _ok(data)
    except HashnodeApiError as e:
        return _fail(str(e))
