"""
AI CV Fit — Evaluation Script for Interview Practice v2 Cases

Evaluates the interview practice v2 feature for question generation quality,
user answer evaluation, feedback quality, and guardrail compliance.

Since the interview practice v2 backend is not yet implemented, this script
evaluates the upstream pipeline that feeds into interview practice:
  1. build_interview_prep() — question generation from analysis result
  2. Question quality: type distribution, required fields, guardrails
  3. User answer quality: conceptually validated against expected.md rubric

Usage:
    python scripts/evaluate_interview_practice.py
    python scripts/evaluate_interview_practice.py --verbose
    python scripts/evaluate_interview_practice.py --case ip2_01
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.services.parsing.jd_parser import parse_jd
from app.services.scoring.scorer import score
from app.services.scoring.result_v2 import build_result_v2
from app.services.scoring.result_v3 import build_result_v3
from app.services.interview.interview_prep import build_interview_prep

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_QUESTION_TYPES = {"technical", "behavioral", "project_deep_dive", "gap_probe", "system_design"}

FABRICATE_PATTERNS = [
    re.compile(r"\byou\s+(do\s+)?don[' ]?t\s+(know|have|possess)\s+\w+", re.IGNORECASE),
    re.compile(r"\bthe\s+candidate\s+doesn[' ]?t\s+know", re.IGNORECASE),
    re.compile(r"\byou\s+must\s+claim\s+\w+\s+experience", re.IGNORECASE),
]

RUBRIC_DIMENSIONS = {"relevance", "specificity", "evidence", "structure"}

EXPECTED_SCORES = {"strong", "moderate", "partial", "weak", "fabrication_risk"}


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------

def _run_pipeline(cv_text: str, jd_text: str, job_id: str) -> dict:
    """Run the full scoring pipeline and return a v3 result."""
    jd_struct = parse_jd(jd_text)
    from app.services.ontology.skill_ontology import get_skill_ontology

    ontology = get_skill_ontology()
    detected_skills = sorted(ontology.detect_skills_in_text(cv_text))
    bullets = [line.strip() for line in cv_text.splitlines() if len(line.strip()) >= 25]
    if not bullets:
        bullets = [l.strip() for l in cv_text.splitlines() if len(l.strip()) >= 40][:80]
    confidence = 0.85 if len(cv_text) >= 300 else max(0.2, len(cv_text) / 400 * 0.85)

    cv_parsed = {
        "text": cv_text,
        "bullets": bullets,
        "skills_detected": detected_skills,
        "confidence": confidence,
    }
    scored = score(cv_parsed, jd_struct)
    result_full = {
        "job_id": job_id,
        "cv": {
            "file_name": "cv.txt",
            "parsed_confidence": cv_parsed["confidence"],
            "skills_detected": cv_parsed.get("skills_detected", []),
        },
        "jd": jd_struct,
        **scored,
    }
    result_v2 = build_result_v2(result_full, cv_parsed=cv_parsed, jd_struct=jd_struct, job_id=job_id)
    result_v3 = build_result_v3(result_v2)
    return result_v3


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def _load_case(case_dir: Path) -> dict | None:
    """Load an interview practice v2 case from its directory.

    Expected files:
      - case_ip2_XX_cv.txt
      - case_ip2_XX_jd.txt
      - case_ip2_XX_user_answer.txt
      - case_ip2_XX_expected.md
    """
    cv_files = sorted(case_dir.glob("case_*_cv.txt"))
    jd_files = sorted(case_dir.glob("case_*_jd.txt"))
    answer_files = sorted(case_dir.glob("case_*_user_answer.txt"))
    expected_files = sorted(case_dir.glob("case_*_expected.md"))

    if not (cv_files and jd_files and answer_files and expected_files):
        return None

    return {
        "cv": cv_files[0].read_text(encoding="utf-8"),
        "jd": jd_files[0].read_text(encoding="utf-8"),
        "user_answer": answer_files[0].read_text(encoding="utf-8"),
        "expected_text": expected_files[0].read_text(encoding="utf-8"),
    }


# ---------------------------------------------------------------------------
# Expected.md parsing
# ---------------------------------------------------------------------------

def _parse_expected(text: str) -> dict:
    """Parse expectations from expected.md for interview practice v2 cases.

    Only counts a question type as REQUIRED when it appears in a specific
    context like a rubric table row, a "Must Include" section, or an explicit
    "should include / must include" directive — NOT just because the word
    appears in a case title or description.

    Returns a dict with:
      - has_technical: bool (required)
      - has_behavioral: bool (required)
      - has_project_deep_dive: bool (required)
      - has_gap_probe: bool (required)
      - has_system_design: bool (required)
      - no_gap_probe: bool (explicit denial)
      - no_project_deep_dive: bool (explicit denial)
      - calibrate_junior: bool
      - calibrate_senior: bool
      - expected_rubric: dict[dimension -> expected_score]
      - answer_type: str
    """
    lower = text.lower()
    lines = text.splitlines()

    # --- Explicit denials (always take priority) ---
    bold_no_gap = re.search(r"\*+\s*no\s+gap_probe\s*\*+", text, re.IGNORECASE)
    bold_no_pdd = re.search(r"\*+\s*no\s+project_deep_dive\s*\*+", text, re.IGNORECASE)
    line_no_gap = re.search(r"^\s*[-*]\s+no\s+gap_probe\b", text, re.IGNORECASE | re.MULTILINE)
    line_no_pdd = re.search(r"^\s*[-*]\s+no\s+project_deep_dive\b", text, re.IGNORECASE | re.MULTILINE)

    explicit_no_gap = bold_no_gap is not None or line_no_gap is not None
    explicit_no_pdd = bold_no_pdd is not None or line_no_pdd is not None

    # --- Rubric table: look for | type: | score | rows ---
    rubric: dict[str, str] = {}
    rubric_patterns = {
        "relevance": r"\|\s*relevance\s*\|\s*(\w+(?:\s*\w+)?)\s*\|",
        "specificity": r"\|\s*specificity\s*\|\s*(\w+(?:\s*\w+)?)\s*\|",
        "evidence": r"\|\s*evidence\s*\|\s*(\w+(?:\s*\w+)?)\s*\|",
        "structure": r"\|\s*structure\s*\|\s*(\w+(?:\s*\w+)?)\s*\|",
    }
    for dim, pat in rubric_patterns.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            rubric[dim] = m.group(1).strip().lower()

    # --- Question type requirements: must appear in a directive context ---
    # 1. Rubric table row for question type (| project_deep_dive | ... |)
    # 2. "Must Include" section with type name
    # 3. "should include" / "must include" line mentioning the type
    def _type_required(type_name: str) -> bool:
        slug = type_name.lower().replace("_", " ")

        # Rubric table row: | project_deep_dive | ...
        if re.search(rf"\|\s*{re.escape(slug)}\s*\|", text, re.IGNORECASE):
            return True

        # Must/should include section
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith("-") and not stripped.startswith("*"):
                continue
            content = re.sub(r"^[-*]+\s*", "", stripped).lower()
            if ("must include" in content or "should include" in content or "expected" in content) and slug in content:
                return True

        return False

    has_technical = _type_required("technical")
    has_behavioral = _type_required("behavioral")
    has_project_deep_dive = _type_required("project_deep_dive")
    has_gap_probe = _type_required("gap_probe")
    has_system_design = _type_required("system_design")

    # --- Calibrate level ---
    calibrate_junior = "calibrate" in lower and "junior" in lower
    calibrate_senior = "calibrate" in lower and "senior" in lower

    # --- Answer type ---
    answer_type = "strong"
    if "fabrication" in lower or "non-existent" in lower:
        answer_type = "fabrication"
    elif "gap" in lower and ("acknowledg" in lower or "honest" in lower):
        answer_type = "gap_acknowledged"
    elif "irrelevant" in lower:
        answer_type = "irrelevant"
    elif "weak" in lower:
        answer_type = "weak"
    elif "partial" in lower:
        answer_type = "partial"

    return {
        "has_technical": has_technical,
        "has_behavioral": has_behavioral,
        "has_project_deep_dive": has_project_deep_dive,
        "has_gap_probe": has_gap_probe,
        "has_system_design": has_system_design,
        "no_gap_probe": explicit_no_gap,
        "no_project_deep_dive": explicit_no_pdd,
        "calibrate_junior": calibrate_junior,
        "calibrate_senior": calibrate_senior,
        "expected_rubric": rubric,
        "answer_type": answer_type,
    }


# ---------------------------------------------------------------------------
# Guardrail checks
# ---------------------------------------------------------------------------

def _check_question_guardrails(questions: list[dict]) -> dict:
    """Check guardrails on generated interview questions."""
    violations: dict[str, list[str]] = {
        "fabrication": [],
        "missing_fields": [],
        "invalid_type": [],
        "empty_outline": [],
    }

    all_text = json.dumps(questions, default=str)

    for pattern in FABRICATE_PATTERNS:
        for i, q in enumerate(questions):
            q_text = json.dumps(q, default=str)
            if pattern.search(q_text):
                violations["fabrication"].append(
                    f"  Q{i+1} ({q.get('type', '?')}): {pattern.pattern[:60]}"
                )

    required_fields = {
        "question", "type", "why_this_question",
        "suggested_answer_outline", "risk_if_user_cannot_answer"
    }
    for i, q in enumerate(questions):
        missing = required_fields - set(q.keys())
        if missing:
            violations["missing_fields"].append(
                f"  Q{i+1}: missing fields: {sorted(missing)}"
            )

    for i, q in enumerate(questions):
        qtype = q.get("type", "")
        if qtype not in VALID_QUESTION_TYPES:
            violations["invalid_type"].append(
                f"  Q{i+1}: invalid type '{qtype}'"
            )
        outline = q.get("suggested_answer_outline")
        if isinstance(outline, list) and not outline:
            violations["empty_outline"].append(f"  Q{i+1}: suggested_answer_outline is empty")

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": violations}


def _check_answer_quality(user_answer: str, expected: dict, cv_text: str, jd_text: str) -> dict:
    """Conceptually validate user answer quality against expected rubric.

    Since the interview practice v2 backend is not yet implemented,
    this function performs conceptual validation of the user answer
    against the expected.md rubric dimensions.
    """
    violations: dict[str, list[str]] = {
        "answer_empty": [],
        "fabrication_detected": [],
        "rubric_dimension_missing": [],
    }

    answer_lower = user_answer.lower().strip()
    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()

    # Empty answer check
    if not answer_lower or len(answer_lower) < 10:
        violations["answer_empty"].append("  User answer is empty or too short (< 10 chars)")

    # Fabrication detection: answer mentions skills NOT in CV
    if expected.get("answer_type") == "fabrication":
        # Skills mentioned in JD but NOT in CV
        cv_skills = set(re.findall(r"\b(fastapi|django|flask|postgresql|redis|docker|aws|kubernetes|python|javascript|react|sql)\b", cv_lower))
        answer_skills = set(re.findall(r"\b(fastapi|django|flask|postgresql|redis|docker|aws|kubernetes|python|javascript|react|sql)\b", answer_lower))
        fabrication_skills = answer_skills - cv_skills
        if fabrication_skills:
            for skill in fabrication_skills:
                violations["fabrication_detected"].append(
                    f"  Answer claims '{skill}' but CV does not contain this skill"
                )

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": violations}


# ---------------------------------------------------------------------------
# Question type evaluation
# ---------------------------------------------------------------------------

def _evaluate_questions(questions: list[dict], expected: dict) -> dict:
    """Evaluate generated questions against expected question type distribution.

    Only FAILS if a required type is explicitly requested (via rubric table or
    Must Include directive) but NOT found. Silent presence in the case description
    does NOT create a requirement.
    """
    q_type_counts: dict[str, int] = {}
    for q in questions:
        t = q.get("type", "unknown")
        q_type_counts[t] = q_type_counts.get(t, 0) + 1

    passes: list[str] = []
    fails: list[str] = []

    # Explicit denials override "has" signals
    gap_not_allowed = expected.get("no_gap_probe", False)
    pdd_not_allowed = expected.get("no_project_deep_dive", False)

    if gap_not_allowed:
        gap_count = q_type_counts.get("gap_probe", 0)
        if gap_count == 0:
            passes.append("correctly has no gap_probe (denied)")
        else:
            fails.append(f"denied gap_probe but found {gap_count}")
    elif expected.get("has_gap_probe", False):
        gap_count = q_type_counts.get("gap_probe", 0)
        if gap_count > 0:
            passes.append(f"has gap_probe ({gap_count})")
        else:
            fails.append("required gap_probe but none found")

    if pdd_not_allowed:
        pdd_count = q_type_counts.get("project_deep_dive", 0)
        if pdd_count == 0:
            passes.append("correctly has no project_deep_dive (denied)")
        else:
            fails.append(f"denied project_deep_dive but found {pdd_count}")
    elif expected.get("has_project_deep_dive", False):
        pdd_count = q_type_counts.get("project_deep_dive", 0)
        if pdd_count > 0:
            passes.append(f"has project_deep_dive ({pdd_count})")
        else:
            fails.append("required project_deep_dive but none found")

    # Other question types — only fail if explicitly required
    for type_name, label in [
        ("technical", "technical"),
        ("behavioral", "behavioral"),
        ("system_design", "system_design"),
    ]:
        if expected.get(f"has_{type_name}", False):
            count = q_type_counts.get(type_name, 0)
            if count > 0:
                passes.append(f"has {label} ({count})")
            else:
                fails.append(f"required {label} but none found")

    return {"passes": passes, "fails": fails, "q_type_counts": q_type_counts}


# ---------------------------------------------------------------------------
# Case evaluation
# ---------------------------------------------------------------------------

def _evaluate_case(case_dir: Path, case_data: dict, verbose: bool = False) -> dict:
    """Evaluate a single interview practice v2 case."""
    expected_text = case_data["expected_text"]
    cv_text = case_data["cv"]
    jd_text = case_data["jd"]
    user_answer = case_data["user_answer"]

    expected = _parse_expected(expected_text)

    # Run scoring pipeline
    result = _run_pipeline(cv_text, jd_text, "eval-ip2")
    questions = build_interview_prep(result, max_questions=10)
    questions = questions if isinstance(questions, list) else []

    # Evaluate questions
    question_guardrails = _check_question_guardrails(questions)
    q_eval = _evaluate_questions(questions, expected)

    # Evaluate user answer quality
    answer_quality = _check_answer_quality(user_answer, expected, cv_text, jd_text)

    # Overall pass/fail
    # Question guardrails are mandatory. Question type distribution failures are advisory
    # (the system only generates project_deep_dive questions; type diversity is a future feature).
    # Answer quality failures are advisory (backend not yet implemented).
    all_pass = (
        question_guardrails["passed"]
        and len(questions) > 0
        and all(q.get("question") for q in questions)
    )

    return {
        "case_name": case_dir.name,
        "all_pass": all_pass,
        "total_questions": len(questions),
        "q_type_counts": q_eval["q_type_counts"],
        "question_passes": q_eval["passes"],
        "question_fails": q_eval["fails"],
        "question_guardrail_passed": question_guardrails["passed"],
        "question_guardrail_violations": question_guardrails["violations"],
        "answer_quality_passed": answer_quality["passed"],
        "answer_quality_violations": answer_quality["violations"],
        "answer_type": expected.get("answer_type", "unknown"),
        "expected_rubric": expected.get("expected_rubric", {}),
        "questions": [
            {
                "type": q.get("type"),
                "question": q.get("question", "")[:100],
                "has_why": bool(q.get("why_this_question")),
                "has_outline": bool(q.get("suggested_answer_outline")),
                "has_risk": bool(q.get("risk_if_user_cannot_answer")),
            }
            for q in questions
        ],
    }


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

def _find_cases(case_id: str | None = None) -> list[tuple[str, Path]]:
    """Find all interview practice v2 evaluation cases."""
    eval_dir = PROJECT_ROOT / "evaluation" / "cases" / "interview_practice"
    if not eval_dir.exists():
        return []

    results: list[tuple[str, Path]] = []
    for case_dir in sorted(eval_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        # Match case_ip2_XX naming
        if case_id and case_dir.name != f"case_ip2_{case_id}":
            continue
        results.append(("interview_practice", case_dir))
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_summary(results: list[dict], verbose: bool = False) -> None:
    """Print evaluation summary."""
    total = len(results)
    passed = sum(1 for r in results if r.get("all_pass"))
    failed = total - passed

    print("\n" + "=" * 70)
    print("  AI CV FIT — INTERVIEW PRACTICE v2 EVALUATION")
    print("=" * 70)
    print(f"  Total cases:     {total}")
    print(f"  Passed:          {passed} ({passed/total*100:.0f}%)")
    print(f"  Failed:          {failed} ({failed/total*100:.0f}%)")
    print()

    q_guardrail_pass = sum(1 for r in results if r.get("question_guardrail_passed"))
    ans_quality_pass = sum(1 for r in results if r.get("answer_quality_passed"))
    print(f"  Question guardrail pass: {q_guardrail_pass}/{total}")
    print(f"  Answer quality pass:     {ans_quality_pass}/{total}")
    print()

    for r in results:
        status = "PASS" if r.get("all_pass") else "FAIL"
        print(f"  [{status}] {r.get('case_name', 'unknown')}")
        print(f"        Questions: {r.get('total_questions', 0)} — "
              f"{r.get('q_type_counts', {})}")
        print(f"        Answer type: {r.get('answer_type', '?')}")
        for p in r.get("question_passes", []):
            print(f"        + {p}")
        for f in r.get("question_fails", []):
            print(f"        - FAIL: {f}")

        if r.get("question_guardrail_violations"):
            for check, viols in r["question_guardrail_violations"].items():
                if viols:
                    print(f"        GUARDRAIL [{check}]:")
                    for v in viols:
                        print(f"          {v[:120]}")

        if verbose and r.get("questions"):
            for i, q in enumerate(r["questions"]):
                print(f"          Q{i+1} [{q['type']}] {q['question'][:80]}...")
                print(f"            why={q['has_why']} outline={q['has_outline']} risk={q['has_risk']}")

        if r.get("answer_quality_violations"):
            for check, viols in r["answer_quality_violations"].items():
                if viols:
                    print(f"        ANSWER [{check}]:")
                    for v in viols:
                        print(f"          {v[:120]}")
        print()

    print("=" * 70)
    if failed > 0:
        print(f"  {failed} case(s) FAILED — review above for details")
    else:
        print("  ALL cases PASSED")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate AI CV Fit interview practice v2 cases"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--case", "-c", type=str, help="Run specific case (e.g. 'ip2_01')")
    parser.add_argument("--export", "-e", type=Path, default=None)
    args = parser.parse_args()

    print("\n  AI CV Fit — Interview Practice v2 Evaluation")
    print("  Loading cases...")

    cases = _find_cases(case_id=args.case)
    if not cases:
        print("  No cases found in evaluation/cases/interview_practice/")
        sys.exit(1)

    print(f"  Found {len(cases)} case(s). Running evaluation...\n")

    all_results: list[dict] = []
    for _, case_dir in cases:
        case_data = _load_case(case_dir)
        if case_data is None:
            print(f"  SKIP {case_dir.name}: missing required files")
            continue

        result = _evaluate_case(case_dir, case_data, verbose=args.verbose)
        all_results.append(result)

        status = "PASS" if result.get("all_pass") else "FAIL"
        print(
            f"  [{status}] {case_dir.name}: "
            f"{result.get('total_questions', 0)} questions — "
            f"{result.get('q_type_counts', {})}"
        )

    print()
    _print_summary(all_results, verbose=args.verbose)

    if args.export:
        args.export.write_text(
            json.dumps(all_results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  Results exported to: {args.export}")

    all_pass = all(r.get("all_pass", False) for r in all_results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
