"""Vietnamese threading through the analysis pipeline (result_v2 / result_v3).

These tests pin the contract added in PR #91: when ``language="vi"`` is threaded
from the worker through ``build_result_v2`` → ``build_result_v3`` →
``build_improvement_actions`` / ``build_safe_rewrite_suggestions`` /
``build_interview_prep`` / ``build_learning_roadmap``, the app-generated prose
becomes Vietnamese. The default (no language / "en") keeps the existing English
output unchanged. User content and proper nouns (job titles, company names,
skill/tech names) are never translated.
"""

from __future__ import annotations

import re

from app.services.improvement.action_plan import build_improvement_actions
from app.services.improvement.safe_rewrite import build_safe_rewrite_suggestions
from app.services.interview.interview_prep import build_interview_prep
from app.services.roadmap.learning_roadmap import build_learning_roadmap
from app.services.scoring.result_v2 import build_result_v2
from app.services.scoring.result_v3 import build_result_v3


_VI_DIACRITIC = re.compile(r"[ăâđêôơưàảãạáằẳẵặắấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵĂÂĐÊÔƠƯÀẢÃẠÁẰẲẴẶẮẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ]")


def _is_vi(text: str) -> bool:
    return bool(_VI_DIACRITIC.search(str(text or "")))


def _v2_inputs():
    """Minimal legacy + jd inputs that produce a meaningful v2 result."""
    legacy = {
        "scores": {
            "fit_score": 78.4,
            "skill_match": 80,
            "responsibility_match": 75,
            "experience_level": 70,
            "project_relevance": 82,
            "cv_quality": 90,
        },
        "skills": {
            "matched_must_groups": [
                {"group": ["python"], "matched_by": "python"},
                {"group": ["fastapi"], "matched_by": "fastapi"},
            ],
            "matched_nice_groups": [
                {"group": ["docker", "kubernetes"], "matched_by": "docker"},
            ],
        },
        "skill_gap": {
            "missing_must_have": ["postgresql"],
            "missing_nice_to_have": ["kubernetes"],
        },
        "responsibility_match": {
            "details": [
                {
                    "jd_requirement": "Build APIs",
                    "best_cv_bullet": "Built FastAPI services",
                    "similarity": 0.8,
                }
            ]
        },
        "cv_improvements": [
            {
                "issue": "Low number of measurable achievements",
                "fix": "add metrics",
            }
        ],
        "evidence": [
            {
                "type": "skill_match",
                "skill_group": ["fastapi"],
                "matched_skill": "fastapi",
                "text": "Built FastAPI services for internal users.",
            }
        ],
    }
    jd = {
        "role": "Backend Engineer",
        "must_have_skill_groups": [["python"], ["fastapi"], ["postgresql"]],
        "nice_to_have_skill_groups": [["docker", "kubernetes"]],
        "responsibilities": ["Build APIs"],
        "skill_group_details": [
            {
                "group": ["python"],
                "type": "required",
                "source_line": "Required: Python backend development.",
            },
            {
                "group": ["postgresql"],
                "type": "required",
                "source_line": "Required: PostgreSQL database experience.",
            },
            {
                "group": ["docker", "kubernetes"],
                "type": "preferred",
                "source_line": "Nice to have: Docker or Kubernetes deployment experience.",
            },
        ],
    }
    return legacy, jd


def _v2(language=None):
    legacy, jd = _v2_inputs()
    kwargs = {}
    if language is not None:
        kwargs["language"] = language
    return build_result_v2(legacy, cv_parsed={}, jd_struct=jd, job_id="job-1", **kwargs)


def _v3(language=None):
    v2 = _v2(language=language)
    kwargs = {}
    if language is not None:
        kwargs["language"] = language
    return build_result_v3(v2, **kwargs)


# ---------------------------------------------------------------------------
# result_v2: summary / score breakdown / limitations / missing skills
# ---------------------------------------------------------------------------


