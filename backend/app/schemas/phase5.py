from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Application status / item_type literals
# ---------------------------------------------------------------------------

ApplicationStatus = Literal[
    "draft",
    "analyzing",
    "improving_cv",
    "ready_to_apply",
    "interview_prep",
    "applied",
    "archived",
]

CareerProfileItemType = Literal[
    "skill",
    "project",
    "experience",
    "education",
    "certification",
    "achievement",
    "link",
]

ReadinessLevel = Literal["not_started", "needs_work", "almost_ready", "ready"]


# ---------------------------------------------------------------------------
# Application schemas
# ---------------------------------------------------------------------------

class ApplicationCreate(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)
    jd_text: str = Field(min_length=1)
    target_role: Optional[str] = Field(default=None, max_length=255)


class ApplicationUpdate(BaseModel):
    job_title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)
    jd_text: Optional[str] = Field(default=None, min_length=1)
    target_role: Optional[str] = Field(default=None, max_length=255)
    status: Optional[ApplicationStatus] = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    job_title: str
    company_name: Optional[str]
    jd_text: str
    target_role: Optional[str]
    status: str
    best_analysis_job_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int


class AttachAnalysisResponse(BaseModel):
    application_id: str
    best_analysis_job_id: str


class ReadinessResponse(BaseModel):
    application_id: str
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


# ---------------------------------------------------------------------------
# Career profile schemas
# ---------------------------------------------------------------------------

class CareerProfileItemCreate(BaseModel):
    item_type: CareerProfileItemType
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    skills_json: Optional[List[Any]] = None
    evidence_text: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=255)


class CareerProfileItemUpdate(BaseModel):
    item_type: Optional[CareerProfileItemType] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    skills_json: Optional[List[Any]] = None
    evidence_text: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=255)


class CareerProfileItemResponse(BaseModel):
    id: str
    user_id: str
    item_type: str
    title: str
    description: Optional[str]
    skills_json: Optional[List[Any]]
    evidence_text: Optional[str]
    source: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareerProfileItemListResponse(BaseModel):
    items: List[CareerProfileItemResponse]
    total: int


# ---------------------------------------------------------------------------
# Application artifact schemas
# ---------------------------------------------------------------------------

ArtifactType = Literal[
    "application_package",
    "cover_letter_draft",
    "interview_practice_result",
    "readiness_summary",
]


class ArtifactResponse(BaseModel):
    id: str
    application_id: str
    artifact_type: str
    payload_json: Any
    created_at: datetime


class ArtifactGeneratedResponse(BaseModel):
    application_id: str
    artifact_id: str
    status: str
    artifact_type: str


class CoverLetterPatch(BaseModel):
    opening: Optional[str] = None
    why_role_company: Optional[str] = None
    relevant_evidence: Optional[List[Any]] = None
    contribution_fit: Optional[str] = None
    closing: Optional[str] = None
    review_notes: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Interview practice schemas
# ---------------------------------------------------------------------------

class InterviewQuestionItem(BaseModel):
    question_id: str
    question: str
    type: str
    related_jd_requirement: str
    related_cv_evidence: List[str]
    why_this_question: str


class InterviewQuestionsResponse(BaseModel):
    application_id: str
    questions: List[InterviewQuestionItem]
    disclaimer: str


class InterviewAnswerCreate(BaseModel):
    question_id: str
    question: str
    answer_text: str


class InterviewAnswerResponse(BaseModel):
    answer_id: str
    application_id: str
    question: str
    answer_text: str
    rubric: Any
    feedback: Any
    created_at: datetime


class InterviewAnswerSummary(BaseModel):
    answer_id: str
    question: str
    rubric: Any
    created_at: datetime


class InterviewAnswerListResponse(BaseModel):
    application_id: str
    answers: List[InterviewAnswerSummary]
    total: int
