"""Phase 6 Help Assistant / Career Coach v1 schemas.

A guided, scoped assistant over a fixed intent set — not a free-form chatbot.
All answers are derived from the authenticated user's own product data.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


HelpIntent = Literal[
    "next_best_action",
    "explain_score",
    "explain_gap",
    "suggest_learning",
    "suggest_interview_practice",
    "explain_application_status",
    "help_product_usage",
]

# Recommended product actions the assistant may surface (never free-form).
RecommendedAction = Literal[
    "open_learning",
    "start_interview",
    "view_readiness",
    "open_package",
    "update_target_job",
    "review_gap",
    "attach_analysis",
    "open_help",
]


class AssistantRequest(BaseModel):
    intent: HelpIntent
    target_job_id: Optional[str] = None
    application_id: Optional[str] = None
    analysis_job_id: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    # Optional UI language ("vi" / "en"). Defaults to English so existing
    # clients are unaffected; the Vietnamese-first frontend sends "vi".
    language: Optional[str] = None


class AssistantResponse(BaseModel):
    intent: str
    answer: str
    based_on: List[str]
    recommended_actions: List[str]
    limitations: str
    fallback_used: bool


class SuggestionItem(BaseModel):
    intent: str
    label: str
    recommended_actions: List[str]


class SuggestionsResponse(BaseModel):
    suggestions: List[SuggestionItem]
    limitations: str