class TestResultV2Language:
    def test_default_english_unchanged(self):
        result = _v2()
        # English default must be preserved for existing tests/clients.
        assert not _is_vi(result["overall"]["summary"])
        assert "fit" in result["overall"]["summary"].lower()
        # English guardrail sentence is the deterministic English notice.
        assert result["overall"]["guardrail_notice"].startswith("This analysis")
        for item in result["limitations"]:
            assert "guarantee" in item.lower() or "miss" in item.lower() or "Do not invent" in item
            assert not _is_vi(item)

    def test_vietnamese_summary_and_guardrail(self):
        result = _v2(language="vi")
        assert _is_vi(result["overall"]["summary"]), result["overall"]["summary"]
        assert "Phù hợp" in result["overall"]["summary"]
        assert "kỹ năng" in result["overall"]["summary"]
        assert "phân tích" in result["overall"]["summary"]
        assert result["overall"]["guardrail_notice"].startswith("Phân tích")
        for item in result["limitations"]:
            assert _is_vi(item), f"English leaked: {item}"

    def test_vietnamese_score_breakdown_labels_and_explanations(self):
        result = _v2(language="vi")
        breakdown = result["score_breakdown"]
        assert breakdown
        for item in breakdown:
            assert _is_vi(item["label"]), f"label not VI: {item['label']}"
            assert _is_vi(item["explanation"]), f"explanation not VI: {item['explanation']}"
        # Technical terms / key names must stay intact.
        keys = {b["key"] for b in breakdown}
        assert {"skill_match", "responsibility_match", "experience_level", "project_relevance", "cv_quality"} <= keys

    def test_english_breakdown_keys_unchanged(self):
        result = _v2()
        breakdown = result["score_breakdown"]
        # English labels and explanations keep stable keys.
        labels = {b["label"] for b in breakdown}
        assert "Skill match" in labels or "skill_match" in labels or any("match" in l.lower() for l in labels)
        for item in breakdown:
            assert not _is_vi(item["label"])
            assert not _is_vi(item["explanation"])

    def test_vietnamese_missing_skills_preserve_tech_names(self):
        result = _v2(language="vi")
        missing = result["missing_skills"]
        assert missing
        joined = " ".join(m["reason"] for m in missing)
        assert _is_vi(joined), joined
        # Technical terms (PostgreSQL / Kubernetes) must be preserved verbatim.
        for tech in ("postgresql", "kubernetes"):
            assert any(tech.lower() in m["skill"].lower() for m in missing), f"missing {tech}"
            assert any(tech.lower() in m["reason"].lower() for m in missing), f"reason did not preserve {tech}"
        # Suggestion prose is Vietnamese.
        for m in missing:
            assert _is_vi(m["suggestion"]), m["suggestion"]


# ---------------------------------------------------------------------------
# result_v3: improvement_actions / safe_rewrite / interview_prep / learning_roadmap
# ---------------------------------------------------------------------------


class TestResultV3Language:
    def test_default_english_unchanged(self):
        result = _v3()
        for action in result["improvement_actions"]:
            assert not _is_vi(action["title"]), f"title leaked VI: {action['title']}"
            assert not _is_vi(action["reason"])
            assert not _is_vi(action["safe_suggestion"])
        for s in result["safe_rewrite_suggestions"]:
            # English default may be the "Built [...]" template OR the
            # fallback rewrite template; both must remain English.
            assert not _is_vi(s["suggested_structure"])
            assert not _is_vi(s["warning"])
        for q in result["interview_prep"]:
            assert q["question"].startswith("Can you walk through") or "JD mentions" in q["question"]
            assert not _is_vi(q["question"])
        for r in result["learning_roadmap"]:
            assert r["why"].startswith("The JD mentions ")
            assert r["estimated_effort"] in ("1-2 weeks", "2-4 weeks")
            assert not _is_vi(r["why"])
        # v3 limitations are the English required ones.
        for lim in result["limitations"]:
            assert "guarantee" in lim.lower() or "Do not invent" in lim or "Missing evidence" in lim

    def test_vietnamese_improvement_actions(self):
        result = _v3(language="vi")
        for action in result["improvement_actions"]:
            assert _is_vi(action["title"]), f"title not VI: {action['title']}"
            assert _is_vi(action["reason"]), f"reason not VI: {action['reason']}"
            assert _is_vi(action["safe_suggestion"]), f"safe_suggestion not VI: {action['safe_suggestion']}"
            assert _is_vi(action["guardrail"]), f"guardrail not VI: {action['guardrail']}"
        # Technical / proper nouns preserved.
        for action in result["improvement_actions"]:
            if action.get("linked_skill"):
                # The skill name should appear verbatim in title or reason.
                assert action["linked_skill"] in action["title"] or action["linked_skill"] in action["reason"]

    def test_vietnamese_safe_rewrite(self):
        result = _v3(language="vi")
        for s in result["safe_rewrite_suggestions"]:
            assert _is_vi(s["suggested_structure"]), s["suggested_structure"]
            assert _is_vi(s["warning"]), s["warning"]
            # Bracketed Vietnamese placeholders are present.
            assert "[tính năng" in s["suggested_structure"] or "[nhiệm vụ thực tế]" in s["suggested_structure"] or "[động từ hành động]" in s["suggested_structure"]
        # English default safety string never appears in Vietnamese output.
        assert all("Only use details" not in s["warning"] for s in result["safe_rewrite_suggestions"])

    def test_vietnamese_interview_prep(self):
        result = _v3(language="vi")
        assert result["interview_prep"]
        for q in result["interview_prep"]:
            assert _is_vi(q["question"]), q["question"]
            assert _is_vi(q["why_this_question"]), q["why_this_question"]
            for line in q["suggested_answer_outline"]:
                assert _is_vi(line), line
            assert _is_vi(q["risk_if_user_cannot_answer"]), q["risk_if_user_cannot_answer"]
        # English strings must not leak.
        joined = " ".join(q["question"] for q in result["interview_prep"])
        assert "Can you walk through" not in joined
        assert "JD mentions" not in joined

    def test_vietnamese_learning_roadmap(self):
        result = _v3(language="vi")
        assert result["learning_roadmap"]
        for r in result["learning_roadmap"]:
            assert _is_vi(r["why"]), r["why"]
            assert _is_vi(r["mini_project"]), r["mini_project"]
            assert r["estimated_effort"] in ("1-2 tuần", "2-4 tuần")
            assert _is_vi(r["cv_evidence_to_add_after_learning"]), r["cv_evidence_to_add_after_learning"]
        # English roadmap strings must not appear.
        joined = " ".join(r["why"] + " " + r["mini_project"] for r in result["learning_roadmap"])
        assert "Build a small project" not in joined
        assert "1-2 weeks" not in joined
        # Technical / framework names in TOPIC_MAP are still English (e.g. "Routing", "Pydantic models")
        # but prose around them is Vietnamese.

    def test_vietnamese_v3_limitations(self):
        result = _v3(language="vi")
        for lim in result["limitations"]:
            assert _is_vi(lim), f"English leaked: {lim}"
        # The required three Vietnamese guardrails must all be present.
        joined = " ".join(result["limitations"])
        assert "Phân tích" in joined
        assert "Thiếu bằng chứng" in joined or "không tìm thấy" in joined
        assert "Không bịa đặt" in joined


