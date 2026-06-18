"""Deterministic Help Assistant logic.

Each intent handler reads only the owned objects in ``HelpContext`` and returns
a structured answer. It never echoes raw CV/JD text, tokens, or secrets, never
guarantees hiring/salary/interview outcomes, and never answers external job
market facts. When the context is insufficient it returns a safe fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


SUPPORTED_INTENTS = (
    "next_best_action",
    "explain_score",
    "explain_gap",
    "suggest_learning",
    "suggest_interview_practice",
    "explain_application_status",
    "help_product_usage",
)

FALLBACK_ANSWER = "I cannot determine this from your current data."

GLOBAL_LIMITATIONS = (
    "This assistant only uses your own saved data (target jobs, analyses, learning "
    "tasks, and interview sessions). It does not predict salaries, job-market trends, "
    "or guarantee interview or hiring outcomes."
)


@dataclass
class HelpContext:
    """Owned objects gathered by the route after ownership validation."""

    application: Optional[Any] = None          # target job / application row
    analysis_job: Optional[Any] = None
    readiness: Optional[Any] = None            # ReadinessResult or None
    learning_tasks: List[Any] = field(default_factory=list)
    interview_sessions: List[Any] = field(default_factory=list)
    interview_scores: List[dict] = field(default_factory=list)
    task: Optional[Any] = None
    session: Optional[Any] = None


def _missing_skill_names(analysis_job: Any) -> list[str]:
    result = getattr(analysis_job, "result_json", None) if analysis_job else None
    if not isinstance(result, dict):
        return []
    out: list[str] = []
    raw = result.get("missing_skills")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and item.get("skill"):
                out.append(str(item["skill"]))
            elif isinstance(item, str):
                out.append(item)
    return out[:10]


def _fallback(intent: str) -> dict:
    return {
        "intent": intent,
        "answer": FALLBACK_ANSWER,
        "based_on": [],
        "recommended_actions": ["attach_analysis", "open_help"],
        "limitations": GLOBAL_LIMITATIONS,
        "fallback_used": True,
    }


def _ok(intent: str, answer: str, based_on: list[str], actions: list[str]) -> dict:
    return {
        "intent": intent,
        "answer": answer,
        "based_on": based_on,
        "recommended_actions": actions,
        "limitations": GLOBAL_LIMITATIONS,
        "fallback_used": False,
    }


def _handle_next_best_action(ctx: HelpContext) -> dict:
    app = ctx.application
    if app is None:
        return _fallback("next_best_action")
    title = getattr(app, "job_title", "this target job")
    if getattr(app, "best_analysis_job_id", None) is None:
        return _ok(
            "next_best_action",
            f"'{title}' has no analysis attached yet. Run and attach an analysis to unlock readiness and tailored prep.",
            [f"target_job:{title}", "status:no_analysis"],
            ["attach_analysis", "view_readiness"],
        )
    level = getattr(ctx.readiness, "readiness_level", None)
    if level in ("not_started", "needs_work"):
        return _ok(
            "next_best_action",
            f"For '{title}', focus on closing skill gaps next — review your gaps and start a learning task.",
            [f"target_job:{title}", f"readiness:{level}"],
            ["review_gap", "open_learning"],
        )
    if level == "almost_ready":
        return _ok(
            "next_best_action",
            f"'{title}' is almost ready. Practice interview answers to build confidence before applying.",
            [f"target_job:{title}", f"readiness:{level}"],
            ["start_interview", "view_readiness"],
        )
    if level == "ready":
        return _ok(
            "next_best_action",
            f"'{title}' looks ready. Open your application package and do a final interview practice pass.",
            [f"target_job:{title}", f"readiness:{level}"],
            ["open_package", "start_interview"],
        )
    return _fallback("next_best_action")


def _handle_explain_score(ctx: HelpContext) -> dict:
    if ctx.readiness is None or getattr(ctx.readiness, "fit_score", None) is None:
        return _fallback("explain_score")
    score = getattr(ctx.readiness, "fit_score")
    level = getattr(ctx.readiness, "readiness_level", "unknown")
    title = getattr(ctx.application, "job_title", "this target job") if ctx.application else "this analysis"
    return _ok(
        "explain_score",
        f"Your fit score for '{title}' is {score:.0f}, which maps to readiness '{level}'. "
        "It reflects how well your CV evidence matches the job requirements — it is a preparation signal, not a hiring prediction.",
        [f"fit_score:{score:.0f}", f"readiness:{level}"],
        ["view_readiness", "review_gap"],
    )


def _handle_explain_gap(ctx: HelpContext) -> dict:
    gaps = _missing_skill_names(ctx.analysis_job)
    if not gaps:
        return _fallback("explain_gap")
    return _ok(
        "explain_gap",
        "The analysis flagged these skills as missing or weakly evidenced: "
        + ", ".join(gaps)
        + ". Add real evidence or learning tasks for the highest-priority ones.",
        [f"missing_skill:{g}" for g in gaps],
        ["review_gap", "open_learning"],
    )


def _handle_suggest_learning(ctx: HelpContext) -> dict:
    if ctx.learning_tasks:
        open_tasks = [t for t in ctx.learning_tasks if getattr(t, "status", "todo") != "done"]
        if open_tasks:
            names = [getattr(t, "skill", "a skill") for t in open_tasks[:5]]
            return _ok(
                "suggest_learning",
                "You have open learning tasks. Continue with: " + ", ".join(names) + ".",
                [f"learning_task:{getattr(t, 'id', '')}" for t in open_tasks[:5]],
                ["open_learning"],
            )
        return _ok(
            "suggest_learning",
            "All your learning tasks are done. Generate a fresh roadmap from your latest analysis to keep improving.",
            ["learning_tasks:all_done"],
            ["open_learning", "review_gap"],
        )
    gaps = _missing_skill_names(ctx.analysis_job)
    if gaps:
        return _ok(
            "suggest_learning",
            "No learning tasks yet. Generate a roadmap to address: " + ", ".join(gaps[:5]) + ".",
            [f"missing_skill:{g}" for g in gaps[:5]],
            ["open_learning", "review_gap"],
        )
    return _fallback("suggest_learning")


def _handle_suggest_interview_practice(ctx: HelpContext) -> dict:
    if ctx.interview_sessions:
        active = [s for s in ctx.interview_sessions if getattr(s, "status", "active") == "active"]
        if active:
            return _ok(
                "suggest_interview_practice",
                "You have an active interview session. Continue answering questions and review your rubric feedback.",
                [f"interview_session:{getattr(active[0], 'id', '')}"],
                ["start_interview"],
            )
        return _ok(
            "suggest_interview_practice",
            "Your past sessions are complete. Start a new session to keep your interview answers sharp.",
            ["interview_sessions:completed"],
            ["start_interview"],
        )
    return _ok(
        "suggest_interview_practice",
        "You have no interview sessions yet. Start one to practice answers grounded in your CV and the job description.",
        ["interview_sessions:none"],
        ["start_interview"],
    )


def _handle_explain_application_status(ctx: HelpContext) -> dict:
    app = ctx.application
    if app is None:
        return _fallback("explain_application_status")
    title = getattr(app, "job_title", "this target job")
    status = getattr(app, "status", "unknown")
    return _ok(
        "explain_application_status",
        f"'{title}' is currently in status '{status}'. Move it forward as you complete analysis, learning, and interview prep.",
        [f"target_job:{title}", f"status:{status}"],
        ["update_target_job", "view_readiness"],
    )


def _handle_help_product_usage(ctx: HelpContext) -> dict:
    return _ok(
        "help_product_usage",
        "Workflow: create a target job, attach an analysis, review readiness and gaps, generate a learning "
        "roadmap, practice interviews, then open your application package. Use the buttons on each page to move between steps.",
        ["help:product_workflow"],
        ["open_help", "view_readiness"],
    )


_HANDLERS = {
    "next_best_action": _handle_next_best_action,
    "explain_score": _handle_explain_score,
    "explain_gap": _handle_explain_gap,
    "suggest_learning": _handle_suggest_learning,
    "suggest_interview_practice": _handle_suggest_interview_practice,
    "explain_application_status": _handle_explain_application_status,
    "help_product_usage": _handle_help_product_usage,
}


def build_assistant_response(intent: str, ctx: HelpContext) -> dict:
    handler = _HANDLERS.get(intent)
    if handler is None:
        return _fallback(intent)
    return handler(ctx)


def build_suggestions(ctx: HelpContext) -> list[dict]:
    """Context-aware list of supported intents + their product actions."""
    labels = {
        "next_best_action": "What should I do next?",
        "explain_score": "Explain my fit score",
        "explain_gap": "What are my skill gaps?",
        "suggest_learning": "Suggest learning tasks",
        "suggest_interview_practice": "Suggest interview practice",
        "explain_application_status": "Explain my application status",
        "help_product_usage": "How does this product work?",
    }
    out: list[dict] = []
    for intent in SUPPORTED_INTENTS:
        result = build_assistant_response(intent, ctx)
        out.append(
            {
                "intent": intent,
                "label": labels[intent],
                "recommended_actions": result["recommended_actions"],
            }
        )
    return out
