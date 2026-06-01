from pydantic import BaseModel
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

class JobHistoryResponse(BaseModel):
    items: list[JobHistoryItemResponse]