# ---------------------------------------------------------------------------
# Direct builder tests — guard against accidental English drift if someone
# refactors the result_v3 wrappers.
# ---------------------------------------------------------------------------


class TestIndividualBuilders:
    def _result(self):
        return _v2()

    def test_build_improvement_actions_vi(self):
        result = self._result()
        actions = build_improvement_actions(result, language="vi")
        assert actions
        for a in actions:
            assert _is_vi(a["title"])
            assert _is_vi(a["reason"])
            assert _is_vi(a["safe_suggestion"])

    def test_build_improvement_actions_en_default(self):
        result = self._result()
        actions = build_improvement_actions(result)
        for a in actions:
            assert not _is_vi(a["title"])
            assert not _is_vi(a["reason"])

    def test_build_safe_rewrite_vi(self):
        result = self._result()
        suggestions = build_safe_rewrite_suggestions(result, language="vi")
        assert suggestions
        for s in suggestions:
            assert _is_vi(s["suggested_structure"])
            assert _is_vi(s["warning"])

    def test_build_safe_rewrite_en_default(self):
        result = self._result()
        suggestions = build_safe_rewrite_suggestions(result)
        for s in suggestions:
            assert s["suggested_structure"].startswith("Built ")
            assert not _is_vi(s["warning"])

    def test_build_interview_prep_vi(self):
        result = self._result()
        questions = build_interview_prep(result, language="vi")
        assert questions
        for q in questions:
            assert _is_vi(q["question"])
            assert _is_vi(q["why_this_question"])

    def test_build_interview_prep_en_default(self):
        result = self._result()
        questions = build_interview_prep(result)
        for q in questions:
            assert q["question"].startswith("Can you walk through") or "JD mentions" in q["question"]
            assert not _is_vi(q["question"])

    def test_build_learning_roadmap_vi(self):
        result = self._result()
        items = build_learning_roadmap(result, language="vi")
        assert items
        for r in items:
            assert _is_vi(r["why"])
            assert _is_vi(r["mini_project"])
            assert r["estimated_effort"] in ("1-2 tuần", "2-4 tuần")

    def test_build_learning_roadmap_en_default(self):
        result = self._result()
        items = build_learning_roadmap(result)
        for r in items:
            assert r["why"].startswith("The JD mentions ")
            assert r["estimated_effort"] in ("1-2 weeks", "2-4 weeks")


# ---------------------------------------------------------------------------
# Privacy / no raw CV or JD leak
# ---------------------------------------------------------------------------


class TestNoLeak:
    def test_no_cv_text_in_vi_result(self):
        cv_text = "CONFIDENTIAL-CV-MARKER-XYZ"
        jd_text = "CONFIDENTIAL-JD-MARKER-ABC"
        legacy, jd = _v2_inputs()
        result = build_result_v2(
            legacy, cv_parsed={"raw_text": cv_text}, jd_struct=jd, job_id="job-1", language="vi"
        )
        result = build_result_v3(result, language="vi")
        # Walk the full JSON to ensure the raw markers are not echoed back.
        import json
        dumped = json.dumps(result, ensure_ascii=False)
        assert cv_text not in dumped
        assert jd_text not in dumped
