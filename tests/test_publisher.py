import json

import httpx
import pytest
import respx

from blogging_mcp.config import Settings
from blogging_mcp.models.article import PublishArticleInput
from blogging_mcp.services.publisher import Publisher


def _gql_response(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content.decode() or "{}") if request.content else {}
    q = body.get("query", "")
    if "publication(" in q:
        return httpx.Response(
            200,
            json={"data": {"publication": {"id": "pub-1", "title": "Blog"}}},
        )
    if "createDraft" in q:
        return httpx.Response(
            200,
            json={"data": {"createDraft": {"draft": {"id": "draft-1", "slug": "hello"}}}},
        )
    if "publishDraft" in q:
        return httpx.Response(
            200,
            json={
                "data": {"publishDraft": {"post": {"url": "https://writer.hashnode.dev/hello"}}},
            },
        )
    return httpx.Response(200, json={"errors": [{"message": f"unexpected gql: {q[:40]}"}]})


@pytest.mark.asyncio
@respx.mock
async def test_publish_both_success(settings_both: Settings) -> None:
    respx.post("https://dev.to/api/articles").mock(
        return_value=httpx.Response(
            201,
            json={"url": "https://dev.to/u/post"},
        )
    )
    respx.post("https://gql.hashnode.com").mock(side_effect=_gql_response)

    pub = Publisher(settings_both)
    inp = PublishArticleInput(title="Hi", body_markdown="Hello")
    r = await pub.publish_article(inp)
    assert r.dev_to.ok is True
    assert r.dev_to.url == "https://dev.to/u/post"
    assert r.hashnode.ok is True
    assert r.hashnode.url == "https://writer.hashnode.dev/hello"


@pytest.mark.asyncio
@respx.mock
async def test_publish_partial_devto_fails(settings_both: Settings) -> None:
    respx.post("https://dev.to/api/articles").mock(return_value=httpx.Response(401, text="nope"))
    respx.post("https://gql.hashnode.com").mock(side_effect=_gql_response)

    pub = Publisher(settings_both)
    inp = PublishArticleInput(title="Hi", body_markdown="Hello")
    r = await pub.publish_article(inp)
    assert r.dev_to.ok is False
    assert r.dev_to.raw_status_code == 401
    assert r.hashnode.ok is True


@pytest.mark.asyncio
@respx.mock
async def test_verify_missing_keys() -> None:
    settings = Settings(
        devto_api_key="",
        hashnode_token="",
        hashnode_publication_host="",
    )
    pub = Publisher(settings)
    r = await pub.verify_credentials()
    assert r.dev_to.ok is False
    assert "DEVTO" in (r.dev_to.error or "")
    assert r.hashnode.ok is False
    assert "Hashnode not configured" in (r.hashnode.error or "")


@pytest.mark.asyncio
@respx.mock
async def test_hashnode_draft_only_note(settings_both: Settings) -> None:
    respx.post("https://dev.to/api/articles").mock(
        return_value=httpx.Response(201, json={"url": "https://dev.to/x"}),
    )
    respx.post("https://gql.hashnode.com").mock(side_effect=_gql_response)

    pub = Publisher(settings_both)
    inp = PublishArticleInput(
        title="Hi",
        body_markdown="Body",
        hashnode_published=False,
    )
    r = await pub.publish_article(inp)
    assert r.hashnode.ok is True
    assert r.hashnode.url is None
    assert r.hashnode.note and "draft" in r.hashnode.note.lower()
