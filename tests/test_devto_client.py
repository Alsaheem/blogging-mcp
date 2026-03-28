import httpx
import pytest
import respx

from blogging_mcp.clients.devto import DevtoClient


@pytest.mark.asyncio
@respx.mock
async def test_get_me_success() -> None:
    respx.get("https://dev.to/api/users/me").mock(
        return_value=httpx.Response(200, json={"username": "alice"})
    )
    client = DevtoClient("k", timeout=5.0)
    data = await client.get_me()
    assert data["username"] == "alice"


@pytest.mark.asyncio
@respx.mock
async def test_create_article_success() -> None:
    respx.post("https://dev.to/api/articles").mock(
        return_value=httpx.Response(
            201,
            json={"url": "https://dev.to/tester/hello-123", "title": "Hello"},
        )
    )
    client = DevtoClient("k", timeout=5.0)
    data = await client.create_article(
        title="Hello",
        body_markdown="# Hi",
        published=True,
        tags=["a", "b"],
        canonical_url=None,
        cover_image=None,
        description=None,
    )
    assert "dev.to" in data["url"]


@pytest.mark.asyncio
@respx.mock
async def test_get_article_success() -> None:
    respx.get("https://dev.to/api/articles/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "title": "T"})
    )
    data = await DevtoClient("k", timeout=5.0).get_article(42)
    assert data["id"] == 42


@pytest.mark.asyncio
@respx.mock
async def test_delete_article_success() -> None:
    respx.delete("https://dev.to/api/articles/99").mock(return_value=httpx.Response(204))
    await DevtoClient("k", timeout=5.0).delete_article(99)
