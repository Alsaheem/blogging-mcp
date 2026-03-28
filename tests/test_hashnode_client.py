import json

import httpx
import pytest
import respx

from blogging_mcp.clients.hashnode import HashnodeApiError, HashnodeClient


@pytest.mark.asyncio
@respx.mock
async def test_resolve_and_publish_flow() -> None:
    calls: list[str] = []

    def responder(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}") if request.content else {}
        q = body.get("query", "")
        if "publication(" in q:
            calls.append("pub")
            return httpx.Response(
                200,
                json={"data": {"publication": {"id": "pid-9", "title": "T"}}},
            )
        if "createDraft" in q:
            calls.append("create")
            return httpx.Response(
                200,
                json={"data": {"createDraft": {"draft": {"id": "d1", "slug": "s"}}}},
            )
        if "publishDraft" in q:
            calls.append("publish")
            return httpx.Response(
                200,
                json={"data": {"publishDraft": {"post": {"url": "https://x.hashnode.dev/s"}}}},
            )
        return httpx.Response(400, json={"errors": [{"message": "bad"}]})

    respx.post("https://gql.hashnode.com").mock(side_effect=responder)

    c = HashnodeClient("pat-token", "x.hashnode.dev", timeout=10.0)
    await c.resolve_publication_id()
    await c.resolve_publication_id()
    assert calls.count("pub") == 1
    did, slug = await c.create_draft(
        title="T",
        content_markdown="# Hi",
        tags=["a"],
        subtitle=None,
        canonical_url=None,
    )
    assert did == "d1"
    assert slug == "s"
    url = await c.publish_draft(did)
    assert "hashnode" in url


@pytest.mark.asyncio
@respx.mock
async def test_graphql_errors() -> None:
    respx.post("https://gql.hashnode.com").mock(
        return_value=httpx.Response(
            200,
            json={"errors": [{"message": "nope"}]},
        )
    )
    c = HashnodeClient("t", "h.hashnode.dev", timeout=5.0)
    with pytest.raises(HashnodeApiError, match="nope"):
        await c.resolve_publication_id()


@pytest.mark.asyncio
@respx.mock
async def test_update_and_remove_post() -> None:
    def responder(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}") if request.content else {}
        q = body.get("query", "")
        if "publication(" in q:
            return httpx.Response(
                200,
                json={"data": {"publication": {"id": "pid-1", "title": "T"}}},
            )
        if "updatePost" in q:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "updatePost": {
                            "post": {"id": "p1", "title": "New", "url": "https://h.hashnode.dev/x"}
                        }
                    }
                },
            )
        if "removePost" in q:
            return httpx.Response(
                200,
                json={"data": {"removePost": {"post": {"id": "p1", "title": "Gone"}}}},
            )
        return httpx.Response(400, json={"errors": [{"message": "bad"}]})

    respx.post("https://gql.hashnode.com").mock(side_effect=responder)

    c = HashnodeClient("t", "h.hashnode.dev", timeout=5.0)
    out = await c.update_post("p1", title="New")
    assert out["title"] == "New"
    out2 = await c.remove_post("p1")
    assert out2["id"] == "p1"
