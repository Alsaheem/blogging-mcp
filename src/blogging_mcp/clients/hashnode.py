"""Hashnode GraphQL API client (https://gql.hashnode.com, PAT auth)."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GQL_URL = "https://gql.hashnode.com"

PUBLICATION_QUERY = """
query PublicationForMcp($host: String!) {
  publication(host: $host) {
    id
    title
  }
}
"""

CREATE_DRAFT_MUTATION = """
mutation CreateDraft($input: CreateDraftInput!) {
  createDraft(input: $input) {
    draft {
      id
      slug
    }
  }
}
"""

PUBLISH_DRAFT_MUTATION = """
mutation PublishDraft($input: PublishDraftInput!) {
  publishDraft(input: $input) {
    post {
      url
    }
  }
}
"""

POST_QUERY = """
query PostForMcp($id: ID!) {
  post(id: $id) {
    id
    title
    subtitle
    slug
    url
    content {
      markdown
    }
    tags {
      name
      slug
    }
  }
}
"""

DRAFT_QUERY = """
query DraftForMcp($id: ObjectId!) {
  draft(id: $id) {
    id
    title
    subtitle
    slug
    content {
      markdown
    }
    tags {
      name
      slug
    }
  }
}
"""

PUBLICATION_POSTS_QUERY = """
query PublicationPosts($host: String!, $first: Int!, $after: String) {
  publication(host: $host) {
    id
    posts(first: $first, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        node {
          id
          title
          slug
          url
        }
      }
    }
  }
}
"""

PUBLICATION_DRAFTS_QUERY = """
query PublicationDrafts($host: String!, $first: Int!) {
  publication(host: $host) {
    id
    drafts(first: $first) {
      edges {
        node {
          id
          title
          slug
        }
      }
    }
  }
}
"""

UPDATE_POST_MUTATION = """
mutation UpdatePost($input: UpdatePostInput!) {
  updatePost(input: $input) {
    post {
      id
      title
      slug
      url
      content {
        markdown
      }
    }
  }
}
"""

REMOVE_POST_MUTATION = """
mutation RemovePost($input: RemovePostInput!) {
  removePost(input: $input) {
    post {
      id
      title
      url
    }
  }
}
"""


class HashnodeApiError(Exception):
    """GraphQL or HTTP failure from Hashnode."""


def _tag_slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s or "tag"


class HashnodeClient:
    """Async Hashnode API using a Personal Access Token (raw value in Authorization header)."""

    def __init__(self, token: str, publication_host: str, *, timeout: float) -> None:
        if not token:
            raise ValueError("Hashnode token is empty")
        if not publication_host.strip():
            raise ValueError("Hashnode publication host is empty")
        self._token = token
        self._host = publication_host.strip()
        self._timeout = timeout
        self._publication_id: str | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self._token,
            "Content-Type": "application/json",
        }

    async def _execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {"query": query, "variables": variables}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(GQL_URL, headers=self._headers(), json=payload)
            r.raise_for_status()
            body = r.json()
        errs = body.get("errors")
        if errs:
            msgs = "; ".join(str(e.get("message", e)) for e in errs)
            raise HashnodeApiError(msgs)
        data = body.get("data")
        if data is None:
            raise HashnodeApiError("Empty GraphQL data")
        return data

    async def resolve_publication_id(self) -> str:
        if self._publication_id:
            return self._publication_id
        data = await self._execute(PUBLICATION_QUERY, {"host": self._host})
        pub = data.get("publication")
        if not pub or not pub.get("id"):
            raise HashnodeApiError(
                f"No publication found for host {self._host!r}. "
                "Use your blog host (e.g. username.hashnode.dev or custom domain)."
            )
        self._publication_id = str(pub["id"])
        logger.debug("Hashnode publication id resolved for %s", self._host)
        return self._publication_id

    async def verify_publication(self) -> None:
        await self.resolve_publication_id()

    async def create_draft(
        self,
        *,
        title: str,
        content_markdown: str,
        tags: list[str],
        subtitle: str | None,
        canonical_url: str | None,
    ) -> tuple[str, str]:
        """Returns (draft_id, slug)."""
        pub_id = await self.resolve_publication_id()
        tag_input = [{"name": t, "slug": _tag_slug(t)} for t in tags[:10]]
        inp: dict[str, Any] = {
            "publicationId": pub_id,
            "title": title,
            "contentMarkdown": content_markdown,
            "tags": tag_input,
        }
        if subtitle:
            inp["subtitle"] = subtitle
        if canonical_url:
            inp["originalArticleURL"] = canonical_url
        data = await self._execute(CREATE_DRAFT_MUTATION, {"input": inp})
        draft = (data.get("createDraft") or {}).get("draft") or {}
        did = draft.get("id")
        slug = draft.get("slug") or ""
        if not did:
            raise HashnodeApiError("createDraft returned no draft id")
        return str(did), str(slug)

    async def publish_draft(self, draft_id: str) -> str:
        data = await self._execute(PUBLISH_DRAFT_MUTATION, {"input": {"draftId": draft_id}})
        post = (data.get("publishDraft") or {}).get("post") or {}
        url = post.get("url")
        if not url:
            raise HashnodeApiError("publishDraft returned no post url")
        return str(url)

    async def get_post(self, post_id: str) -> dict[str, Any]:
        data = await self._execute(POST_QUERY, {"id": post_id})
        post = data.get("post")
        if not post:
            raise HashnodeApiError("post not found")
        return dict(post)

    async def get_draft(self, draft_id: str) -> dict[str, Any]:
        data = await self._execute(DRAFT_QUERY, {"id": draft_id})
        draft = data.get("draft")
        if not draft:
            raise HashnodeApiError("draft not found")
        return dict(draft)

    async def list_posts(self, *, first: int = 20, after: str | None = None) -> dict[str, Any]:
        await self.resolve_publication_id()
        data = await self._execute(
            PUBLICATION_POSTS_QUERY,
            {"host": self._host, "first": min(first, 50), "after": after},
        )
        pub = data.get("publication")
        if not pub:
            raise HashnodeApiError("publication not found")
        return dict(pub)

    async def list_drafts(self, *, first: int = 20) -> dict[str, Any]:
        await self.resolve_publication_id()
        data = await self._execute(
            PUBLICATION_DRAFTS_QUERY,
            {"host": self._host, "first": min(first, 50)},
        )
        pub = data.get("publication")
        if not pub:
            raise HashnodeApiError("publication not found")
        return dict(pub)

    async def update_post(
        self,
        post_id: str,
        *,
        title: str | None = None,
        subtitle: str | None = None,
        content_markdown: str | None = None,
        slug: str | None = None,
        canonical_url: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        inp: dict[str, Any] = {"id": post_id}
        if title is not None:
            inp["title"] = title
        if subtitle is not None:
            inp["subtitle"] = subtitle
        if content_markdown is not None:
            inp["contentMarkdown"] = content_markdown
        if slug is not None:
            inp["slug"] = slug
        if canonical_url is not None:
            inp["originalArticleURL"] = canonical_url
        if tags is not None:
            inp["tags"] = [{"name": t, "slug": _tag_slug(t)} for t in tags[:10]]
        if len(inp) == 1:
            raise HashnodeApiError("update_post: provide at least one field to change besides id")
        data = await self._execute(UPDATE_POST_MUTATION, {"input": inp})
        post = (data.get("updatePost") or {}).get("post")
        if not post:
            raise HashnodeApiError("updatePost returned no post")
        return dict(post)

    async def remove_post(self, post_id: str) -> dict[str, Any]:
        data = await self._execute(REMOVE_POST_MUTATION, {"input": {"id": post_id}})
        post = (data.get("removePost") or {}).get("post")
        if not post:
            raise HashnodeApiError("removePost returned no post")
        return dict(post)
