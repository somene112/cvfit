"""Readiness derivation for Target Jobs.

Mirrors the Phase 5 application readiness logic but returns a plain dataclass so
both the attach-analysis endpoint (to cache ``last_readiness_score``) and the
readiness endpoint can reuse it. Derives signals from the attached analysis
result only — it never invents a score and never reads raw CV/JD text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.db.models import AnalysisJob, Application


@dataclass
class ReadinessResult:
    fit_score: Optional[float]
    readiness_level: str
    summary: str
    next_actions: List[str] = field(default_factory=list)


def _extract_fit_score(result_json: dict) -> Optional[float]:
    # Explicit is-not-None checks so a score of 0.0 is not skipped.
    for candidate in (
        result_json.get("overall_fit_score"),
        (result_json.get("result") or {}).get("fit_score"),
        (result_json.get("scores") or {}).get("fit_score"),
    ):
        if candidate is not None:
            try:
                return float(candidate)
            except (TypeError, ValueError):
                return None
    return None


def compute_readiness(app: Application, job: Optional[AnalysisJob]) -> ReadinessResult:
    """Derive readiness for a target job from its attached analysis job.

    Returns a safe ``not_started`` result when no analysis is attached or the
    analysis has not completed, so callers never crash on empty data.
    """
    if app.best_analysis_job_id is None:
        return ReadinessResult(
            fit_score=None,
            readiness_level="not_started",
            summary="No analysis is attached to this target job yet.",
            next_actions=[
                "Run an analysis for this job description.",
                "Attach the analysis result using the attach-analysis endpoint.",
            ],
        )

    if job is None or job.status != "succeeded" or job.result_json is None:
        return ReadinessResult(
            fit_score=None,
            readiness_level="not_started",
            summary="The attached analysis has not completed yet.",
            next_actions=["Wait for the analysis to complete, then check readiness again."],
        )

    fit_score = _extract_fit_score(job.result_json)

    if fit_score is None:
        return ReadinessResult(
            fit_score=None,
            readiness_level="not_started",
            summary="The attached analysis did not include a fit score.",
            next_actions=["Attach a completed analysis to this target job."],
        )
    if fit_score >= 75:
        return ReadinessResult(
            fit_score=fit_score,
            readiness_level="ready",
            summary="Target job readiness is based on the attached analysis result.",
            next_actions=[
                "Review missing skills and add evidence to your career profile.",
                "Open the application package to prepare your cover letter and interview practice.",
            ],
        )
    if fit_score >= 55:
        return ReadinessResult(
            fit_score=fit_score,
            readiness_level="almost_ready",
            summary="Target job readiness is based on the attached analysis result.",
            next_actions=[
                "Address the top missing skills from the analysis.",
                "Add project evidence for matched skills to your career profile.",
            ],
        )
    return ReadinessResult(
        fit_score=fit_score,
        readiness_level="needs_work",
        summary="Target job readiness is based on the attached analysis result.",
        next_actions=[
            "Review missing skills from the latest analysis.",
            "Add project evidence to your career profile.",
            "Consider revising your CV to address high-priority JD requirements.",
        ],
    )
