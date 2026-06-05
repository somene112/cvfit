"""
AI CV Fit — Evaluation Script for Scoring Cases

Runs the full scoring pipeline on all evaluation cases and reports:
- Fit score per case
- Score range validation
- Guardrail compliance checks

Usage:
    python scripts/evaluate_scoring_cases.py
    python scripts/evaluate_scoring_cases.py --verbose
    python scripts/evaluate_scoring_cases.py --case 01
    python scripts/evaluate_scoring_cases.py --category easy
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# Add backend/ so that "from app.services..." imports resolve correctly
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.services.parsing.jd_parser import parse_jd
from app.services.scoring.scorer import score
from app.services.scoring.result_v2 import build_result_v2

# ---------------------------------------------------------------------------
# Guardrail check functions
# ---------------------------------------------------------------------------

GUARANTEE_PATTERNS = [
    re.compile(r"\bwill\s+(definitely\s+)?(get\s+)?(hired|selected|accepted)", re.IGNORECASE),
    re.compile(r"\bguarantee[sd]?\s+(you[' ]?ll\s+)?(get\s+)?(hired|selected)", re.IGNORECASE),
    re.compile(r"\bwill\s+definitely\s+be\s+(hired|picked)", re.IGNORECASE),
    re.compile(r"\b100%\s+(sure|certain)\s+to\s+(get\s+)?(hired|selected)", re.IGNORECASE),
    re.compile(r"\byou\s+will\s+definitely\s+(get\s+)?(the\s+)?job", re.IGNORECASE),
    re.compile(r"guaranteed\s+(to\s+)?(get\s+)?(hired|interview|selected)", re.IGNORECASE),
]

FABRICATE_PATTERNS = [
    re.compile(r"\byou\s+don[' ]?t\s+(know|have|possess|master)\s+\w+", re.IGNORECASE),
    re.compile(r"\b(no|zero)\s+(experience|knowledge)\s+in\s+\w+", re.IGNORECASE),
    re.compile(r"\bdefinitely\s+(lacks|missing)\s+\w+", re.IGNORECASE),
]

MISSING_SKILL_BAD_PATTERNS = [
    re.compile(r"\byou\s+(do\s+)?n[' ]?t\s+know\s+\w+", re.IGNORECASE),
    re.compile(r"\byou\s+(do\s+)?n[' ]?t\s+have\s+\w+", re.IGNORECASE),
    re.compile(r"\bthe\s+candidate\s+doesn[' ]?t\s+know", re.IGNORECASE),
]


def _check_guarantee(output_text: str) -> list[str]:
    """Check for guarantee language."""
    violations = []
    for pattern in GUARANTEE_PATTERNS:
        matches = pattern.findall(output_text)
        if matches:
            violations.append(f"  Guarantee pattern: {pattern.pattern[:60]}")
    return violations


def _check_fabrication(output_text: str) -> list[str]:
    """Check for fabrication claims."""
    violations = []
    for pattern in FABRICATE_PATTERNS:
        if pattern.search(output_text):
            violations.append(f"  Fabricate pattern: {pattern.pattern[:60]}")
    return violations


def _check_missing_skill_wording(result: dict) -> list[str]:
    """Check that missing skills use correct wording (no fabrication, no absolute claims)."""
    violations = []
    missing = result.get("missing_skills", [])
    for item in missing:
        reason = str(item.get("reason", ""))
        suggestion = str(item.get("suggestion", ""))

        # Check for absolute fabrication language in reason
        for pattern in MISSING_SKILL_BAD_PATTERNS:
            if pattern.search(reason):
                violations.append(
                    f"  Fabrication in missing skill '{item.get('skill', '?')}': {reason[:80]}"
                )

        # Verify suggestion has conditional guardrail wording
        # (reason field may be truncated at ~240 chars by the scorer, check suggestion instead)
        if suggestion:
            has_conditional = (
                "if you have actually used" in suggestion.lower() or
                "only add this if it is true" in suggestion.lower()
            )
            if not has_conditional:
                violations.append(
                    f"  Missing skill '{item.get('skill', '?')}' suggestion lacks conditional guardrail: {suggestion[:80]}"
                )
    return violations


def _check_improvement_actions(result: dict) -> list[str]:
    """Check improvement actions use conditional wording."""
    violations = []
    actions = result.get("improvement_actions", [])
    for item in actions:
        suggestion = str(item.get("suggestion", ""))
        if "if you have actually used" not in suggestion.lower() and "only add this if it is true" not in suggestion.lower():
            violations.append(f"  Action '{item.get('title', '?')}' missing conditional guardrail wording")
    return violations


def _check_low_fit_cap(result: dict) -> list[str]:
    """Check that low-fit cases don't score too high."""
    violations = []
    fit_score = result.get("fit_score", 0) or 0
    matched = result.get("matched_skills", [])
    missing = result.get("missing_skills", [])

    # If there are many missing must-have skills, score should not be high
    must_have_missing = [m for m in missing if m.get("requirement_type") == "must_have"]
    if len(must_have_missing) >= 3 and fit_score >= 70:
        violations.append(
            f"  Low-fit cap violated: {len(must_have_missing)} missing must-have skills but fit_score={fit_score} (>=70)"
        )
    return violations


