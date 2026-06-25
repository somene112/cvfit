"""Guardrail-safe deterministic cover letter draft builder — no LLM, no fabrication.

Localized: when ``language="vi"`` the app-generated prose is Vietnamese. User
content (job title, company name, skill/tech names) is never translated.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Optional

from app.services.i18n import resolve_language


def normalize_text_payload(value: Any) -> Any:
    """Recursively NFC-normalize every string in a payload.

    Vietnamese diacritics can arrive decomposed (NFD: base letter + combining
    mark), which some fonts render as broken/overlapping glyphs. Normalizing to
    NFC (single composed code points) makes the text render correctly. NFC is
    idempotent, so re-normalizing already-correct text is a no-op.
    """
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_text_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_text_payload(item) for key, item in value.items()}
    return value


COVER_LETTER_DISCLAIMER = (
    "This is a draft cover letter generated from your CV and job description. "
    "It must be reviewed and edited before submission. "
    "It does not guarantee any hiring outcome."
)
COVER_LETTER_DISCLAIMER_VI = (
    "Đây là bản nháp thư xin việc được tạo từ CV và mô tả công việc của bạn. "
    "Bạn cần xem lại và chỉnh sửa trước khi gửi. "
    "Bản nháp này không đảm bảo bất kỳ kết quả tuyển dụng nào."
)


def build_cover_letter_payload(
    application: Any,
    job: Optional[Any],
    profile_items: list,
    *,
    language: str = "en",
) -> dict:
    lang = resolve_language(language)
    result: dict = job.result_json if (job and job.result_json) else {}

    company_name: Optional[str] = getattr(application, "company_name", None) or None
    default_role = "vị trí này" if lang == "vi" else "this role"
    job_title: str = getattr(application, "job_title", default_role) or default_role

    matched_skills = _extract_skill_list(result.get("matched_skills"))
    missing_skills = _extract_skill_list(result.get("missing_skills"))

    review_notes: list[str] = []
    if not company_name:
        review_notes.append(
            "Chưa cung cấp tên công ty; thư sử dụng cách diễn đạt theo vị trí thay vì tên công ty cụ thể."
            if lang == "vi"
            else "company_name was not provided; role-focused wording used instead of a specific company name."
        )

    for skill in matched_skills[:4]:
        if not _is_backed_by_profile(skill, profile_items):
            review_notes.append(
                f"{skill}: chỉ lấy từ phân tích CV — không tìm thấy bằng chứng dự án trong hồ sơ năng lực. "
                "Vui lòng kiểm tra trước khi gửi."
                if lang == "vi"
                else f"{skill}: sourced from CV analysis only — no project evidence found in career profile. "
                "Please verify before sending."
            )

    if not matched_skills:
        review_notes.append(
            "Không tìm thấy kỹ năng phù hợp trong kết quả phân tích. "
            "Bản nháp này chỉ là khung tối thiểu — hãy đính kèm một phân tích hoàn chỉnh để tạo bản nháp đầy đủ hơn."
            if lang == "vi"
            else "No matched skills found in the analysis result. "
            "This draft is a minimal skeleton — attach a completed analysis to generate a fuller draft."
        )

    if lang == "vi":
        company_suffix = f" tại {company_name}" if company_name else ""
        team_ref = f"đội ngũ tại {company_name}" if company_name else "đội ngũ của quý công ty"
        opening = (
            f"Tôi viết thư này để bày tỏ sự quan tâm sâu sắc đến vị trí {job_title}{company_suffix}. "
            "Dựa trên CV và yêu cầu của vị trí, tôi tin rằng kinh nghiệm của mình rất phù hợp với cơ hội này."
        )
        why_role_company = (
            f"Vị trí {job_title}{company_suffix} phù hợp với nền tảng chuyên môn và định hướng của tôi. "
            + _build_why_body(matched_skills, lang)
        )
        closing = (
            f"Tôi rất mong có cơ hội trao đổi về cách kinh nghiệm của mình có thể đóng góp cho {team_ref}. "
            "Cảm ơn bạn đã xem xét hồ sơ của tôi."
        )
        missing_evidence = [
            f"{skill}: được yêu cầu trong mô tả công việc nhưng không tìm thấy trong CV hoặc hồ sơ năng lực."
            for skill in missing_skills[:6]
        ]
    else:
        company_suffix = f" at {company_name}" if company_name else ""
        team_ref = f"the team at {company_name}" if company_name else "your team"
        opening = (
            f"I am writing to express my strong interest in the {job_title} position{company_suffix}. "
            "Based on my CV and the role requirements, I believe my background is a strong fit for this opportunity."
        )
        why_role_company = (
            f"The {job_title} role{company_suffix} aligns well with my professional background and interests. "
            + _build_why_body(matched_skills, lang)
        )
        closing = (
            f"I would welcome the opportunity to discuss how my background can contribute to {team_ref}. "
            "Thank you for considering my application."
        )
        missing_evidence = [
            f"{skill}: required by the JD but not found in CV or career profile."
            for skill in missing_skills[:6]
        ]

    relevant_evidence = _build_relevant_evidence(matched_skills, profile_items, lang)
    contribution_fit = _build_contribution_fit(matched_skills, missing_skills, lang)

    if not review_notes:
        review_notes.append(
            "Vui lòng xem lại kỹ bản nháp này trước khi gửi. "
            "Xác minh mọi thông tin khớp với kinh nghiệm thực tế của bạn."
            if lang == "vi"
            else "Please review this draft carefully before sending. "
            "Verify all claims match your actual experience."
        )

    return normalize_text_payload({
        "opening": opening,
        "why_role_company": why_role_company,
        "relevant_evidence": relevant_evidence,
        "contribution_fit": contribution_fit,
        "closing": closing,
        "review_notes": review_notes,
        "missing_evidence": missing_evidence,
        "disclaimer": COVER_LETTER_DISCLAIMER_VI if lang == "vi" else COVER_LETTER_DISCLAIMER,
    })


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


def _build_relevant_evidence(matched_skills: list[str], profile_items: list, lang: str) -> list[dict]:
    evidence: list[dict] = []

    for item in profile_items[:3]:
        item_type = getattr(item, "item_type", "") or ""
        if item_type not in ("project", "experience"):
            continue
        title = getattr(item, "title", "") or ""
        description = getattr(item, "description", "") or ""
        skills_json = getattr(item, "skills_json") or []
        desc_text = f": {description}" if description else ""
        if lang == "vi":
            skills_text = (
                f" (kỹ năng: {', '.join(str(s) for s in skills_json[:3])})"
                if isinstance(skills_json, list) and skills_json
                else ""
            )
        else:
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
                "evidence_item": (
                    f"Theo CV của tôi, tôi có kinh nghiệm với {skill}."
                    if lang == "vi"
                    else f"Based on my CV, I have experience with {skill}."
                ),
                "source": "matched_skill",
                "cv_reference": f"matched_skill: {skill}",
            })

    if not evidence:
        evidence.append({
            "evidence_item": (
                "Vui lòng thêm bằng chứng về dự án hoặc kinh nghiệm cụ thể vào hồ sơ năng lực "
                "để tăng sức thuyết phục cho phần này."
                if lang == "vi"
                else "Please add specific project or experience evidence to your career profile "
                "to strengthen this section."
            ),
            "source": "placeholder",
            "cv_reference": "",
        })

    return evidence[:4]


def _build_why_body(matched_skills: list[str], lang: str) -> str:
    if matched_skills:
        top = ", ".join(matched_skills[:3])
        if lang == "vi":
            return (
                f"Kinh nghiệm của tôi bao gồm việc trực tiếp làm việc với {top}, "
                "phù hợp với các yêu cầu chính của vị trí này."
            )
        return (
            f"My background includes hands-on experience with {top}, "
            "which directly aligns with the key requirements of this position."
        )
    if lang == "vi":
        return (
            "Nền tảng và kinh nghiệm của tôi phù hợp với các yêu cầu chuyên môn "
            "được mô tả trong mô tả công việc."
        )
    return (
        "My background and experience align with the technical and professional "
        "requirements described in the job description."
    )


def _build_contribution_fit(matched_skills: list[str], missing_skills: list[str], lang: str) -> str:
    parts: list[str] = []

    if matched_skills:
        top = ", ".join(matched_skills[:3])
        if lang == "vi":
            parts.append(
                f"Bằng chứng trong CV cho thấy năng lực của tôi với {top}, "
                "đáp ứng các yêu cầu kỹ thuật cốt lõi của vị trí này."
            )
        else:
            parts.append(
                f"My CV evidence demonstrates proficiency in {top}, "
                "which I believe addresses the core technical requirements of this role."
            )

    if missing_skills:
        gap = ", ".join(missing_skills[:2])
        if lang == "vi":
            parts.append(
                f"Mô tả công việc nhấn mạnh {gap} là yêu cầu quan trọng. "
                "Tôi đang chủ động phát triển năng lực trong các lĩnh vực này, "
                "và bạn nên xem lại phần này trước khi nộp hồ sơ."
            )
        else:
            parts.append(
                f"The JD highlights {gap} as key requirements. "
                "I am actively developing expertise in these areas, "
                "though I recommend reviewing this section before submitting your application."
            )

    if not parts:
        if lang == "vi":
            parts.append(
                "Nền tảng của tôi phù hợp với yêu cầu của vị trí. "
                "Vui lòng xem lại phần này và bổ sung bằng chứng cụ thể từ hồ sơ năng lực."
            )
        else:
            parts.append(
                "My background aligns with the role requirements. "
                "Please review this section and add specific evidence from your career profile."
            )

    return " ".join(parts)
