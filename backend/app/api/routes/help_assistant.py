"""Phase 6 Help Assistant / Career Coach v1 routes.

Guided, scoped assistant. The route validates ownership of every referenced
object (cross-user → 404), gathers owned context, and delegates to the
deterministic service. Responses never include raw CV/JD text, tokens, or secrets.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import (
    AnalysisJob,
    Application,
    InterviewSession,
    InterviewSessionAnswer,
    LearningTask,
    User,
)
from app.db.session import get_db
from app.schemas.help_assistant import (
    AssistantRequest,
    AssistantResponse,
    SuggestionItem,
    SuggestionsResponse,
)
from app.services.help import HelpContext, build_assistant_response, build_suggestions
from app.services.i18n import resolve_language
from app.services.target_jobs import compute_readiness


def require_help_enabled() -> None:
    if not settings.ENABLE_PHASE6_HELP_ASSISTANT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


router = APIRouter(
    prefix="/v1/help",
    tags=["help-assistant"],
    dependencies=[Depends(require_help_enabled)],
)


def _parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if value is None:
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


def _owned_application(app_id: Optional[uuid.UUID], user: User, db: Session) -> Optional[Application]:
    if app_id is None:
        return None
    app = db.get(Application, app_id)
    if app is None or app.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target job not found")
    return app


def _owned_analysis(job_id: Optional[uuid.UUID], user: User, db: Session) -> Optional[AnalysisJob]:
    if job_id is None:
        return None
    job = db.get(AnalysisJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")
    return job


def _owned_task(task_id: Optional[uuid.UUID], user: User, db: Session) -> Optional[LearningTask]:
    if task_id is None:
        return None
    task = db.get(LearningTask, task_id)
    if task is None or task.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="learning task not found")
    return task


def _owned_session(session_id: Optional[uuid.UUID], user: User, db: Session) -> Optional[InterviewSession]:
    if session_id is None:
        return None
    session = db.get(InterviewSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="interview session not found")
    return session


def _build_context(body: AssistantRequest, user: User, db: Session) -> HelpContext:
    target_job = _owned_application(_parse_uuid(body.target_job_id), user, db)
    application = _owned_application(_parse_uuid(body.application_id), user, db)
    analysis_job = _owned_analysis(_parse_uuid(body.analysis_job_id), user, db)
    task = _owned_task(_parse_uuid(body.task_id), user, db)
    session = _owned_session(_parse_uuid(body.session_id), user, db)

    app = target_job or application
    # Resolve readiness/analysis from the app's attached analysis when not given.
    if analysis_job is None and app is not None and app.best_analysis_job_id is not None:
        analysis_job = _owned_analysis(app.best_analysis_job_id, user, db)

    readiness = compute_readiness(app, analysis_job) if app is not None else None

    learning_tasks = (
        db.query(LearningTask).filter(LearningTask.user_id == user.id).all()
    )
    interview_sessions = (
        db.query(InterviewSession).filter(InterviewSession.user_id == user.id).all()
    )
    interview_scores: list[dict] = []
    if session is not None:
        answers = (
            db.query(InterviewSessionAnswer)
            .filter(InterviewSessionAnswer.session_id == session.id)
            .all()
        )
        interview_scores = [a.score_json for a in answers if isinstance(a.score_json, dict)]

    return HelpContext(
        application=app,
        analysis_job=analysis_job,
        readiness=readiness,
        learning_tasks=learning_tasks,
        interview_sessions=interview_sessions,
        interview_scores=interview_scores,
        task=task,
        session=session,
    )


@router.post("/assistant", response_model=AssistantResponse)
def assistant(
    body: AssistantRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AssistantResponse:
    ctx = _build_context(body, current_user, db)
    result = build_assistant_response(body.intent, ctx, language=body.language)
    return AssistantResponse(**result)


@router.get("/suggestions", response_model=SuggestionsResponse)
def suggestions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    language: Optional[str] = Query(default=None),
) -> SuggestionsResponse:
    lang = resolve_language(language)
    learning_tasks = db.query(LearningTask).filter(LearningTask.user_id == current_user.id).all()
    interview_sessions = db.query(InterviewSession).filter(InterviewSession.user_id == current_user.id).all()
    ctx = HelpContext(learning_tasks=learning_tasks, interview_sessions=interview_sessions)
    items = [SuggestionItem(**s) for s in build_suggestions(ctx, language=lang)]
    return SuggestionsResponse(
        suggestions=items,
        limitations=(
            "Các gợi ý chỉ giới hạn trong những ý định được hỗ trợ trong sản phẩm. Trợ lý không trả lời "
            "các câu hỏi về thị trường lao động bên ngoài hay đảm bảo kết quả."
            if lang == "vi"
            else "Suggestions are scoped to supported in-product intents only. The assistant does not "
            "answer external job-market questions or guarantee outcomes."
        ),
    )
