from __future__ import annotations

from pydantic import BaseModel, Field


class PublishArticleInput(BaseModel):
    """Validated input for cross-platform publish (used internally and for tests)."""

    title: str = Field(..., min_length=1, max_length=500)
    body_markdown: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    devto_published: bool = True
    hashnode_published: bool = Field(
        default=True,
        description="If true, publish on Hashnode after createDraft; if false, leave draft only",
    )
    canonical_url: str | None = None
    cover_image: str | None = Field(default=None, description="dev.to cover image URL only")
    description: str | None = Field(
        default=None,
        description="dev.to subtitle; also Hashnode draft subtitle when set",
    )