def check_guardrails(result: dict) -> dict:
    """Run all guardrail checks against a result dict."""
    # Build text representations for pattern checks
    output_parts = [
        result.get("overall", {}).get("summary", ""),
        result.get("overall", {}).get("guardrail_notice", ""),
    ]
    output_parts.extend([
        item.get("reason", "") for item in result.get("missing_skills", [])
    ])
    output_parts.extend([
        item.get("suggestion", "") for item in result.get("improvement_actions", [])
    ])
    output_text = " ".join(str(p) for p in output_parts)

    violations: dict[str, list[str]] = {
        "guarantee": _check_guarantee(output_text),
        "fabrication": _check_fabrication(output_text),
        "missing_skill_wording": _check_missing_skill_wording(result),
        "improvement_actions": _check_improvement_actions(result),
        "low_fit_cap": _check_low_fit_cap(result),
    }

    total_violations = sum(len(v) for v in violations.values())
    return {
        "passed": total_violations == 0,
        "total_violations": total_violations,
        "violations": violations,
    }


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def load_case(case_path: Path) -> dict | None:
    """Load a single evaluation case from its directory.
    Case files are named: case_XX_cv.txt, case_XX_jd.txt, case_XX_expected.md
    """
    # Find the case files in the directory
    cv_files = sorted(case_path.glob("case_*_cv.txt"))
    jd_files = sorted(case_path.glob("case_*_jd.txt"))
    expected_files = sorted(case_path.glob("case_*_expected.md"))

    if not cv_files or not jd_files or not expected_files:
        return None

    cv_file = cv_files[0]
    jd_file = jd_files[0]
    expected_file = expected_files[0]

    cv_text = cv_file.read_text(encoding="utf-8")
    jd_text = jd_file.read_text(encoding="utf-8")
    expected_text = expected_file.read_text(encoding="utf-8")

    # Parse expected score range from expected.md
    score_range = _parse_expected_score(expected_text)
    fit_level = _parse_expected_fit_level(expected_text)

    return {
        "cv_text": cv_text,
        "jd_text": jd_text,
        "expected_text": expected_text,
        "score_range": score_range,
        "fit_level": fit_level,
        "guardrail_expectations": _parse_guardrail_expectations(expected_text),
    }


