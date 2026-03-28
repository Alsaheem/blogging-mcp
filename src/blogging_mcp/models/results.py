from __future__ import annotations

from pydantic import BaseModel, Field


class PlatformOutcome(BaseModel):
    ok: bool
    url: str | None = None
    error: str | None = None
    raw_status_code: int | None = Field(default=None, description="HTTP status if applicable")
    note: str | None = Field(default=None, description="Extra context (e.g. Hashnode draft-only)")


class PublishArticleResult(BaseModel):
    dev_to: PlatformOutcome
    hashnode: PlatformOutcome


class VerifyCredentialsResult(BaseModel):
    dev_to: PlatformOutcome
    hashnode: PlatformOutcome
