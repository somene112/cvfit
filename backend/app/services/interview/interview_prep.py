from __future__ import annotations

from typing import Any

from app.services.i18n import resolve_language


def build_interview_prep(result: dict, *, max_questions: int = 6, language: str = "en") -> list[dict]:
    lang = resolve_language(language)
    questions: list[dict] = []

    for item in _matched_skills(result):
        if len(questions) >= max_questions:
            break
        skill = _safe_label(item.get("skill") or ("kỹ năng này" if lang == "vi" else "this skill"))
        cv_ids = _ids(item.get("cv_evidence_ids"))
        if lang == "vi":
            questions.append(
                {
                    "question": (
                        f"Bạn có thể trình bày một dự án hoặc nhiệm vụ thực tế mà bạn đã sử dụng {skill}, "
                        "bao gồm vai trò, các lựa chọn triển khai và kết quả không?"
                    ),
                    "type": "project_deep_dive",
                    "why_this_question": (
                        f"Mô tả công việc có vẻ coi trọng {skill}, và CV đã phân tích chứa bằng chứng liên quan."
                    ),
                    "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                    "related_cv_evidence": cv_ids,
                    "suggested_answer_outline": [
                        "Nêu bối cảnh dự án hoặc nhiệm vụ thực tế.",
                        "Giải thích trách nhiệm cụ thể của bạn.",
                        "Mô tả các công cụ và lựa chọn triển khai thực tế.",
                        "Chia sẻ một kết quả hoặc bài học thực tế nếu bạn có thể kiểm chứng.",
                    ],
                    "risk_if_user_cannot_answer": (
                        f"Nếu bạn không thể giải thích bằng chứng về {skill}, mức độ phù hợp có thể trông hời hợt khi phỏng vấn."
                    ),
                }
            )
        else:
            questions.append(
                {
                    "question": (
                        f"Can you walk through a real project or task where you used {skill}, including your role, "
                        "the implementation choices, and the outcome?"
                    ),
                    "type": "project_deep_dive",
                    "why_this_question": (
                        f"The JD appears to value {skill}, and the parsed CV contains related evidence."
                    ),
                    "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                    "related_cv_evidence": cv_ids,
                    "suggested_answer_outline": [
                        "State the real project or task context.",
                        "Explain your specific responsibility.",
                        "Describe the actual tools and implementation choices.",
                        "Share a real outcome or lesson learned if you can verify it.",
                    ],
                    "risk_if_user_cannot_answer": (
                        f"If you cannot explain the {skill} evidence, the match may appear shallow in interview."
                    ),
                }
            )

    for item in _missing_skills(result):
        if len(questions) >= max_questions:
            break
        skill = _safe_label(item.get("skill") or ("kỹ năng này" if lang == "vi" else "this skill"))
        if lang == "vi":
            questions.append(
                {
                    "question": (
                        f"Mô tả công việc có đề cập đến {skill}. Mức độ hiện tại của bạn với kỹ năng này ra sao, "
                        "và bạn sẽ làm gì để thu hẹp khoảng cách?"
                    ),
                    "type": "gap_probe",
                    "why_this_question": (
                        f"Không tìm thấy bằng chứng về {skill} trong CV đã phân tích, nên người phỏng vấn có thể "
                        "dò hỏi về khoảng trống này."
                    ),
                    "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                    "related_cv_evidence": [],
                    "suggested_answer_outline": [
                        "Hãy trung thực về việc bạn đã sử dụng kỹ năng này hay chưa.",
                        "Nếu đã dùng, chỉ mô tả bối cảnh thực tế.",
                        "Nếu chưa dùng, hãy trình bày kế hoạch học tập hoặc nền tảng liên quan.",
                        "Tránh tuyên bố kinh nghiệm mà bạn không thể chứng minh.",
                    ],
                    "risk_if_user_cannot_answer": (
                        "Nếu đây là yêu cầu bắt buộc, việc chuẩn bị yếu có thể làm giảm mức độ sẵn sàng phỏng vấn."
                    ),
                }
            )
        else:
            questions.append(
                {
                    "question": f"The JD mentions {skill}. What is your current level with it, and how would you close the gap?",
                    "type": "gap_probe",
                    "why_this_question": (
                        f"{skill} evidence was not found in the parsed CV, so an interviewer may probe this gap."
                    ),
                    "related_jd_requirement": _safe_label(item.get("jd_requirement") or skill),
                    "related_cv_evidence": [],
                    "suggested_answer_outline": [
                        "Be honest about whether you have used the skill.",
                        "If you have used it, describe only the real context.",
                        "If you have not used it, explain the learning plan or related foundation.",
                        "Avoid claiming experience you cannot support.",
                    ],
                    "risk_if_user_cannot_answer": (
                        "If this is a must-have requirement, weak preparation may reduce interview readiness."
                    ),
                }
            )

    return questions[:max_questions]


def _matched_skills(result: dict) -> list[dict]:
    matched = result.get("matched_skills")
    if isinstance(matched, list):
        return [item for item in matched if isinstance(item, dict)]
    return []


def _missing_skills(result: dict) -> list[dict]:
    missing = result.get("missing_skills")
    if isinstance(missing, list):
        return [item for item in missing if isinstance(item, dict)]
    return []


def _ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _safe_label(value: Any) -> str:
    text = str(value or "").strip()
    return text[:220] if text else "this requirement"
