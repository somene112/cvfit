"""Phase 6 Shareable Readiness schemas.

Share links expose a redacted readiness summary to anyone holding the raw token.
The raw token is returned exactly once (on create) and never persisted/echoed
afterward. ``token_hash`` is never exposed in any response.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ShareTargetType = Literal["target_job", "application"]


class ShareVisibility(BaseModel):
    summary_only: bool = True
    include_score_breakdown: bool = False
    include_package: bool = False
    include_cover_letter: bool = False
    include_learning_roadmap: bool = False
    hide_raw_cv: bool = True
    hide_raw_jd: bool = True


class ShareLinkCreate(BaseModel):
    target_type: ShareTargetType
    target_id: str
    visibility: Optional[ShareVisibility] = None
    expires_at: Optional[datetime] = None


class ShareLinkUpdate(BaseModel):
    visibility: Optional[ShareVisibility] = None
    expires_at: Optional[datetime] = None


class ShareLinkResponse(BaseModel):
    """Owner-facing metadata. Never includes the raw token or token_hash."""

    id: str
    target_type: str
    target_id: str
    visibility: ShareVisibility
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class ShareLinkCreateResponse(ShareLinkResponse):
    """Adds the raw token + relative public path, returned only once on create."""

    share_token: str = Field(description="Raw token — shown once; store it now, it cannot be retrieved again.")
    public_path: str


class ShareLinkListResponse(BaseModel):
    items: List[ShareLinkResponse]
    total: int


class PublicReadinessView(BaseModel):
    """Redacted, unauthenticated public view. No owner identity, no raw CV/JD."""

    target_type: str
    job_title: str
    company_name: Optional[str]
    readiness_level: str
    summary: str
    fit_score: Optional[int] = None  # only when include_score_breakdown
    score_breakdown: Optional[dict] = None  # only when include_score_breakdown
    learning_focus: Optional[List[str]] = None  # only when include_learning_roadmap
    disclaimer: str = (
        "This is a shared readiness summary. It is a preparation signal based on the "
        "candidate's CV/JD evidence and does not guarantee interview or hiring outcomes."
    )
