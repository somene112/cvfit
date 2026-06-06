from __future__ import annotations

import re
import uuid
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import jobs as jobs_route
from app.db.models import AnalysisJob
from app.db.session import get_db
from app.services.scoring.result_v2 import build_result_v2
from app.services.scoring.result_v3 import build_result_v3


SENSITIVE_KEYS = {
    "access_token",
    "access_token_hash",
    "Authorization",
    "Bearer",
    "JWT",
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

HIRING_GUARANTEE_PATTERNS = [
    r"guarantee[sd]?\s+(an\s+)?interview",
    r"guarantee[sd]?\s+(you\s+)?(will\s+)?(be\s+)?hired",
    r"will\s+definitely\s+(get\s+)?(hired|selected)",
    r"you\s+will\s+get\s+(the\s+)?job",
]


def jd_struct() -> dict:
    return {
        "role": "Backend Engineer",
        "must_have_skill_groups": [["python"], ["fastapi"], ["postgresql"]],
        "nice_to_have_skill_groups": [["docker"], ["kubernetes"]],
        "responsibilities": ["Build backend APIs", "Deploy and monitor services"],
        "skill_group_details": [
            {
                "group": ["python"],
                "type": "required",
                "source_line": "Required: Python backend development.",
            },
            {
                "group": ["fastapi"],
                "type": "required",
                "source_line": "Required: FastAPI service development.",
            },
            {
                "group": ["postgresql"],
                "type": "required",
                "source_line": "Required: PostgreSQL database experience.",
            },
            {
                "group": ["docker"],
                "type": "preferred",
                "source_line": "Nice to have: Docker deployment experience.",
            },
            {
                "group": ["kubernetes"],
                "type": "preferred",
                "source_line": "Nice to have: Kubernetes deployment experience.",
            },
        ],
    }


def legacy_result(score: float = 76.2) -> dict:
    return {
        "job_id": "job-v3",
        "scores": {
            "fit_score": score,
            "skill_match": 80,
            "responsibility_match": 72,
            "experience_level": 70,
            "project_relevance": 78,
            "cv_quality": 84,
        },
        "skills": {
            "matched_must_groups": [
                {"group": ["python"], "matched_by": "python"},
                {"group": ["fastapi"], "matched_by": "fastapi"},
            ],
            "matched_nice_groups": [
                {"group": ["docker"], "matched_by": "docker"},
            ],
        },
        "skill_gap": {
            "missing_must_have": ["postgresql"],
            "missing_nice_to_have": ["kubernetes"],
            "learn_suggestions": [],
        },
        "responsibility_match": {
            "details": [
                {
                    "jd_requirement": "Build backend APIs",
                    "best_cv_bullet": "Built FastAPI services for internal users.",
                    "similarity": 0.82,
                }
            ]
        },
        "cv_improvements": [
            {
                "issue": "Low number of measurable achievements",
                "fix": "add real metrics only if they are true",
            }
        ],
        "evidence": [
            {
                "type": "skill_match",
                "skill_group": ["fastapi"],
                "matched_skill": "fastapi",
                "text": "Built FastAPI services for internal users.",
            },
            {
                "type": "responsibility_match",
                "jd_requirement": "Build backend APIs",
                "text": "Built FastAPI services for internal users.",
                "similarity": 0.82,
            },
        ],
    }


def v3_result(score: float = 76.2) -> dict:
    v2 = build_result_v2(
        legacy_result(score=score),
        cv_parsed={"confidence": 0.86, "skills_detected": ["python", "fastapi", "docker"]},
        jd_struct=jd_struct(),
        job_id="job-v3",
    )
    return build_result_v3(v2)


def test_result_v3_preserves_v2_score_aliases_and_fields():
    result = v3_result(score=88.4)

    assert result["schema_version"] == "3.0"
    assert result["fit_score"] == 88.4
    assert result["scores"]["fit_score"] == 88.4
    assert result["overall"]["fit_score"] == 88.4

    for key in (
        "scores",
        "overall",
        "score_breakdown",
        "matched_skills",
        "missing_skills",
        "evidence",
        "skills",
        "skill_gap",
        "cv_improvements",
        "responsibility_match",
    ):
        assert key in result


def test_result_v3_has_required_phase4_sections():
    result = v3_result()

    assert result["schema_version"] == "3.0"
    assert isinstance(result["improvement_actions"], list)
    assert isinstance(result["safe_rewrite_suggestions"], list)
    assert isinstance(result["interview_prep"], list)
    assert isinstance(result["learning_roadmap"], list)
    assert isinstance(result["limitations"], list)
    assert result["metadata"]["contract_version"] == "result_json_v3"
    assert result["metadata"]["scorer_version"] == "phase4.result_json_v3"
    assert any("does not guarantee any hiring outcome" in item for item in result["limitations"])


def test_improvement_actions_use_v3_shape_and_no_fabrication_wording():
    result = v3_result()
    actions = result["improvement_actions"]

    assert actions
    for action in actions:
        for key in (
            "id",
            "priority",
            "category",
            "title",
            "status",
            "linked_skill",
            "linked_evidence",
            "reason",
            "safe_suggestion",
            "do_not_fabricate",
        ):
            assert key in action
        assert action["status"] == "open"
        assert action["do_not_fabricate"] is True
        assert action["priority"] in {"high", "medium", "low"}

    reasons = " ".join(action["reason"] for action in actions)
    suggestions = " ".join(action["safe_suggestion"] for action in actions)
    assert "was not found in the parsed CV" in reasons
    assert "If you have actually used" in suggestions
    assert "Only add this if it is true" in suggestions
    assert "you do not have" not in reasons.lower()
    assert "you don't know" not in reasons.lower()
    assert "invent" not in suggestions.lower()


def test_safe_rewrite_suggestions_are_templates_not_fake_bullets():
    result = v3_result()

    assert result["safe_rewrite_suggestions"]
    for suggestion in result["safe_rewrite_suggestions"]:
        assert suggestion["do_not_fabricate"] is True
        assert suggestion["warning"] == "Only use details that are true and can be defended in an interview."
        assert "[actual framework]" in suggestion["suggested_structure"] or "[actual task]" in suggestion["suggested_structure"]
        assert "[real metric" in suggestion["suggested_structure"] or "[real result]" in suggestion["suggested_structure"]
        assert suggestion["missing_context_to_confirm"]


def test_interview_prep_uses_outlines_not_fabricated_answers():
    result = v3_result()

    assert result["interview_prep"]
    for item in result["interview_prep"]:
        assert item["question"]
        assert item["type"] in {"project_deep_dive", "gap_probe"}
        assert item["why_this_question"]
        assert "related_jd_requirement" in item
        assert "related_cv_evidence" in item
        assert isinstance(item["suggested_answer_outline"], list)
        assert item["suggested_answer_outline"]
        assert "risk_if_user_cannot_answer" in item
        outline_text = " ".join(item["suggested_answer_outline"]).lower()
        assert "i built" not in outline_text
        assert "tell them you" not in outline_text


def test_learning_roadmap_is_future_facing():
    result = v3_result()

    assert result["learning_roadmap"]
    for item in result["learning_roadmap"]:
        assert item["do_not_claim_until_completed"] is True
        assert "was not found in the parsed CV" in item["why"]
        assert "After completing" in item["cv_evidence_to_add_after_learning"]
        assert item["topics"]
        assert item["mini_project"]
        assert item["estimated_effort"]


def test_no_hiring_guarantee_wording_in_v3_result():
    result_text = str(v3_result())

    for pattern in HIRING_GUARANTEE_PATTERNS:
        assert re.search(pattern, result_text, re.IGNORECASE) is None


def test_result_v3_scrubs_sensitive_keys_recursively():
    unsafe = build_result_v2(
        legacy_result(),
        cv_parsed={"confidence": 0.86, "skills_detected": ["python"]},
        jd_struct=jd_struct(),
        job_id="job-v3",
    )
    unsafe.update(
        {
            "access_token": "secret-token",
            "Authorization": "Bearer jwt-token",
            "password_hash": "hash",
            "raw_cv_text": "private cv",
            "nested": {
                "storage_path": "uploads/private.docx",
                "object_key": "private/key",
                "safe": "ok",
            },
        }
    )

    result = build_result_v3(unsafe)
    keys = {key.lower() for key in _all_keys(result)}
    text = str(result)

    for key in SENSITIVE_KEYS:
        assert key.lower() not in keys
    for leaked in ("secret-token", "jwt-token", "private cv", "uploads/private.docx", "private/key"):
        assert leaked not in text
    assert result["nested"] == {"safe": "ok"}


def test_result_endpoint_shape_still_works_with_v3_payload():
    result = v3_result(score=79.5)
    job_id = uuid.uuid4()
    access_token = "correct-token"
    job = SimpleNamespace(
        id=job_id,
        status="succeeded",
        progress=100,
        error_message=None,
        result_json=result,
        report_docx_path=None,
        access_token_hash=jobs_route._hash_access_token(access_token),
        user_id=None,
    )
    fake_db = SimpleNamespace(get=lambda model, key: job if model is AnalysisJob else None)

    app = FastAPI()
    app.include_router(jobs_route.router)
    app.dependency_overrides[get_db] = lambda: fake_db
    client = TestClient(app)

    response = client.get(f"/v1/jobs/{job_id}/result?access_token={access_token}")

    assert response.status_code == 200
    payload = response.json()
    nested = payload["result"]
    assert payload["overall_fit_score"] == 79.5
    assert payload["summary"]
    assert payload["recommendations"] == nested["improvement_actions"]
    assert nested["schema_version"] == "3.0"
    assert nested["fit_score"] == 79.5
    assert nested["scores"]["fit_score"] == 79.5
    assert nested["overall"]["fit_score"] == 79.5
    assert nested["safe_rewrite_suggestions"]
    assert nested["interview_prep"]
    assert nested["learning_roadmap"]


def _all_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_all_keys(item))
        return keys
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_all_keys(item))
        return keys
    return []
