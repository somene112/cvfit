"""Guardrail-safe deterministic cover letter draft builder — no LLM, no fabrication."""

from __future__ import annotations

from typing import Any, Optional


COVER_LETTER_DISCLAIMER = (
    "This is a draft cover letter generated from your CV and job description. "
    "It must be reviewed and edited before submission. "
    "It does not guarantee any hiring outcome."
)


def build_cover_letter_payload(
    application: Any,
    job: Optional[Any],
    profile_items: list,
) -> dict:
    result: dict = job.result_json if (job and job.result_json) else {}

    company_name: Optional[str] = getattr(application, "company_name", None) or None
    job_title: str = getattr(application, "job_title", "this role") or "this role"

    matched_skills = _extract_skill_list(result.get("matched_skills"))
    missing_skills = _extract_skill_list(result.get("missing_skills"))

    review_notes: list[str] = []
    if not company_name:
        review_notes.append(
            "company_name was not provided; role-focused wording used instead of a specific company name."
        )

    for skill in matched_skills[:4]:
        if not _is_backed_by_profile(skill, profile_items):
            review_notes.append(
                f"{skill}: sourced from CV analysis only — no project evidence found in career profile. "
                "Please verify before sending."
            )

    if not matched_skills:
        review_notes.append(
            "No matched skills found in the analysis result. "
            "This draft is a minimal skeleton — attach a completed analysis to generate a fuller draft."
        )

    company_suffix = f" at {company_name}" if company_name else ""
    team_ref = f"the team at {company_name}" if company_name else "your team"

    opening = (
        f"I am writing to express my strong interest in the {job_title} position{company_suffix}. "
        "Based on my CV and the role requirements, I believe my background is a strong fit for this opportunity."
    )

    why_role_company = (
        f"The {job_title} role{company_suffix} aligns well with my professional background and interests. "
        + _build_why_body(matched_skills)
    )

    relevant_evidence = _build_relevant_evidence(matched_skills, profile_items)

    contribution_fit = _build_contribution_fit(matched_skills, missing_skills)

    closing = (
        f"I would welcome the opportunity to discuss how my background can contribute to {team_ref}. "
        "Thank you for considering my application."
    )

    missing_evidence = [
        f"{skill}: required by the JD but not found in CV or career profile."
        for skill in missing_skills[:6]
    ]

    if not review_notes:
        review_notes.append(
            "Please review this draft carefully before sending. "
            "Verify all claims match your actual experience."
        )

    return {
        "opening": opening,
        "why_role_company": why_role_company,
        "relevant_evidence": relevant_evidence,
        "contribution_fit": contribution_fit,
        "closing": closing,
        "review_notes": review_notes,
        "missing_evidence": missing_evidence,
        "disclaimer": COVER_LETTER_DISCLAIMER,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_skill_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            skill = item.get("skill") or item.get("name") or item.get("title")
            if skill:
                out.append(str(skill))
    return out


def _is_backed_by_profile(skill: str, profile_items: list) -> bool:
    skill_lower = skill.lower()
    for item in profile_items:
        skills_json = getattr(item, "skills_json") or []
        if isinstance(skills_json, list) and any(skill_lower in str(s).lower() for s in skills_json):
            return True
        title = str(getattr(item, "title") or "").lower()
        desc = str(getattr(item, "description") or "").lower()
        if skill_lower in title or skill_lower in desc:
            return True
    return False


def _build_relevant_evidence(matched_skills: list[str], profile_items: list) -> list[dict]:
    evidence: list[dict] = []

    for item in profile_items[:3]:
        item_type = getattr(item, "item_type", "") or ""
        if item_type not in ("project", "experience"):
            continue
        title = getattr(item, "title", "") or ""
        description = getattr(item, "description", "") or ""
        skills_json = getattr(item, "skills_json") or []
        desc_text = f": {description}" if description else ""
        skills_text = (
            f" (skills: {', '.join(str(s) for s in skills_json[:3])})"
            if isinstance(skills_json, list) and skills_json
            else ""
        )
        evidence.append({
            "evidence_item": f"{title}{desc_text}{skills_text}",
            "source": "profile_item",
            "cv_reference": f"{item_type}: {title}",
        })

    for skill in matched_skills:
        if len(evidence) >= 4:
            break
        if not _is_backed_by_profile(skill, profile_items):
            evidence.append({
                "evidence_item": f"Based on my CV, I have experience with {skill}.",
                "source": "matched_skill",
                "cv_reference": f"matched_skill: {skill}",
            })

    if not evidence:
        evidence.append({
            "evidence_item": (
                "Please add specific project or experience evidence to your career profile "
                "to strengthen this section."
            ),
            "source": "placeholder",
            "cv_reference": "",
        })

    return evidence[:4]


def _build_why_body(matched_skills: list[str]) -> str:
    if matched_skills:
        top = ", ".join(matched_skills[:3])
        return (
            f"My background includes hands-on experience with {top}, "
            "which directly aligns with the key requirements of this position."
        )
    return (
        "My background and experience align with the technical and professional "
        "requirements described in the job description."
    )


def _build_contribution_fit(matched_skills: list[str], missing_skills: list[str]) -> str:
    parts: list[str] = []

    if matched_skills:
        top = ", ".join(matched_skills[:3])
        parts.append(
            f"My CV evidence demonstrates proficiency in {top}, "
            "which I believe addresses the core technical requirements of this role."
        )

    if missing_skills:
        gap = ", ".join(missing_skills[:2])
        parts.append(
            f"The JD highlights {gap} as key requirements. "
            "I am actively developing expertise in these areas, "
            "though I recommend reviewing this section before submitting your application."
        )

    if not parts:
        parts.append(
            "My background aligns with the role requirements. "
            "Please review this section and add specific evidence from your career profile."
        )

    return " ".join(parts)
