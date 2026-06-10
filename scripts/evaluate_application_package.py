"""
AI CV Fit — Evaluation Script for Application Package Cases

Evaluates the application package builder (build_package_payload) for correctness,
completeness, and guardrail compliance.

Usage:
    python scripts/evaluate_application_package.py
    python scripts/evaluate_application_package.py --verbose
    python scripts/evaluate_application_package.py --case ap_01
    python scripts/evaluate_application_package.py --category application_package
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

from app.services.application_package import build_package_payload


# ---------------------------------------------------------------------------
# Guardrail check functions
# ---------------------------------------------------------------------------

GUARANTEE_PATTERNS = [
    re.compile(r"\bguarantee[sd]?\s+(you[' ]?ll\s+)?(get\s+)?(hired|selected|accepted)", re.IGNORECASE),
    re.compile(r"\bwill\s+definitely\s+(get\s+)?(hired|picked)", re.IGNORECASE),
    re.compile(r"\b100%\s+(sure|certain)\s+to\s+(get\s+)?(hired|selected)", re.IGNORECASE),
    re.compile(r"\byou\s+will\s+definitely\s+(get\s+)?(the\s+)?job", re.IGNORECASE),
    re.compile(r"guaranteed\s+(to\s+)?(get\s+)?(hired|interview|selected)", re.IGNORECASE),
]

FABRICATE_PATTERNS = [
    re.compile(r"\byou\s+(do\s+)?don[' ]?t\s+(know|have|possess|master)\s+\w+", re.IGNORECASE),
    re.compile(r"\b(no|zero)\s+(experience|knowledge)\s+in\s+\w+", re.IGNORECASE),
    re.compile(r"\byou\s+must\s+claim\s+\w+\s+experience", re.IGNORECASE),
    re.compile(r"\bdefinitely\s+(lacks|missing)\s+\w+", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_application(company_name: str | None, job_title: str, jd_text: str) -> Any:
    """Build a minimal mock application object."""
    app = type("MockApplication", (), {
        "id": "mock-app-id",
        "company_name": company_name,
        "job_title": job_title,
        "jd_text": jd_text,
    })()
    return app


def _mock_job(analysis_result: dict | None) -> Any:
    """Build a minimal mock analysis job from an analysis_result JSON."""
    job = type("MockJob", (), {
        "id": "mock-job-id",
        "result_json": analysis_result or {},
    })()
    return job


def _mock_profile_items(profile_json: dict) -> list[Any]:
    """Build a list of minimal mock profile item objects from a profile JSON."""
    items = []
    for raw_item in profile_json.get("items", []):
        item = type("MockProfileItem", (), {
            "id": raw_item.get("id", "mock-item-id"),
            "item_type": raw_item.get("item_type", "skill"),
            "title": raw_item.get("title", ""),
            "description": raw_item.get("description", ""),
            "skills_json": raw_item.get("skills_json", []),
            "evidence_text": raw_item.get("evidence_text", ""),
            "source": raw_item.get("source", "cv"),
        })()
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# Guardrail checks
# ---------------------------------------------------------------------------

def _check_guardrails(package: dict) -> dict:
    """Run guardrail checks against an application package."""
    violations: dict[str, list[str]] = {
        "guarantee": [],
        "fabrication": [],
        "disclaimer": [],
    }

    # Serialize package to text for pattern checks
    package_text = json.dumps(package, default=str).lower()

    for pattern in GUARANTEE_PATTERNS:
        if pattern.search(package_text):
            violations["guarantee"].append(
                f"  Guarantee pattern found: {pattern.pattern[:60]}"
            )

    for pattern in FABRICATE_PATTERNS:
        if pattern.search(package_text):
            violations["fabrication"].append(
                f"  Fabrication pattern found: {pattern.pattern[:60]}"
            )

    # Disclaimer must be present and meaningful
    disclaimer = package.get("disclaimer", "")
    disclaimer_lower = disclaimer.lower()
    has_disclaimer = bool(disclaimer and len(disclaimer) >= 20)
    has_must_review = "review" in disclaimer_lower or "edit" in disclaimer_lower
    has_no_guarantee = "guarantee" in disclaimer_lower or "do not" in disclaimer_lower or "does not" in disclaimer_lower
    disclaimer_ok = has_disclaimer and (has_must_review or has_no_guarantee)

    if not disclaimer_ok:
        violations["disclaimer"].append(
            f"  Disclaimer missing or incomplete: '{disclaimer[:120] if disclaimer else '(empty)'}'"
        )

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": {"guardrail": [v for sub in violations.values() for v in sub]}}


def _check_structure(package: dict) -> dict:
    """Check that all required sections are present and structurally valid."""
    required_sections = [
        "readiness_summary",
        "best_cv_analysis",
        "cover_letter_draft",
        "interview_prep_pack",
        "learning_roadmap",
        "evidence_checklist",
        "disclaimer",
    ]

    violations: dict[str, list[str]] = {
        "missing_sections": [],
        "invalid_structure": [],
    }

    for section in required_sections:
        if section not in package:
            violations["missing_sections"].append(f"  Missing section: {section}")

    readiness = package.get("readiness_summary")
    if readiness is not None:
        if not isinstance(readiness, dict):
            violations["invalid_structure"].append("  readiness_summary is not a dict")
        else:
            if "readiness_level" not in readiness:
                violations["invalid_structure"].append("  readiness_summary missing readiness_level")
            if "next_actions" not in readiness:
                violations["invalid_structure"].append("  readiness_summary missing next_actions")

    best_cv = package.get("best_cv_analysis")
    if best_cv is not None:
        if not isinstance(best_cv, dict):
            violations["invalid_structure"].append("  best_cv_analysis is not a dict")

    evidence = package.get("evidence_checklist")
    if evidence is not None:
        if not isinstance(evidence, list):
            violations["invalid_structure"].append("  evidence_checklist is not a list")
        else:
            for i, item in enumerate(evidence):
                if not isinstance(item, dict):
                    violations["invalid_structure"].append(
                        f"  evidence_checklist[{i}] is not a dict"
                    )
                elif "skill" not in item:
                    violations["invalid_structure"].append(
                        f"  evidence_checklist[{i}] missing 'skill' field"
                    )

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": {"structure": [v for sub in violations.values() for v in sub]}}


def _check_readiness_level(package: dict, expected_level: str) -> dict:
    """Check that the readiness level matches expected."""
    readiness = package.get("readiness_summary") or {}
    actual = readiness.get("readiness_level", "")

    valid_levels = {"not_started", "needs_work", "almost_ready", "ready"}
    violations = []

    if actual not in valid_levels:
        violations.append(f"  Invalid readiness_level: '{actual}'")

    if expected_level and actual != expected_level:
        violations.append(
            f"  Readiness mismatch: expected '{expected_level}' but got '{actual}'"
        )

    return {"passed": len(violations) == 0, "violations": {"readiness": violations}}


def _check_fit_score(package: dict, expected_range: tuple[float, float]) -> dict:
    """Check that the fit score is within expected range."""
    readiness = package.get("readiness_summary") or {}
    fit_score = readiness.get("fit_score")

    violations = []
    if fit_score is not None:
        try:
            score = float(fit_score)
            if not (expected_range[0] <= score <= expected_range[1]):
                violations.append(
                    f"  fit_score={score} outside expected range "
                    f"[{expected_range[0]}–{expected_range[1]}]"
                )
        except (TypeError, ValueError):
            violations.append(f"  fit_score is not numeric: {fit_score}")

    return {"passed": len(violations) == 0, "violations": {"score": violations}}


def _check_next_actions(package: dict, readiness_level: str) -> dict:
    """Check that next_actions are appropriate for the readiness level."""
    readiness = package.get("readiness_summary") or {}
    next_actions = readiness.get("next_actions", [])

    violations = []
    if not isinstance(next_actions, list):
        violations.append("  next_actions is not a list")
        return {"passed": False, "violations": {"next_action": violations}}

    if not next_actions:
        violations.append("  next_actions is empty")

    # not_started should have attach analysis action
    if readiness_level == "not_started":
        action_text = " ".join(str(a).lower() for a in next_actions)
        if "attach" not in action_text and "analysis" not in action_text:
            violations.append(
                "  not_started package should mention attaching an analysis job"
            )

    return {"passed": len(violations) == 0, "violations": {"next_action": violations}}


def _check_evidence_checklist(package: dict) -> dict:
    """Check that evidence checklist items are well-formed."""
    checklist = package.get("evidence_checklist", [])
    violations = []

    if not isinstance(checklist, list):
        violations.append("  evidence_checklist is not a list")
        return {"passed": False, "violations": {"evidence_checklist": violations}}

    for i, item in enumerate(checklist):
        if not isinstance(item, dict):
            violations.append(f"  evidence_checklist[{i}] is not a dict")
            continue

        if "skill" not in item:
            violations.append(f"  evidence_checklist[{i}] missing 'skill'")
        if "has_profile_evidence" not in item:
            violations.append(f"  evidence_checklist[{i}] missing 'has_profile_evidence'")
        if "note" not in item:
            violations.append(f"  evidence_checklist[{i}] missing 'note'")

    return {"passed": len(violations) == 0, "violations": {"evidence_checklist": violations}}


def _check_cover_letter_stub(package: dict, expect_null: bool) -> dict:
    """Check cover_letter_draft stub behavior."""
    cover_letter = package.get("cover_letter_draft")
    violations = []

    if expect_null and cover_letter is not None:
        violations.append(
            "  cover_letter_draft should be null (generated separately via /cover-letter endpoint)"
        )
    if not expect_null and cover_letter is None:
        violations.append("  cover_letter_draft should not be null")

    return {"passed": len(violations) == 0, "violations": {"cover_letter_stub": violations}}


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def _load_case(case_dir: Path) -> dict | None:
    """Load an application package case from its directory."""
    analysis_files = sorted(case_dir.glob("case_*_analysis_result.json"))
    profile_files = sorted(case_dir.glob("case_*_profile.json"))
    expected_files = sorted(case_dir.glob("case_*_expected.md"))

    if not analysis_files:
        return None

    analysis_file = analysis_files[0]
    profile_file = profile_files[0] if profile_files else None
    expected_file = expected_files[0] if expected_files else None

    with open(analysis_file, encoding="utf-8") as f:
        analysis_result = json.load(f)

    profile_json = {"items": []}
    if profile_file:
        with open(profile_file, encoding="utf-8") as f:
            profile_json = json.load(f)

    expected_text = ""
    if expected_file:
        expected_text = expected_file.read_text(encoding="utf-8")

    return {
        "analysis_result": analysis_result,
        "profile_json": profile_json,
        "expected_text": expected_text,
    }


def _parse_expected_level(text: str) -> str | None:
    """Parse expected readiness_level from expected.md."""
    patterns = [
        r"readiness_level:\s*`?(\w+)`?",
        r"Expected readiness:\s*`?(\w+)`?",
        r"readiness:\s*`?(\w+)`?",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).lower()
    return None


def _parse_expected_score_range(text: str) -> tuple[float, float]:
    """Parse expected fit_score range from expected.md."""
    patterns = [
        r"fit_score:\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)",
        r"fit_score:\s*(\d+(?:\.\d+)?)\s*\(.*?\)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            low = float(m.group(1))
            high = float(m.group(2) if m.lastindex and m.group(2) else m.group(1))
            return (low, high)
    return (0.0, 100.0)


def _parse_expectations(text: str) -> dict:
    """Parse key expectations from expected.md."""
    expectations = {
        "ready": "readiness_level" not in text or "ready" in text,
        "all_sections": "all 7 sections" in text.lower() or "all sections" in text.lower(),
        "no_fabrication": "no fabrication" in text.lower(),
        "disclaimer_present": "disclaimer" in text.lower(),
        "cover_letter_null": "cover_letter" in text.lower() and "null" in text.lower(),
        "interview_prep": "interview" in text.lower() and "questions" in text.lower(),
        "roadmap": "roadmap" in text.lower(),
        "evidence_checklist": "evidence_checklist" in text.lower(),
        "not_started": "not_started" in text.lower(),
    }
    return expectations


# ---------------------------------------------------------------------------
# Case evaluation
# ---------------------------------------------------------------------------

def _evaluate_case(case_dir: Path, case_data: dict, verbose: bool = False) -> dict:
    """Evaluate the application package for a single case."""
    expected_text = case_data["expected_text"]
    expected_level = _parse_expected_level(expected_text)
    score_range = _parse_expected_score_range(expected_text)
    expectations = _parse_expectations(expected_text)

    # Build mock objects
    analysis_result = case_data["analysis_result"]
    jd_text = analysis_result.get("jd", {}).get("text", "Sample Job") if isinstance(analysis_result, dict) else "Sample Job"
    job_title = "Software Engineer"
    if isinstance(analysis_result, dict):
        job_title = analysis_result.get("job_title", job_title)

    app = _mock_application(None, job_title, jd_text)
    job = _mock_job(analysis_result if analysis_result else None)
    profile_items = _mock_profile_items(case_data["profile_json"])

    # Build package
    package = build_package_payload(app, job, profile_items)

    # Run all checks
    guardrail_result = _check_guardrails(package)
    structure_result = _check_structure(package)
    readiness_result = _check_readiness_level(package, expected_level or "")
    score_result = _check_fit_score(package, score_range)
    next_action_result = _check_next_actions(
        package,
        expected_level or "ready",
    )
    evidence_result = _check_evidence_checklist(package)

    # Cover letter stub check
    expect_null = expectations.get("cover_letter_null", False)
    cover_letter_result = _check_cover_letter_stub(package, expect_null)

    # Compile all violations
    all_violations: dict[str, list[str]] = {}
    for check_result in [
        guardrail_result,
        structure_result,
        readiness_result,
        score_result,
        next_action_result,
        evidence_result,
        cover_letter_result,
    ]:
        for key, viols in check_result.get("violations", {}).items():
            if key not in all_violations:
                all_violations[key] = []
            all_violations[key].extend(viols)

    total_violations = sum(len(v) for v in all_violations.values())
    all_pass = (
        guardrail_result["passed"]
        and structure_result["passed"]
        and readiness_result["passed"]
        and score_result["passed"]
        and next_action_result["passed"]
        and evidence_result["passed"]
        and cover_letter_result["passed"]
    )

    readiness = package.get("readiness_summary") or {}
    readiness_level = readiness.get("readiness_level", "unknown")
    fit_score = readiness.get("fit_score")

    return {
        "case_name": case_dir.name,
        "all_pass": all_pass,
        "total_violations": total_violations,
        "readiness_level": readiness_level,
        "fit_score": fit_score,
        "expected_readiness": expected_level,
        "expected_score_range": score_range,
        "guardrail_passed": guardrail_result["passed"],
        "structure_passed": structure_result["passed"],
        "readiness_passed": readiness_result["passed"],
        "score_passed": score_result["passed"],
        "next_action_passed": next_action_result["passed"],
        "evidence_checklist_passed": evidence_result["passed"],
        "cover_letter_stub_passed": cover_letter_result["passed"],
        "violations": all_violations,
        "sections_found": list(package.keys()),
    }


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

def _find_cases(case_id: str | None = None) -> list[tuple[str, Path]]:
    """Find all application package evaluation cases."""
    eval_dir = PROJECT_ROOT / "evaluation" / "cases" / "application_package"
    if not eval_dir.exists():
        return []

    results: list[tuple[str, Path]] = []
    for case_dir in sorted(eval_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        if case_id and case_dir.name != f"case_ap_{case_id}":
            continue
        results.append(("application_package", case_dir))
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
    print("  AI CV FIT — APPLICATION PACKAGE EVALUATION")
    print("=" * 70)
    print(f"  Total cases:     {total}")
    print(f"  Passed:          {passed} ({passed/total*100:.0f}%)")
    print(f"  Failed:          {failed} ({failed/total*100:.0f}%)")
    print()

    checks = ["guardrail", "structure", "readiness", "score", "next_action", "evidence_checklist", "cover_letter_stub"]
    check_labels = [
        "Guardrail pass",
        "Structure pass",
        "Readiness pass",
        "Score pass",
        "Next-action pass",
        "Evidence checklist pass",
        "Cover-letter stub pass",
    ]
    for check, label in zip(checks, check_labels):
        count = sum(1 for r in results if r.get(f"{check}_passed", False))
        print(f"  {label}:    {count}/{total}")

    print("=" * 70)

    if verbose:
        print("\n  DETAILED RESULTS\n")
        for r in results:
            status = "PASS" if r["all_pass"] else "FAIL"
            print(f"  [{status}] {r.get('case_name', 'unknown')}")
            print(f"        Readiness: {r.get('readiness_level', '?')} "
                  f"(expected {r.get('expected_readiness', '?')})")
            print(f"        Fit score: {r.get('fit_score', '?')} "
                  f"(range {r.get('expected_score_range', ('?', '?'))})")
            print(f"        Sections: {r.get('sections_found', [])}")

            if r.get("violations"):
                for check, viols in r["violations"].items():
                    if viols:
                        print(f"        [{check.upper()}]")
                        for v in viols[:5]:
                            print(f"          {v[:120]}")
            print()

    if failed > 0:
        print("  FAILURES:\n")
        for r in results:
            if not r["all_pass"]:
                print(f"  - {r.get('case_name', 'unknown')}")
                if r.get("violations"):
                    for check, viols in r["violations"].items():
                        if viols:
                            print(f"      {check}: {viols[0][:100]}")
        print()

    print(f"  {passed}/{total} cases passed all checks")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate AI CV Fit application package cases"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--case", "-c", type=str, help="Run specific case (e.g. 'ap_01')")
    parser.add_argument("--export", "-e", type=Path, default=None)
    args = parser.parse_args()

    print("\n  AI CV Fit — Application Package Evaluation")
    print("  Loading cases...")

    cases = _find_cases(case_id=args.case)
    if not cases:
        print("  No cases found in evaluation/cases/application_package/")
        sys.exit(1)

    print(f"  Found {len(cases)} case(s). Running evaluation...\n")

    all_results: list[dict] = []
    for _, case_dir in cases:
        case_data = _load_case(case_dir)
        if case_data is None:
            print(f"  SKIP {case_dir.name}: missing analysis_result JSON")
            continue

        result = _evaluate_case(case_dir, case_data, verbose=args.verbose)
        all_results.append(result)

        status = "PASS" if result["all_pass"] else "FAIL"
        readiness = result.get("readiness_level", "?")
        score = result.get("fit_score", "?")
        print(
            f"  [{status}] {case_dir.name}: "
            f"readiness={readiness} score={score} "
            f"violations={result['total_violations']}"
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
