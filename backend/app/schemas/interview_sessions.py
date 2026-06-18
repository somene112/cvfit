"""Phase 6 Interview Practice v2 schemas.

Sessions, questions, and answers. Constrained fields validated with Literals;
responses use plain strings for forward-compatibility. Scoring uses the
six-dimension rubric: relevance, evidence, clarity, structure, confidence, risk.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


QuestionType = Literal["technical", "behavioral", "project", "HR", "gap_check"]
Difficulty = Literal["easy", "medium", "hard"]
SessionType = Literal["mixed", "technical", "behavioral", "project", "HR", "gap_check"]
SessionStatus = Literal["active", "completed", "archived"]


class SessionCreateRequest(BaseModel):
    target_job_id: Optional[str] = None
    application_id: Optional[str] = None
    analysis_job_id: Optional[str] = None
    session_type: SessionType = "mixed"
    difficulty: Difficulty = "medium"


class SessionResponse(BaseModel):
    id: str
    user_id: str
    target_job_id: Optional[str]
    application_id: Optional[str]
    analysis_job_id: Optional[str]
    session_type: str
    difficulty: str
    status: str
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    items: List[SessionResponse]
    total: int


class QuestionResponse(BaseModel):
    id: str
    session_id: str
    question_type: str
    difficulty: str
    question_text: str
    related_evidence: Optional[Any] = None
    rubric: Optional[Any] = None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    questions: List[QuestionResponse]
    total_questions: int


class QuestionsGenerateRequest(BaseModel):
    question_type: Optional[QuestionType] = None
    difficulty: Optional[Difficulty] = None
    count: int = Field(default=5, ge=1, le=15)


class QuestionsGenerateResponse(BaseModel):
    session_id: str
    questions: List[QuestionResponse]
    total: int
    limitations: str


class AnswerCreateRequest(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=1, max_length=8000)


class AnswerResponse(BaseModel):
    id: str
    session_id: str
    question_id: str
    answer_text: str
    score: Any
    feedback: Any
    attempt_number: int
    created_at: datetime


class AnswerListResponse(BaseModel):
    items: List[AnswerResponse]
    total: int


class SessionSummaryResponse(BaseModel):
    session_id: str
    total_questions: int
    total_answers: int
    average_score: Optional[float]
    best_dimension: Optional[str]
    weakest_dimension: Optional[str]
    risk_flags: List[str]
    recommended_next_steps: List[str]
    limitations: str
    disclaimer: str = (
        "Practice feedback is a preparation signal based on your answers and available "
        "CV/JD/profile evidence. It does not guarantee interview or hiring outcomes."
    )
