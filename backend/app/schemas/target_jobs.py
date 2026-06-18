"""Phase 6 Target Jobs schemas.

Target Jobs are a product layer over the existing ``applications`` table. Input
schemas validate the Phase 6 status vocabulary; response ``status`` is a plain
string so applications created through Phase 5 flows (with Phase 5 statuses) can
also be surfaced in the unified workspace without validation errors.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# Phase 6 Target Jobs status vocabulary (used for input validation only).
TargetJobStatus = Literal[
    "saved",
    "analyzing",
    "ready_to_apply",
    "interviewing",
    "applied",
    "rejected",
    "offer",
    "archived",
]

ReadinessLevel = Literal["not_started", "needs_work", "almost_ready", "ready"]


class TargetJobCreate(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    jd_text: str = Field(min_length=1)
    company_name: Optional[str] = Field(default=None, max_length=255)
    target_role: Optional[str] = Field(default=None, max_length=255)
    source_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[TargetJobStatus] = None


class TargetJobUpdate(BaseModel):
    job_title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)
    jd_text: Optional[str] = Field(default=None, min_length=1)
    target_role: Optional[str] = Field(default=None, max_length=255)
    source_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[TargetJobStatus] = None


class TargetJobResponse(BaseModel):
    id: str
    user_id: str
    job_title: str
    company_name: Optional[str]
    jd_text: str
    target_role: Optional[str]
    source_url: Optional[str]
    status: str
    best_analysis_job_id: Optional[str]
    last_readiness_score: Optional[int]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class TargetJobListResponse(BaseModel):
    items: List[TargetJobResponse]
    total: int


class AttachAnalysisResponse(BaseModel):
    target_job_id: str
    best_analysis_job_id: str
    last_readiness_score: Optional[int]


class TargetJobReadinessResponse(BaseModel):
    target_job_id: str
    status: str
    best_analysis_job_id: Optional[str]
    fit_score: Optional[float]
    readiness_level: ReadinessLevel
    summary: str
    next_actions: List[str]
    disclaimer: str = (
        "Readiness is a preparation signal based on available CV/JD evidence. "
        "It does not guarantee interview or hiring outcomes."
    )


class TargetJobPackageResponse(BaseModel):
    target_job_id: str
    has_package: bool
    artifact_id: Optional[str] = None
    artifact_type: Optional[str] = None
    payload_json: Optional[dict] = None
    created_at: Optional[datetime] = None
