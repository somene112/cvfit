from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class UploadResponse(BaseModel):
    cv_file_id: str
    cv_id: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None

class JobCreateResponse(BaseModel):
    job_id: str
    access_token: str
    status: str = "queued"

class JobReanalysisResponse(BaseModel):
    job_id: str
    access_token: str
    parent_job_id: str
    analysis_group_id: str
    revision_number: int
    status: str = "queued"

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    error_message: Optional[str] = None
    error: Optional[str] = None

class JobResultResponse(BaseModel):
    job_id: str
    result: Any
    overall_fit_score: Optional[float] = None
    summary: Optional[str] = None
    strengths: Optional[list[Any]] = None
    missing_skills: Optional[list[Any]] = None
    recommendations: Optional[list[Any]] = None
    evidence: Optional[list[Any]] = None

class JobHistoryItemResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    overall_fit_score: Optional[float] = None
    has_report: bool
    target_role: Optional[str] = None
    parent_job_id: Optional[str] = None
    analysis_group_id: Optional[str] = None
    revision_number: int = 1

class JobHistoryResponse(BaseModel):
    items: list[JobHistoryItemResponse]

class JobComparisonResponse(BaseModel):
    base_job_id: str
    new_job_id: str
    base_score: Optional[float] = None
    new_score: Optional[float] = None
    score_delta: Optional[float] = None
    breakdown_delta: dict[str, float] = Field(default_factory=dict)
    resolved_missing_skills: list[Any] = Field(default_factory=list)
    still_missing_skills: list[Any] = Field(default_factory=list)
    newly_matched_skills: list[Any] = Field(default_factory=list)
    new_evidence: list[Any] = Field(default_factory=list)
    keyword_stuffing_warnings: list[Any] = Field(default_factory=list)
    improvement_summary: str
    next_actions: list[Any] = Field(default_factory=list)
