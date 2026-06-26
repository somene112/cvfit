"""Phase 6 Learning Roadmap backend routes.

All routes require an authenticated user and are scoped by ``user_id``;
cross-user access to any referenced object returns 404 (no existence leak).
Generation derives tasks from the user's own analysis result only.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import AnalysisJob, Application, LearningTask, User
from app.db.session import get_db
from app.schemas.learning import (
    LearningPriority,
    LearningStatus,
    LearningTaskListResponse,
    LearningTaskResponse,
    LearningTaskType,
    LearningTaskUpdate,
    RoadmapGenerateRequest,
    RoadmapGenerateResponse,
)
from app.services.learning import generate_learning_tasks

router = APIRouter(prefix="/v1/learning", tags=["learning"])

# Nested generation endpoint under the target-jobs namespace (contract path).
target_job_router = APIRouter(prefix="/v1/target-jobs", tags=["learning"])


def require_learning_enabled() -> None:
    if not settings.ENABLE_PHASE6_LEARNING:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")


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


def _task_to_response(task: LearningTask) -> LearningTaskResponse:
    return LearningTaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        target_job_id=str(task.target_job_id) if task.target_job_id else None,
        application_id=str(task.application_id) if task.application_id else None,
        analysis_job_id=str(task.analysis_job_id) if task.analysis_job_id else None,
        skill=task.skill,
        category=task.category,
        priority=task.priority,
        task_type=task.task_type,
        title=task.title,
        description=task.description,
        evidence_to_add=task.evidence_to_add,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _persist_tasks(
    db: Session,
    user: User,
    raw_tasks: list[dict],
    *,
    target_job_id: Optional[uuid.UUID],
    application_id: Optional[uuid.UUID],
    analysis_job_id: Optional[uuid.UUID],
) -> list[LearningTask]:
    now = datetime.utcnow()
    created: list[LearningTask] = []
    for raw in raw_tasks:
        task = LearningTask(
            id=uuid.uuid4(),
            user_id=user.id,
            target_job_id=target_job_id,
            application_id=application_id,
            analysis_job_id=analysis_job_id,
            skill=raw["skill"],
            category=raw.get("category"),
            priority=raw.get("priority", "medium"),
            task_type=raw.get("task_type", "practice"),
            title=raw["title"],
            description=raw.get("description"),
            evidence_to_add=raw.get("evidence_to_add"),
            status="todo",
            created_at=now,
            updated_at=now,
        )
        db.add(task)
        created.append(task)
    db.commit()
    for task in created:
        db.refresh(task)
    return created


def _generate_and_store(
    db: Session,
    user: User,
    *,
    target_job_id: Optional[uuid.UUID],
    application_id: Optional[uuid.UUID],
    analysis_job: Optional[AnalysisJob],
    analysis_job_id: Optional[uuid.UUID],
    max_tasks: int,
    language: Optional[str] = None,
) -> RoadmapGenerateResponse:
    raw_tasks, limitations = generate_learning_tasks(analysis_job, max_tasks=max_tasks, language=language)
    created = _persist_tasks(
        db, user, raw_tasks,
        target_job_id=target_job_id,
        application_id=application_id,
        analysis_job_id=analysis_job_id,
    )
    items = [_task_to_response(t) for t in created]
    return RoadmapGenerateResponse(tasks=items, total=len(items), limitations=limitations)


@router.post(
    "/roadmaps/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=RoadmapGenerateResponse,
    dependencies=[Depends(require_learning_enabled)],
)
def generate_roadmap(
    body: RoadmapGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> RoadmapGenerateResponse:
    target_job_id = _parse_uuid(body.target_job_id)
    application_id = _parse_uuid(body.application_id)
    analysis_job_id = _parse_uuid(body.analysis_job_id)

    analysis_job: Optional[AnalysisJob] = None
    resolved_analysis_id: Optional[uuid.UUID] = None

    # Validate ownership of every provided object and resolve an analysis context.
    if analysis_job_id is not None:
        analysis_job = _get_owned_analysis(analysis_job_id, current_user, db)
        resolved_analysis_id = analysis_job.id
    for app_ref in (target_job_id, application_id):
        if app_ref is not None:
            app = _get_owned_application(app_ref, current_user, db)
            if analysis_job is None and app.best_analysis_job_id is not None:
                analysis_job = _get_owned_analysis(app.best_analysis_job_id, current_user, db)
                resolved_analysis_id = analysis_job.id

    return _generate_and_store(
        db, current_user,
        target_job_id=target_job_id,
        application_id=application_id,
        analysis_job=analysis_job,
        analysis_job_id=resolved_analysis_id,
        max_tasks=body.max_tasks,
        language=body.language,
    )


@target_job_router.post(
    "/{job_id}/learning/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=RoadmapGenerateResponse,
    dependencies=[Depends(require_learning_enabled)],
)
def generate_for_target_job(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> RoadmapGenerateResponse:
    app = _get_owned_application(job_id, current_user, db)

    analysis_job: Optional[AnalysisJob] = None
    resolved_analysis_id: Optional[uuid.UUID] = None
    if app.best_analysis_job_id is not None:
        analysis_job = _get_owned_analysis(app.best_analysis_job_id, current_user, db)
        resolved_analysis_id = analysis_job.id

    return _generate_and_store(
        db, current_user,
        target_job_id=app.id,
        application_id=None,
        analysis_job=analysis_job,
        analysis_job_id=resolved_analysis_id,
        max_tasks=8,
    )


@router.get("/tasks", response_model=LearningTaskListResponse, dependencies=[Depends(require_learning_enabled)])
def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
    target_job_id: Optional[str] = Query(default=None),
    status_filter: Optional[LearningStatus] = Query(default=None, alias="status"),
    priority: Optional[LearningPriority] = Query(default=None),
    task_type: Optional[LearningTaskType] = Query(default=None),
) -> LearningTaskListResponse:
    query = db.query(LearningTask).filter(LearningTask.user_id == current_user.id)
    if target_job_id is not None:
        query = query.filter(LearningTask.target_job_id == _parse_uuid(target_job_id))
    if status_filter is not None:
        query = query.filter(LearningTask.status == status_filter)
    if priority is not None:
        query = query.filter(LearningTask.priority == priority)
    if task_type is not None:
        query = query.filter(LearningTask.task_type == task_type)
    tasks = query.order_by(LearningTask.created_at.desc()).all()
    items = [_task_to_response(t) for t in tasks]
    return LearningTaskListResponse(items=items, total=len(items))


@router.get("/tasks/{task_id}", response_model=LearningTaskResponse, dependencies=[Depends(require_learning_enabled)])
def get_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> LearningTaskResponse:
    task = db.get(LearningTask, task_id)
    if task is None or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="learning task not found")
    return _task_to_response(task)


@router.patch("/tasks/{task_id}", response_model=LearningTaskResponse, dependencies=[Depends(require_learning_enabled)])
def patch_task(
    task_id: uuid.UUID,
    body: LearningTaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> LearningTaskResponse:
    task = db.get(LearningTask, task_id)
    if task is None or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="learning task not found")

    if body.status is not None:
        task.status = body.status
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.evidence_to_add is not None:
        task.evidence_to_add = body.evidence_to_add
    if body.priority is not None:
        task.priority = body.priority
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return _task_to_response(task)
