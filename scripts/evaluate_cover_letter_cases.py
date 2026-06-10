"""
AI CV Fit — Evaluation Script for Cover Letter Cases

Evaluates the cover letter builder (build_cover_letter_payload) for quality,
structure completeness, and guardrail compliance.

Usage:
    python scripts/evaluate_cover_letter_cases.py
    python scripts/evaluate_cover_letter_cases.py --verbose
    python scripts/evaluate_cover_letter_cases.py --case cl_01
    python scripts/evaluate_cover_letter_cases.py --category cover_letter
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

from app.services.cover_letter import build_cover_letter_payload


# ---------------------------------------------------------------------------
# Guardrail patterns
# ---------------------------------------------------------------------------

GUARANTEE_PATTERNS = [
    re.compile(r"\bguarantee[sd]?\s+(you[' ]?ll\s+)?(get\s+)?(hired|selected|accepted)", re.IGNORECASE),
    re.compile(r"\bwill\s+definitely\s+(get\s+)?(hired|picked)", re.IGNORECASE),
    re.compile(r"\b100%\s+(sure|certain)\s+to\s+(get\s+)?(hired|selected)", re.IGNORECASE),
    re.compile(r"\byou\s+will\s+definitely\s+(get\s+)?(the\s+)?job", re.IGNORECASE),
    re.compile(r"guaranteed\s+(to\s+)?(get\s+)?(hired|interview|selected)", re.IGNORECASE),
]

FABRICATE_SKILL_PATTERNS = [
    re.compile(r"\bexperienced?\s+in\s+(fastapi|django|flask|postgresql|redis|docker|aws|kubernetes)", re.IGNORECASE),
    re.compile(r"\b(built|developed|designed)\s+(a\s+)?(fastapi|django|flask)\s+(service|api|app|system)", re.IGNORECASE),
    re.compile(r"\b(fastapi|django|flask)\s+(experience|expertise|proficient)", re.IGNORECASE),
]

FABRICATE_METRIC_PATTERNS = [
    re.compile(r"\b(reduced|decreased|improved|increased|boosted)\s+.*?(by\s+\d+%)", re.IGNORECASE),
    re.compile(r"\b\d+\s*(hours?|days?|weeks?|months?)\s+of\s+\w+\s+(experience|work)", re.IGNORECASE),
    re.compile(r"\b(million|thousand|%)?\s*(users?|customers?|clients?|requests?)\s+(handled|served|processed)", re.IGNORECASE),
]

FABRICATE_COMPANY_PATTERNS = [
    re.compile(r"\b(google|meta|amazon|microsoft|apple|netflix|uber|airbnb|spotify)\s+(team|company|work)", re.IGNORECASE),
    re.compile(r"\bat\s+(google|meta|amazon|microsoft|apple|netflix|uber|airbnb|spotify)", re.IGNORECASE),
]

FABRICATE_PROJECT_PATTERNS = [
    re.compile(r"\b(built|developed|deployed)\s+(an?\s+)?(production|scale|large)\s+(system|api|platform|service)", re.IGNORECASE),
    re.compile(r"\bmicroservices?\s+(architecture|design|with\s+(fastapi|django|flask))", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_application(company_name: str | None, job_title: str, jd_text: str) -> Any:
    """Build a minimal mock application object."""
    return type("MockApplication", (), {
        "id": "mock-app-id",
        "company_name": company_name,
        "job_title": job_title,
        "jd_text": jd_text,
    })()


def _mock_job(analysis_result: dict | None) -> Any:
    """Build a minimal mock analysis job."""
    return type("MockJob", (), {
        "id": "mock-job-id",
        "result_json": analysis_result or {},
    })()


def _mock_profile_items(profile_json: dict) -> list[Any]:
    """Build minimal mock profile item objects."""
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

def _check_guardrails(letter: dict, case_expectations: dict) -> dict:
    """Run guardrail checks against a cover letter."""
    violations: dict[str, list[str]] = {
        "guarantee": [],
        "fabricate_skill": [],
        "fabricate_metric": [],
        "fabricate_company": [],
        "fabricate_project": [],
        "disclaimer": [],
        "review_notes": [],
    }

    # Build text representation
    text_parts = [
        letter.get("opening", ""),
        letter.get("why_role_company", ""),
        letter.get("contribution_fit", ""),
        letter.get("closing", ""),
    ]
    for ev in letter.get("relevant_evidence", []):
        text_parts.append(str(ev.get("evidence_item", "")))
    text_parts.extend(str(n) for n in letter.get("review_notes", []))
    text_parts.extend(str(n) for n in letter.get("missing_evidence", []))
    text = " ".join(text_parts).lower()

    # Guarantee language
    for pattern in GUARANTEE_PATTERNS:
        if pattern.search(text):
            violations["guarantee"].append(
                f"  Guarantee language found: {pattern.pattern[:60]}"
            )

    # Fabricated skills (only check if the skill is NOT in the expected matched_skills)
    if case_expectations.get("no_fabricated_skills"):
        matched_skills = case_expectations.get("matched_skills", [])
        missing_skills = case_expectations.get("missing_skills", [])
        never_allowed = set(s.lower() for s in missing_skills)
        for pattern in FABRICATE_SKILL_PATTERNS:
            for match in pattern.finditer(text):
                fabricated_skill = match.group(1).lower() if match.lastindex else ""
                if fabricated_skill in never_allowed:
                    violations["fabricate_skill"].append(
                        f"  Fabricated skill '{fabricated_skill}' found: {pattern.pattern[:60]}"
                    )

    # Fabricated metrics
    for pattern in FABRICATE_METRIC_PATTERNS:
        if pattern.search(text):
            # Only flag if this case explicitly tests for metric fabrication
            if case_expectations.get("no_fabricated_metrics"):
                violations["fabricate_metric"].append(
                    f"  Fabricated metric found: {pattern.pattern[:60]}"
                )

    # Fabricated company names
    for pattern in FABRICATE_COMPANY_PATTERNS:
        if pattern.search(text):
            if case_expectations.get("no_fabricated_company"):
                violations["fabricate_company"].append(
                    f"  Fabricated company found: {pattern.pattern[:60]}"
                )

    # Fabricated project claims
    for pattern in FABRICATE_PROJECT_PATTERNS:
        if pattern.search(text):
            if case_expectations.get("no_fabricated_project"):
                violations["fabricate_project"].append(
                    f"  Fabricated project claim found: {pattern.pattern[:60]}"
                )

    # Disclaimer check
    disclaimer = letter.get("disclaimer", "")
    disclaimer_lower = disclaimer.lower()
    has_disclaimer = bool(disclaimer and len(disclaimer) >= 20)
    has_review = "review" in disclaimer_lower or "edit" in disclaimer_lower
    has_no_guarantee = "guarantee" in disclaimer_lower or "does not" in disclaimer_lower
    disclaimer_ok = has_disclaimer and (has_review or has_no_guarantee)
    if not disclaimer_ok:
        violations["disclaimer"].append(
            f"  Disclaimer missing or incomplete: '{disclaimer[:80] if disclaimer else '(empty)'}'"
        )

    # Review notes check
    review_notes = letter.get("review_notes", [])
    has_review_notes = isinstance(review_notes, list) and len(review_notes) > 0
    if case_expectations.get("review_notes_required") and not has_review_notes:
        violations["review_notes"].append(
            "  review_notes are required but missing or empty"
        )

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": violations}


def _check_structure(letter: dict, required_sections: list[str]) -> dict:
    """Check that all required sections are present and non-empty."""
    violations: dict[str, list[str]] = {
        "missing_sections": [],
        "empty_sections": [],
    }

    required_str_sections = ["opening", "why_role_company", "contribution_fit", "closing", "disclaimer"]
    required_list_sections = ["relevant_evidence", "review_notes", "missing_evidence"]

    for section in required_str_sections:
        if section in required_sections:
            value = letter.get(section)
            if not value:
                violations["missing_sections"].append(f"  Missing section: {section}")
            elif isinstance(value, str) and len(value.strip()) < 10:
                violations["empty_sections"].append(f"  Section '{section}' is too short: < 10 chars")

    for section in required_list_sections:
        if section in required_sections:
            value = letter.get(section)
            if value is None:
                violations["missing_sections"].append(f"  Missing section: {section}")
            elif not isinstance(value, list):
                violations["empty_sections"].append(f"  Section '{section}' is not a list")
            elif len(value) == 0 and section == "relevant_evidence":
                # Empty relevant_evidence is sometimes OK (placeholder)
                pass

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": violations}


def _check_skill_references(letter: dict, expected_present: list[str], expected_absent: list[str]) -> dict:
    """Check skill reference compliance in the cover letter.

    The cover_letter service only uses matched_skills[:3] in contribution_fit,
    so we only FAIL when a skill appears in relevant_evidence (concrete claim)
    but is NOT mentioned anywhere else in the letter (outside evidence_item).
    We warn for expected_present skills not in relevant_evidence since they may
    be excluded due to the [:3] limit.
    """
    violations: dict[str, list[str]] = {
        "missing_skill": [],
        "extra_skill": [],
    }

    # Full letter text (used for extra_skill pattern matching)
    text = (
        letter.get("opening", "") + " " +
        letter.get("why_role_company", "") + " " +
        letter.get("contribution_fit", "") + " " +
        letter.get("closing", "") + " " +
        " ".join(str(ev.get("evidence_item", "")) for ev in letter.get("relevant_evidence", []))
    ).lower()

    # Helper: extract skill names from text
    def _skills_in(text: str) -> set[str]:
        return {s.lower() for s in re.findall(
            r"(fastapi|django|flask|postgresql|redis|docker|aws|kubernetes|python|javascript|react|sql)",
            text, re.IGNORECASE)}

    # Skills in each evidence_item
    evidence_skills: list[set[str]] = [
        _skills_in(str(ev.get("evidence_item", "")))
        for ev in letter.get("relevant_evidence", [])
    ]

    # Non-evidence letter text (opening, why, fit, closing)
    non_ev_text = (
        letter.get("opening", "") + " " +
        letter.get("why_role_company", "") + " " +
        letter.get("contribution_fit", "") + " " +
        letter.get("closing", "")
    ).lower()

    # MISSING: skill in evidence but not anywhere in the full letter text
    # Note: skills in evidence[3+] may be padding from [:3] limit in cover_letter.py
    # (only top-3 matched skills appear in contribution_fit).
    # We check against the FULL text to allow padding skills to appear only in evidence.
    for i, ev_skills in enumerate(evidence_skills):
        for s in ev_skills:
            if s not in text:
                violations["missing_skill"].append(
                    f"  Skill '{s}' is in relevant_evidence[{i}] "
                    f"but not mentioned anywhere in the letter"
                )

    # EXTRA: skill from expected_absent appears in a claim context
    absent_lower = {s.lower() for s in expected_absent}
    for skill_lower in absent_lower:
        pattern = re.compile(
            rf"\b(know|have|used|built|experienced|proficient)\s+(in\s+)?{re.escape(skill_lower)}",
            re.IGNORECASE,
        )
        if pattern.search(text):
            violations["extra_skill"].append(
                f"  Skill '{skill_lower}' should not be claimed "
                f"(it is in expected_absent)"
            )

    total = sum(len(v) for v in violations.values())
    return {"passed": total == 0, "total_violations": total, "violations": violations}


def _check_tone(letter: dict, expected_tone: str) -> dict:
    """Check that the letter has the expected tone (conservative/neutral/strong)."""
    violations = []

    text_parts = [
        letter.get("opening", ""),
        letter.get("why_role_company", ""),
        letter.get("contribution_fit", ""),
    ]
    text = " ".join(text_parts).lower()

    if expected_tone == "conservative":
        # Conservative letters should use hedging language
        strong_claim_patterns = [
            re.compile(r"\b(perfectly|extremely|exceptionally|highly)\s+(qualified|suitable)", re.IGNORECASE),
            re.compile(r"\b(I\s+am\s+(certain|sure)\s+that\s+I)", re.IGNORECASE),
        ]
        for pattern in strong_claim_patterns:
            if pattern.search(text):
                violations.append(
                    f"  Conservative tone expected but found strong claim: {pattern.pattern[:60]}"
                )

    return {"passed": len(violations) == 0, "violations": {"tone": violations}}


# ---------------------------------------------------------------------------
# Case loading
# ---------------------------------------------------------------------------

def _load_case(case_dir: Path) -> dict | None:
    """Load a cover letter case from its directory."""
    cv_files = sorted(case_dir.glob("case_*_cv.txt"))
    jd_files = sorted(case_dir.glob("case_*_jd.txt"))
    profile_files = sorted(case_dir.glob("case_*_profile.json"))
    expected_files = sorted(case_dir.glob("case_*_expected.md"))

    if not cv_files:
        return None

    cv_file = cv_files[0]
    jd_file = jd_files[0] if jd_files else None
    profile_file = profile_files[0] if profile_files else None
    expected_file = expected_files[0] if expected_files else None

    cv_text = cv_file.read_text(encoding="utf-8")
    jd_text = jd_file.read_text(encoding="utf-8") if jd_file else ""

    profile_json = {"items": []}
    if profile_file:
        with open(profile_file, encoding="utf-8") as f:
            profile_json = json.load(f)

    expected_text = ""
    if expected_file:
        expected_text = expected_file.read_text(encoding="utf-8")

    return {
        "cv_text": cv_text,
        "jd_text": jd_text,
        "profile_json": profile_json,
        "expected_text": expected_text,
    }


def _parse_expectations(text: str) -> dict:
    """Parse expectations from expected.md."""
    expectations: dict = {
        "matched_skills": [],
        "missing_skills": [],
        "no_fabricated_skills": False,
        "no_fabricated_metrics": False,
        "no_fabricated_company": False,
        "no_fabricated_project": False,
        "review_notes_required": True,
        "expected_present": [],
        "expected_absent": [],
        "tone": "normal",
        "required_sections": ["opening", "why_role_company", "contribution_fit", "closing", "relevant_evidence", "disclaimer"],
    }

    if "no fabrication" in text.lower():
        expectations["no_fabricated_skills"] = True
        expectations["no_fabricated_metrics"] = True
        expectations["no_fabricated_project"] = True

    if "no fabricated" in text.lower():
        if "skill" in text.lower():
            expectations["no_fabricated_skills"] = True
        if "metric" in text.lower():
            expectations["no_fabricated_metrics"] = True
        if "company" in text.lower():
            expectations["no_fabricated_company"] = True
        if "project" in text.lower():
            expectations["no_fabricated_project"] = True

    if "conservative" in text.lower():
        expectations["tone"] = "conservative"

    if "not mentioned" in text.lower():
        # Extract skills that should not be mentioned
        skill_patterns = re.findall(r"(?:FastAPI|Django|Flask|PostgreSQL|Redis|Docker|AWS|Kubernetes|FastAPI|Python|JavaScript|React)", text)
        missing_section = False
        for line in text.split("\n"):
            if "missing skill" in line.lower() or "should not" in line.lower():
                missing_section = True
                missing_skills = re.findall(r"(?:FastAPI|Django|Flask|PostgreSQL|Redis|Docker|AWS|Kubernetes|Python|JavaScript|React)", line)
                expectations["expected_absent"].extend(missing_skills)

    if "should reference" in text.lower() or "references" in text.lower():
        # Extract skills that should be referenced (case-insensitive)
        # Only from "Must Include" section lines, not the entire file
        present_skills = set()
        in_must_include = False
        for line in text.split("\n"):
            stripped = line.strip().lower()
            if "must include" in stripped:
                in_must_include = True
            elif in_must_include and stripped.startswith("-"):
                # Extract skill names from this bullet line
                for skill in re.findall(r"(fastapi|django|flask|postgresql|redis|docker|aws|kubernetes|python|javascript|react|sql)", stripped):
                    present_skills.add(skill.title())
            elif in_must_include and stripped and not stripped.startswith("-"):
                # Exited Must Include section
                in_must_include = False
        expectations["expected_present"] = list(present_skills)

    return expectations


def _extract_analysis_result(cv_text: str, jd_text: str) -> dict:
    """Build a minimal analysis result from CV and JD text for cover letter generation.

    Uses skill ontology for both CV and JD text to extract skills, since
    parse_jd() may not extract skills from all JD text formats.
    """
    from app.services.ontology.skill_ontology import get_skill_ontology

    ontology = get_skill_ontology()

    # Extract JD skills ONLY from the REQUIRED/REQUIREMENTS section,
    # excluding NICE TO HAVE and RESPONSIBILITIES sections, to prevent
    # nice-to-have skills being treated as required.
    jd_lower = jd_text.lower()
    req_start = jd_lower.find("requirements")
    nice_start = jd_lower.find("nice to have")
    resp_start = jd_lower.find("responsibilities")

    if req_start == -1:
        req_section = jd_text
    else:
        # Start AFTER the "requirements" header line to skip the separator line
        header_end = jd_text.find("\n", req_start + 11)
        content_start = header_end + 1 if header_end != -1 else req_start + 11

        # End at the next section (nice_to_have or responsibilities)
        next_section = len(jd_text)
        if nice_start != -1 and nice_start > req_start:
            next_section = nice_start
        elif resp_start != -1 and resp_start > req_start:
            next_section = resp_start

        req_section = jd_text[content_start:next_section]

    cv_skills = sorted(ontology.detect_skills_in_text(cv_text))
    jd_skills = sorted(ontology.detect_skills_in_text(req_section))
    jd_skills_lower = [s.lower() for s in jd_skills]

    matched = [s for s in cv_skills if s.lower() in jd_skills_lower]
    missing = [s for s in jd_skills if s.lower() not in [d.lower() for d in cv_skills]]

    return {
        "overall_fit_score": round(len(matched) / max(len(jd_skills), 1) * 100, 1),
        "matched_skills": [{"skill": s} for s in matched],
        "missing_skills": [{"skill": s, "reason": f"JD requires {s} but not found in CV"} for s in missing],
    }


# ---------------------------------------------------------------------------
# Case evaluation
# ---------------------------------------------------------------------------

def _evaluate_case(case_dir: Path, case_data: dict, verbose: bool = False) -> dict:
    """Evaluate the cover letter for a single case."""
    cv_text = case_data["cv_text"]
    jd_text = case_data["jd_text"]
    profile_json = case_data["profile_json"]
    expected_text = case_data["expected_text"]
    expectations = _parse_expectations(expected_text)

    # Build mock objects
    app = _mock_application(None, "Software Engineer", jd_text)
    analysis_result = _extract_analysis_result(cv_text, jd_text)
    job = _mock_job(analysis_result)
    profile_items = _mock_profile_items(profile_json)

    # Build cover letter
    letter = build_cover_letter_payload(app, job, profile_items)

    # Extract matched skills from analysis result to populate expected_present
    # (expected.md parsing may not extract all skills from "Must Include" sections)
    analysis_result = job.result_json if hasattr(job, 'result_json') else {}
    matched_skills_list = []
    for item in analysis_result.get("matched_skills", []):
        if isinstance(item, dict):
            matched_skills_list.append(item.get("skill", ""))
        elif isinstance(item, str):
            matched_skills_list.append(item)

    # Run checks
    guardrail_result = _check_guardrails(letter, expectations)
    structure_result = _check_structure(letter, expectations.get("required_sections", []))
    # Use matched_skills from analysis result as expected_present,
    # supplemented by expected_present from expected.md parsing
    all_expected_present = list(set(expectations.get("expected_present", []) + matched_skills_list))
    skill_ref_result = _check_skill_references(
        letter,
        all_expected_present,
        expectations.get("expected_absent", []),
    )
    tone_result = _check_tone(letter, expectations.get("tone", "normal"))

    # Compile violations
    all_violations: dict[str, list[str]] = {}
    for check_result in [guardrail_result, structure_result, skill_ref_result, tone_result]:
        for key, viols in check_result.get("violations", {}).items():
            if key not in all_violations:
                all_violations[key] = []
            all_violations[key].extend(viols)

    total_violations = sum(len(v) for v in all_violations.values())
    all_pass = (
        guardrail_result["passed"]
        and structure_result["passed"]
        and skill_ref_result["passed"]
        and tone_result["passed"]
    )

    return {
        "case_name": case_dir.name,
        "all_pass": all_pass,
        "total_violations": total_violations,
        "guardrail_passed": guardrail_result["passed"],
        "structure_passed": structure_result["passed"],
        "skill_ref_passed": skill_ref_result["passed"],
        "tone_passed": tone_result["passed"],
        "violations": all_violations,
        "sections_found": list(letter.keys()),
    }


# ---------------------------------------------------------------------------
# Case discovery
# ---------------------------------------------------------------------------

def _find_cases(case_id: str | None = None) -> list[tuple[str, Path]]:
    """Find all cover letter evaluation cases."""
    eval_dir = PROJECT_ROOT / "evaluation" / "cases" / "cover_letter"
    if not eval_dir.exists():
        return []

    results: list[tuple[str, Path]] = []
    for case_dir in sorted(eval_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        if case_id and case_dir.name != f"case_cl_{case_id}":
            continue
        results.append(("cover_letter", case_dir))
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
    print("  AI CV FIT — COVER LETTER EVALUATION")
    print("=" * 70)
    print(f"  Total cases:     {total}")
    print(f"  Passed:          {passed} ({passed/total*100:.0f}%)")
    print(f"  Failed:          {failed} ({failed/total*100:.0f}%)")
    print()

    checks = ["guardrail", "structure", "skill_ref", "tone"]
    labels = ["Guardrail pass", "Structure pass", "Skill ref pass", "Tone pass"]
    for check, label in zip(checks, labels):
        count = sum(1 for r in results if r.get(f"{check}_passed", False))
        print(f"  {label}:       {count}/{total}")

    print("=" * 70)

    if verbose:
        print("\n  DETAILED RESULTS\n")
        for r in results:
            status = "PASS" if r["all_pass"] else "FAIL"
            print(f"  [{status}] {r.get('case_name', 'unknown')}")
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
    parser = argparse.ArgumentParser(description="Evaluate AI CV Fit cover letter cases")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--case", "-c", type=str, help="Run specific case (e.g. 'cl_01')")
    parser.add_argument("--export", "-e", type=Path, default=None)
    args = parser.parse_args()

    print("\n  AI CV Fit — Cover Letter Evaluation")
    print("  Loading cases...")

    cases = _find_cases(case_id=args.case)
    if not cases:
        print("  No cases found in evaluation/cases/cover_letter/")
        sys.exit(1)

    print(f"  Found {len(cases)} case(s). Running evaluation...\n")

    all_results: list[dict] = []
    for _, case_dir in cases:
        case_data = _load_case(case_dir)
        if case_data is None:
            print(f"  SKIP {case_dir.name}: missing CV file")
            continue

        result = _evaluate_case(case_dir, case_data, verbose=args.verbose)
        all_results.append(result)

        status = "PASS" if result["all_pass"] else "FAIL"
        print(
            f"  [{status}] {case_dir.name}: "
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
