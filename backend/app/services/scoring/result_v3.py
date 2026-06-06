from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.services.improvement import build_improvement_actions, build_safe_rewrite_suggestions
from app.services.interview import build_interview_prep
from app.services.roadmap import build_learning_roadmap


SCHEMA_VERSION = "3.0"
CONTRACT_VERSION = "result_json_v3"
SCORER_VERSION = "phase4.result_json_v3"
NO_HIRING_GUARANTEE = (
    "This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome."
)

SENSITIVE_KEYS = {
    "access_token",
    "access_token_hash",
    "authorization",
    "bearer",
    "jwt",
    "password",
    "password_hash",
    "raw_cv_text",
    "cv_text",
    "storage_path",
    "report_docx_path",
    "local_path",
    "file_path",
    "s3_key",
    "object_key",
    "bucket",
    "secret",
}

SENSITIVE_PATTERNS = [
    re.compile(r"access_token\s*=\s*[^&\s]+", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"[A-Za-z]:[\\/][^\s]+"),
    re.compile(r"s3://[^\s]+", re.IGNORECASE),
]


def build_result_v3(v2_result: dict) -> dict:
    result = _scrub_sensitive(deepcopy(v2_result or {}))
    _preserve_score_aliases(result)

    result["schema_version"] = SCHEMA_VERSION
    result["improvement_actions"] = build_improvement_actions(result)
    result["safe_rewrite_suggestions"] = build_safe_rewrite_suggestions(result)
    result["interview_prep"] = build_interview_prep(result)
    result["learning_roadmap"] = build_learning_roadmap(result)
    result["limitations"] = _build_limitations(result.get("limitations"))
    result["metadata"] = _build_metadata(result.get("metadata"))

    return _scrub_sensitive(result)


def _preserve_score_aliases(result: dict) -> None:
    scores = result.get("scores") if isinstance(result.get("scores"), dict) else {}
    score = _first_score(scores.get("fit_score"), result.get("fit_score"), _overall_score(result))
    if score is None:
        return
    scores["fit_score"] = score
    result["scores"] = scores
    result["fit_score"] = score
    overall = result.get("overall") if isinstance(result.get("overall"), dict) else {}
    overall["fit_score"] = score
    result["overall"] = overall


def _first_score(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _overall_score(result: dict) -> Any:
    overall = result.get("overall") if isinstance(result.get("overall"), dict) else {}
    return overall.get("fit_score")


def _build_limitations(existing: Any) -> list[str]:
    limitations = [str(item) for item in existing if item] if isinstance(existing, list) else []
    required = [
        NO_HIRING_GUARANTEE,
        "Missing evidence means support was not found in the parsed CV, not that the candidate definitely lacks the skill.",
        "Do not invent skills, experience, projects, employers, dates, certifications, or metrics based on these suggestions.",
    ]
    for item in required:
        if not any(item.lower() == existing_item.lower() for existing_item in limitations):
            limitations.append(item)
    return limitations


def _build_metadata(existing: Any) -> dict:
    metadata = deepcopy(existing) if isinstance(existing, dict) else {}
    metadata["contract_version"] = CONTRACT_VERSION
    metadata["scorer_version"] = SCORER_VERSION
    return _scrub_sensitive(metadata)


def _scrub_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _scrub_sensitive(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list):
        return [_scrub_sensitive(item) for item in value]
    if isinstance(value, str):
        return _scrub_sensitive_text(value)
    return value


def _scrub_sensitive_text(value: str) -> str:
    text = value
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text