def _parse_expected_score(text: str) -> tuple[float, float]:
    """Parse expected score range from expected.md content."""
    # Look for: Expected: 75–90, Expected: 5-25, etc.
    patterns = [
        r"Expected:\s*(\d+(?:\.\d+)?)\s*[-–to]+\s*(\d+(?:\.\d+)?)",
        r"Expected:\s*(\d+(?:\.\d+)?)\s*\(.*?\)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            low = float(m.group(1))
            high = float(m.group(2) if m.lastindex and m.group(2) else m.group(1))
            return (low, high)
    return (0.0, 100.0)


def _parse_expected_fit_level(text: str) -> str | None:
    """Parse expected fit_level from expected.md content."""
    patterns = [
        r"fit_level:\s*`?(\w+)`?",
        r"level:\s*`?(\w+)`?",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).lower()
    return None


def _parse_guardrail_expectations(text: str) -> dict:
    """Parse guardrail expectations from expected.md content."""
    expectations = {
        "no_guarantee": "No guarantee language" in text,
        "no_fabrication": "no fabrication" in text.lower(),
        "missing_skill_wording": "not found in parsed CV" in text.lower(),
        "conditional_suggestions": "only add this if it is true" in text.lower(),
    }
    return expectations


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def run_case(case: dict, verbose: bool = False) -> dict:
    """Run the full scoring pipeline on a single case."""
    cv_text = case["cv_text"]
    jd_text = case["jd_text"]

    # Parse JD
    jd_struct = parse_jd(jd_text)

    # Build a synthetic cv_parsed dict for scorer
    # We simulate parser output from the raw text
    from app.services.ontology.skill_ontology import get_skill_ontology

    ontology = get_skill_ontology()
    detected_skills = sorted(ontology.detect_skills_in_text(cv_text))
    bullets = [line.strip() for line in cv_text.splitlines()
               if len(line.strip()) >= 25]
    if not bullets:
        bullets = [l.strip() for l in cv_text.splitlines() if len(l.strip()) >= 40][:80]
    confidence = 0.85 if len(cv_text) >= 300 else max(0.2, len(cv_text) / 400 * 0.85)

    cv_parsed = {
        "text": cv_text,
        "bullets": bullets,
        "skills_detected": detected_skills,
        "confidence": confidence,
    }

    # Run scorer
    scored = score(cv_parsed, jd_struct)

    # Build result full
    result_full = {
        "job_id": "eval-job",
        "cv": {
            "file_name": "cv.txt",
            "parsed_confidence": cv_parsed["confidence"],
            "skills_detected": cv_parsed.get("skills_detected", []),
        },
        "jd": jd_struct,
        **scored
    }

    # Build v2 result
    result_v2 = build_result_v2(
        result_full,
        cv_parsed=cv_parsed,
        jd_struct=jd_struct,
        job_id="eval-job",
    )

    return result_v2


# ---------------------------------------------------------------------------
# Result evaluation
# ---------------------------------------------------------------------------

def evaluate_case(case: dict, result: dict, verbose: bool = False) -> dict:
    """Compare actual result against expected behavior."""
    fit_score = result.get("fit_score", 0) or 0
    expected_low, expected_high = case["score_range"]
    expected_fit_level = case["fit_level"]

    score_in_range = expected_low <= fit_score <= expected_high

    guardrail = check_guardrails(result)
    guardrail_passed = guardrail["passed"]

    fit_level_match = True
    if expected_fit_level:
        actual_fit_level = result.get("overall", {}).get("fit_level", "")
        fit_level_match = actual_fit_level == expected_fit_level

    score_discrepancy = None
    if not score_in_range:
        score_discrepancy = f"score={fit_score:.1f} outside expected range [{expected_low}–{expected_high}]"

    fit_level_discrepancy = None
    if not fit_level_match and expected_fit_level:
        actual = result.get("overall", {}).get("fit_level", "")
        fit_level_discrepancy = f"fit_level='{actual}' but expected '{expected_fit_level}'"

    all_pass = score_in_range and guardrail_passed and fit_level_match

    return {
        "case_name": case.get("name", "unknown"),
        "all_pass": all_pass,
        "score_in_range": score_in_range,
        "fit_level_match": fit_level_match,
        "guardrail_passed": guardrail_passed,
        "fit_score": round(fit_score, 1),
        "expected_range": (expected_low, expected_high),
        "fit_level": result.get("overall", {}).get("fit_level", ""),
        "expected_fit_level": expected_fit_level,
        "score_discrepancy": score_discrepancy,
        "fit_level_discrepancy": fit_level_discrepancy,
        "guardrail_violations": guardrail["violations"] if not guardrail_passed else {},
        "result_summary": result.get("overall", {}).get("summary", ""),
        "matched_skills_count": len(result.get("matched_skills", [])),
        "missing_skills_count": len(result.get("missing_skills", [])),
        "improvement_actions_count": len(result.get("improvement_actions", [])),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_summary(results: list[dict], verbose: bool = False):
    """Print evaluation summary to console."""
    total = len(results)
    passed = sum(1 for r in results if r["all_pass"])
    failed = total - passed

    score_pass = sum(1 for r in results if r["score_in_range"])
    guardrail_pass = sum(1 for r in results if r["guardrail_passed"])
    fit_level_pass = sum(1 for r in results if r["fit_level_match"])

    print("\n" + "=" * 70)
    print("  AI CV FIT — EVALUATION SUMMARY")
    print("=" * 70)
    print(f"  Total cases:     {total}")
    print(f"  Passed:          {passed} ({passed/total*100:.0f}%)")
    print(f"  Failed:          {failed} ({failed/total*100:.0f}%)")
    print()
    print(f"  Score in range:  {score_pass}/{total} ({score_pass/total*100:.0f}%)")
    print(f"  Fit level match: {fit_level_pass}/{total} ({fit_level_pass/total*100:.0f}%)")
    print(f"  Guardrail pass:  {guardrail_pass}/{total} ({guardrail_pass/total*100:.0f}%)")
    print("=" * 70)

    if verbose:
        print("\n  DETAILED RESULTS\n")
        for r in results:
            status = "PASS" if r["all_pass"] else "FAIL"
            print(f"  [{status}] {r.get('case_name', 'unknown')}")
            print(f"        Score: {r['fit_score']:.1f} (expected {r['expected_range'][0]}–{r['expected_range'][1]})")
            print(f"        Level: {r['fit_level']} (expected {r['expected_fit_level'] or '?'})")
            print(f"        Matched: {r['matched_skills_count']} skills, Missing: {r['missing_skills_count']}")
            if r["score_discrepancy"]:
                print(f"        DISCREPANCY: {r['score_discrepancy']}")
            if r["fit_level_discrepancy"]:
                print(f"        DISCREPANCY: {r['fit_level_discrepancy']}")
            if r["guardrail_violations"]:
                for check, violations in r["guardrail_violations"].items():
                    if violations:
                        print(f"        GUARDRAIL [{check}]:")
                        for v in violations:
                            print(f"          {v}")
            print()

    if failed > 0:
        print("  DISCREPANCIES:\n")
        for r in results:
            if not r["all_pass"]:
                print(f"  - {r.get('case_name', 'unknown')}: {r['fit_score']:.1f} "
                      f"(range: {r['expected_range'][0]}–{r['expected_range'][1]})")
                if r["score_discrepancy"]:
                    print(f"    {r['score_discrepancy']}")
                if r["fit_level_discrepancy"]:
                    print(f"    {r['fit_level_discrepancy']}")
                if r["guardrail_violations"]:
                    for check, violations in r["guardrail_violations"].items():
                        if violations:
                            print(f"    Guardrail [{check}]: {len(violations)} violation(s)")
        print()

    print(f"  Guardrail summary: {guardrail_pass}/{total} cases passed all guardrails")
    print("=" * 70)


def export_json(results: list[dict], output_path: Path):
    """Export evaluation results as JSON."""
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results exported to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_cases(category: str | None = None, case_id: str | None = None) -> list[tuple[str, Path]]:
    """Find all evaluation cases, optionally filtered."""
    eval_dir = PROJECT_ROOT / "evaluation" / "cases"
    cases: list[tuple[str, Path]] = []

    categories = [category] if category else ["easy", "medium", "hard", "edge"]
    for cat in categories:
        cat_dir = eval_dir / cat
        if not cat_dir.exists():
            continue
        for case_dir in sorted(cat_dir.iterdir()):
            if not case_dir.is_dir():
                continue
            if case_id and case_dir.name != f"case_{case_id}":
                continue
            cases.append((cat, case_dir))
    return cases


def main():
    parser = argparse.ArgumentParser(description="Evaluate AI CV Fit scoring cases")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed results")
    parser.add_argument("--case", "-c", type=str, help="Run specific case (e.g. '01', '06')")
    parser.add_argument("--category", type=str, choices=["easy", "medium", "hard", "edge"],
                        help="Run only cases in specific category")
    parser.add_argument("--export", "-e", type=Path, default=None,
                        help="Export results as JSON to specified path")
    args = parser.parse_args()

    print("\n  AI CV Fit — Scoring Evaluation")
    print("  Loading cases...")

    cases_found = find_cases(category=args.category, case_id=args.case)
    if not cases_found:
        print(f"  No cases found.")
        if args.category:
            print(f"  Category '{args.category}' not found.")
        if args.case:
            print(f"  Case '{args.case}' not found.")
        sys.exit(1)

    print(f"  Found {len(cases_found)} case(s). Running evaluation...\n")

    all_results: list[dict] = []
    for i, (cat, case_path) in enumerate(cases_found, 1):
        case_name = f"{cat}/{case_path.name}"
        print(f"  [{i}/{len(cases_found)}] Evaluating {case_name}... ", end="", flush=True)

        case = load_case(case_path)
        if case is None:
            print("SKIP (missing files)")
            continue

        try:
            result = run_case(case, verbose=args.verbose)
        except Exception as exc:
            print(f"ERROR: {exc}")
            all_results.append({
                "case_name": case_name,
                "all_pass": False,
                "error": str(exc),
            })
            continue

        case["name"] = case_name
        eval_result = evaluate_case(case, result, verbose=args.verbose)
        all_results.append(eval_result)

        status = "PASS" if eval_result["all_pass"] else "FAIL"
        print(f"{status} (score={eval_result['fit_score']:.1f})")

    print()
    print_summary(all_results, verbose=args.verbose)

    if args.export:
        export_json(all_results, args.export)

    # Exit code 0 if all pass, 1 if any fail
    all_pass = all(r.get("all_pass", False) for r in all_results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
