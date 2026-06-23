"""Phase 6 Interview Practice v2 backend routes.

Sessions, questions, and answers. All routes require auth and are scoped by
``user_id``; ownership of questions/answers is enforced through their parent
session. Cross-user access returns 404. Answer text is stored as product data
for the owner only and is never emitted to analytics or logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime
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
    InterviewSessionQuestion,
    User,
)
from app.db.session import get_db
from app.schemas.interview_sessions import (
    AnswerCreateRequest,
    AnswerListResponse,
    AnswerResponse,
    Difficulty,
    QuestionResponse,
    QuestionsGenerateRequest,
    QuestionsGenerateResponse,
    SessionCreateRequest,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    SessionStatus,
    SessionSummaryResponse,
    SessionType,
)
from app.services.interview.sessions_v2 import (
    generate_questions,
    score_answer_v2,
    summarize_answers,
)
from app.services.billing.credit_gating import consume_credit, ensure_credit_available

def require_interview_v2_enabled() -> None:
    if not settings.ENABLE_PHASE6_INTERVIEW_V2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


router = APIRouter(
    prefix="/v1/interview/sessions",
    tags=["interview-v2"],
    dependencies=[Depends(require_interview_v2_enabled)],
)


def _parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if value is None:
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


def _get_owned_application(app_id: uuid.UUID, user: User, db: Session) -> Application:
    app = db.get(Application, app_id)
    if app is None or app.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="target job not found")
    return app


def _get_owned_analysis(job_id: uuid.UUID, user: User, db: Session) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="analysis job not found")
    return job


def _get_owned_session(session_id: uuid.UUID, user: User, db: Session) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="interview session not found")
    return session


def _session_to_response(s: InterviewSession) -> SessionResponse:
    return SessionResponse(
        id=str(s.id),
        user_id=str(s.user_id),
        target_job_id=str(s.target_job_id) if s.target_job_id else None,
        application_id=str(s.application_id) if s.application_id else None,
        analysis_job_id=str(s.analysis_job_id) if s.analysis_job_id else None,
        session_type=s.session_type,
        difficulty=s.difficulty,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _question_to_response(q: InterviewSessionQuestion) -> QuestionResponse:
    return QuestionResponse(
        id=str(q.id),
        session_id=str(q.session_id),
        question_type=q.question_type,
        difficulty=q.difficulty,
        question_text=q.question_text,
        related_evidence=q.related_evidence_json,
        rubric=q.rubric_json,
        created_at=q.created_at,
    )


def _answer_to_response(a: InterviewSessionAnswer) -> AnswerResponse:
    return AnswerResponse(
        id=str(a.id),
        session_id=str(a.session_id),
        question_id=str(a.question_id),
        answer_text=a.answer_text,
        score=a.score_json,
        feedback=a.feedback_json,
        attempt_number=a.attempt_number,
        created_at=a.created_at,
    )


def _resolve_analysis(
    db: Session,
    user: User,
    *,
    target_job_id: Optional[uuid.UUID],
    application_id: Optional[uuid.UUID],
    analysis_job_id: Optional[uuid.UUID],
) -> Optional[AnalysisJob]:
    if analysis_job_id is not None:
        return _get_owned_analysis(analysis_job_id, user, db)
    for app_ref in (target_job_id, application_id):
        if app_ref is not None:
            app = _get_owned_application(app_ref, user, db)
            if app.best_analysis_job_id is not None:
                return _get_owned_analysis(app.best_analysis_job_id, user, db)
    return None


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
def create_session(
    body: SessionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SessionResponse:
    target_job_id = _parse_uuid(body.target_job_id)
    application_id = _parse_uuid(body.application_id)
    analysis_job_id = _parse_uuid(body.analysis_job_id)

    # Validate ownership of any referenced objects (raises 404 on mismatch).
    resolved = _resolve_analysis(
        db, current_user,
        target_job_id=target_job_id,
        application_id=application_id,
        analysis_job_id=analysis_job_id,
    )

    now = datetime.utcnow()
    session = InterviewSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        target_job_id=target_job_id,
        application_id=application_id,
        analysis_job_id=analysis_job_id or (resolved.id if resolved else None),
        session_type=body.session_type,
        difficulty=body.difficulty,
        status="active",
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_to_response(session)


@router.get("", response_model=SessionListResponse)
def list_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    target_job_id: Optional[str] = Query(default=None),
    status_filter: Optional[SessionStatus] = Query(default=None, alias="status"),
    difficulty: Optional[Difficulty] = Query(default=None),
    session_type: Optional[SessionType] = Query(default=None),
) -> SessionListResponse:
    query = db.query(InterviewSession).filter(InterviewSession.user_id == current_user.id)
    if target_job_id is not None:
        query = query.filter(InterviewSession.target_job_id == _parse_uuid(target_job_id))
    if status_filter is not None:
        query = query.filter(InterviewSession.status == status_filter)
    if difficulty is not None:
        query = query.filter(InterviewSession.difficulty == difficulty)
    if session_type is not None:
        query = query.filter(InterviewSession.session_type == session_type)
    sessions = query.order_by(InterviewSession.created_at.desc()).all()
    items = [_session_to_response(s) for s in sessions]
    return SessionListResponse(items=items, total=len(items))


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    session = _get_owned_session(session_id, current_user, db)
    questions = (
        db.query(InterviewSessionQuestion)
        .filter(InterviewSessionQuestion.session_id == session.id)
        .order_by(InterviewSessionQuestion.created_at.desc())
        .all()
    )
    q_items = [_question_to_response(q) for q in questions]
    return SessionDetailResponse(
        session=_session_to_response(session),
        questions=q_items,
        total_questions=len(q_items),
    )


@router.post(
    "/{session_id}/questions/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=QuestionsGenerateResponse,
)
def generate_session_questions(
    session_id: uuid.UUID,
    body: QuestionsGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> QuestionsGenerateResponse:
    session = _get_owned_session(session_id, current_user, db)

    analysis_job: Optional[AnalysisJob] = None
    if session.analysis_job_id is not None:
        analysis_job = _get_owned_analysis(session.analysis_job_id, current_user, db)

    raw_questions, limitations = generate_questions(
        analysis_job,
        requested_type=body.question_type,
        difficulty=body.difficulty or session.difficulty,
        count=body.count,
    )

    now = datetime.utcnow()
    created: list[InterviewSessionQuestion] = []
    for raw in raw_questions:
        q = InterviewSessionQuestion(
            id=uuid.uuid4(),
            session_id=session.id,
            question_type=raw["question_type"],
            difficulty=raw["difficulty"],
            question_text=raw["question_text"],
            related_evidence_json=raw.get("related_evidence_json"),
            rubric_json=raw.get("rubric_json"),
            created_at=now,
        )
        db.add(q)
        created.append(q)
    session.updated_at = now
    db.commit()
    for q in created:
        db.refresh(q)

    items = [_question_to_response(q) for q in created]
    return QuestionsGenerateResponse(
        session_id=str(session.id),
        questions=items,
        total=len(items),
        limitations=limitations,
    )


@router.post(
    "/{session_id}/answers",
    status_code=status.HTTP_201_CREATED,
    response_model=AnswerResponse,
)
def submit_answer(
    session_id: uuid.UUID,
    body: AnswerCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> AnswerResponse:
    session = _get_owned_session(session_id, current_user, db)

    question_id = _parse_uuid(body.question_id)
    question = db.get(InterviewSessionQuestion, question_id)
    if question is None or question.session_id != session.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="question not found")

    analysis_job: Optional[AnalysisJob] = None
    if session.analysis_job_id is not None:
        candidate = db.get(AnalysisJob, session.analysis_job_id)
        if candidate is not None and candidate.user_id == current_user.id:
            analysis_job = candidate

    ensure_credit_available(db, current_user.id, "interview")

    score_json, feedback_json = score_answer_v2(question.question_text, body.answer_text, analysis_job)

    prior = (
        db.query(InterviewSessionAnswer)
        .filter(
            InterviewSessionAnswer.session_id == session.id,
            InterviewSessionAnswer.question_id == question.id,
        )
        .all()
    )
    attempt_number = len(prior) + 1

    now = datetime.utcnow()
    answer = InterviewSessionAnswer(
        id=uuid.uuid4(),
        session_id=session.id,
        question_id=question.id,
        answer_text=body.answer_text,
        score_json=score_json,
        feedback_json=feedback_json,
        attempt_number=attempt_number,
        created_at=now,
    )
    db.add(answer)
    consume_credit(
        db,
        current_user.id,
        "interview",
        related_job_id=analysis_job.id if analysis_job else None,
        related_application_id=session.application_id,
    )
    session.updated_at = now
    db.commit()
    db.refresh(answer)
    return _answer_to_response(answer)


@router.get("/{session_id}/answers", response_model=AnswerListResponse)
def list_answers(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    question_id: Optional[str] = Query(default=None),
) -> AnswerListResponse:
    session = _get_owned_session(session_id, current_user, db)
    query = db.query(InterviewSessionAnswer).filter(InterviewSessionAnswer.session_id == session.id)
    if question_id is not None:
        query = query.filter(InterviewSessionAnswer.question_id == _parse_uuid(question_id))
    answers = query.order_by(InterviewSessionAnswer.created_at.desc()).all()
    items = [_answer_to_response(a) for a in answers]
    return AnswerListResponse(items=items, total=len(items))


@router.get("/{session_id}/summary", response_model=SessionSummaryResponse)
def get_summary(
    session_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> SessionSummaryResponse:
    session = _get_owned_session(session_id, current_user, db)

    total_questions = (
        db.query(InterviewSessionQuestion)
        .filter(InterviewSessionQuestion.session_id == session.id)
        .all()
    )
    answers = (
        db.query(InterviewSessionAnswer)
        .filter(InterviewSessionAnswer.session_id == session.id)
        .all()
    )
    scores = [a.score_json for a in answers if isinstance(a.score_json, dict)]
    agg = summarize_answers(scores)

    recommended: list[str] = []
    if agg["weakest_dimension"]:
        recommended.append(f"Focus your next answers on improving '{agg['weakest_dimension']}'.")
    if not answers:
        recommended.append("Generate questions and submit answers to receive feedback.")
    else:
        recommended.append("Retry your weakest answers with a concrete STAR example.")

    limitations = (
        "Summary is based only on answers submitted in this session and the attached "
        "analysis, if any. Based on current analysis only."
    )

    return SessionSummaryResponse(
        session_id=str(session.id),
        total_questions=len(total_questions),
        total_answers=len(answers),
        average_score=agg["average_score"],
        best_dimension=agg["best_dimension"],
        weakest_dimension=agg["weakest_dimension"],
        risk_flags=agg["risk_flags"],
        recommended_next_steps=recommended,
        limitations=limitations,
    )
