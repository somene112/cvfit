"""Phase 6 Learning Roadmap schemas.

Tasks are derived from the user's own analysis result (missing skills, weak
evidence, interview-prep items). Constrained fields are validated with Literals;
responses use plain strings so existing rows are always serializable.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


LearningPriority = Literal["high", "medium", "low"]
LearningTaskType = Literal["article", "project", "practice", "interview_prep", "profile_evidence"]
LearningStatus = Literal["todo", "in_progress", "done"]


class RoadmapGenerateRequest(BaseModel):
    target_job_id: Optional[str] = None
    application_id: Optional[str] = None
    analysis_job_id: Optional[str] = None
    max_tasks: int = Field(default=8, ge=1, le=30)
    # Optional UI language ("vi"/"en"). Defaults to English generation so existing
    # clients are unaffected; the Vietnamese-first frontend sends "vi".
    language: Optional[str] = None


class LearningTaskResponse(BaseModel):
    id: str
    user_id: str
    target_job_id: Optional[str]
    application_id: Optional[str]
    analysis_job_id: Optional[str]
    skill: str
    category: Optional[str]
    priority: str
    task_type: str
    title: str
    description: Optional[str]
    evidence_to_add: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class RoadmapGenerateResponse(BaseModel):
    tasks: List[LearningTaskResponse]
    total: int
    limitations: str


class LearningTaskListResponse(BaseModel):
    items: List[LearningTaskResponse]
    total: int


class LearningTaskUpdate(BaseModel):
    status: Optional[LearningStatus] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    evidence_to_add: Optional[str] = None
    priority: Optional[LearningPriority] = None
