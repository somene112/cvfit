"""Deterministic interview practice service — no LLM, rule-based scoring only."""

from __future__ import annotations

from typing import Any, Optional

QUESTIONS_DISCLAIMER = (
    "Questions are generated from your CV, JD, and analysis result. "
    "They are practice aids only — real interviewers may ask different questions."
)

FEEDBACK_DISCLAIMER = (
    "Feedback is generated from your CV, JD, application workspace, and provided answer. "
    "Review before using in a real interview."
)

MAX_QUESTIONS = 8


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generate_interview_questions(
    application: Any,
    job: Optional[Any],
    profile_items: list,
) -> list[dict]:
    """Return up to MAX_QUESTIONS interview question dicts."""
    result: dict = job.result_json if (job and job.result_json) else {}

    matched_skills = _extract_skill_list(result.get("matched_skills"))
    missing_skills = _extract_skill_list(result.get("missing_skills"))
    jd_requirements = _extract_jd_requirements(result)

    questions: list[dict] = []

    # 1. Pull existing interview_prep questions from result_json first (max 3)
    existing = _extract_existing_prep(result)
    for i, q in enumerate(existing[:3]):
        skill = q.get("related_skill") or ""
        questions.append({
            "question_id": f"q_{len(questions) + 1}",
            "question": q["question"],
            "type": q.get("type", "technical"),
            "related_jd_requirement": _find_jd_requirement(skill, jd_requirements),
            "related_cv_evidence": _find_cv_evidence(skill, profile_items),
            "why_this_question": q.get("why", f"{skill} appears in the analysis result.") if skill else "Sourced from your prior analysis.",
        })

    # 2. project_deep_dive for profile items that match a matched skill
    for item in profile_items:
        if len(questions) >= MAX_QUESTIONS:
            break
        item_type = getattr(item, "item_type", "") or ""
        if item_type not in ("project", "experience"):
            continue
        title = getattr(item, "title", "") or ""
        desc = getattr(item, "description", "") or ""
        item_skills = _item_skill_list(item)
        overlap = [s for s in matched_skills if _skill_in_item(s, item)]
        if not overlap:
            continue
        skill_ref = overlap[0]
        questions.append({
            "question_id": f"q_{len(questions) + 1}",
            "question": (
                f"Describe your work on '{title}'. "
                f"What challenges did you face and how does it relate to {skill_ref}?"
            ),
            "type": "project_deep_dive",
            "related_jd_requirement": _find_jd_requirement(skill_ref, jd_requirements),
            "related_cv_evidence": [title] + ([desc[:80]] if desc else []),
            "why_this_question": (
                f"{skill_ref} appears in both the JD and your career profile item '{title}'."
            ),
        })

    # 3. technical questions for matched skills not yet covered
    covered_skills = _collect_covered_skills(questions)
    for skill in matched_skills:
        if len(questions) >= MAX_QUESTIONS:
            break
        if skill.lower() in covered_skills:
            continue
        evidence = _find_cv_evidence(skill, profile_items)
        questions.append({
            "question_id": f"q_{len(questions) + 1}",
            "question": (
                f"The JD requires {skill}. Can you describe a situation where you applied {skill} "
                "in a project or professional context?"
            ),
            "type": "technical",
            "related_jd_requirement": _find_jd_requirement(skill, jd_requirements),
            "related_cv_evidence": evidence,
            "why_this_question": f"{skill} is a matched skill from your CV and JD.",
        })

    # 4. gap_probe for must-have missing skills (prioritised first)
    for skill_info in _extract_skill_list_raw(result.get("missing_skills")):
        if len(questions) >= MAX_QUESTIONS:
            break
        skill, req_type = _parse_skill_info(skill_info)
        if not skill:
            continue
        if req_type == "must_have":
            questions.append({
                "question_id": f"q_{len(questions) + 1}",
                "question": (
                    f"The JD requires {skill} experience. "
                    f"How would you approach learning and applying {skill} for this role?"
                ),
                "type": "gap_probe",
                "related_jd_requirement": f"{skill} ({req_type})",
                "related_cv_evidence": [],
                "why_this_question": (
                    f"{skill} evidence was not found in the parsed CV. This is a must-have JD requirement."
                ),
            })

    # 5. gap_probe for nice-to-have missing skills if still room
    for skill_info in _extract_skill_list_raw(result.get("missing_skills")):
        if len(questions) >= MAX_QUESTIONS:
            break
        skill, req_type = _parse_skill_info(skill_info)
        if not skill:
            continue
        if req_type != "must_have":
            already = any(
                q["type"] == "gap_probe" and skill.lower() in q["question"].lower()
                for q in questions
            )
            if not already:
                questions.append({
                    "question_id": f"q_{len(questions) + 1}",
                    "question": (
                        f"The JD mentions {skill}. Do you have any experience with {skill}? "
                        "If not, how would you plan to develop this skill?"
                    ),
                    "type": "gap_probe",
                    "related_jd_requirement": f"{skill} ({req_type})",
                    "related_cv_evidence": [],
                    "why_this_question": (
                        f"{skill} was listed as a nice-to-have JD requirement not found in your CV."
                    ),
                })

    # 6. Fallback: generic behavioral questions when no analysis produced any questions
    if not questions:
        job_title = getattr(application, "job_title", "this role") or "this role"
        questions.extend([
            {
                "question_id": "q_1",
                "question": (
                    f"Why are you interested in the {job_title} role? "
                    "What about this opportunity aligns with your professional goals?"
                ),
                "type": "behavioral",
                "related_jd_requirement": job_title,
                "related_cv_evidence": [],
                "why_this_question": (
                    "No analysis result is attached yet. "
                    "This is a general readiness question to help you prepare."
                ),
            },
            {
                "question_id": "q_2",
                "question": (
                    "Describe a challenging project you have worked on. "
                    "What was your role and what did you learn from the experience?"
                ),
                "type": "behavioral",
                "related_jd_requirement": job_title,
                "related_cv_evidence": [
                    getattr(item, "title", "")
                    for item in profile_items
                    if getattr(item, "item_type", "") in ("project", "experience")
                ][:2],
                "why_this_question": (
                    "This behavioral question helps assess relevant background "
                    "regardless of a specific JD analysis."
                ),
            },
        ])

    return questions[:MAX_QUESTIONS]


# ---------------------------------------------------------------------------
# Rubric scoring
# ---------------------------------------------------------------------------

def score_answer(
    question: str,
    answer_text: str,
    application: Any,
    job: Optional[Any],
    profile_items: list,
) -> tuple[dict, dict]:
    """Return (rubric_dict, feedback_dict)."""
    result: dict = job.result_json if (job and job.result_json) else {}
    matched_skills = _extract_skill_list(result.get("matched_skills"))
    missing_skills = _extract_skill_list(result.get("missing_skills"))

    answer_lower = answer_text.lower()
    question_lower = question.lower()

    # --- relevance: answer addresses the question topic ---
    question_keywords = _extract_keywords(question_lower)
    keyword_hits = sum(1 for kw in question_keywords if kw in answer_lower)
    relevance = min(5, keyword_hits + (1 if len(answer_text) > 50 else 0))

    # --- specificity: specific details, numbers, tech terms ---
    specificity = _score_specificity(answer_text)

    # --- evidence: references known CV/profile items ---
    evidence_score, matched_evidence = _score_evidence(answer_lower, profile_items, matched_skills)

    # --- structure: STAR / logical flow ---
    structure = _score_structure(answer_text)

    # --- risk_gap: inverse scale — 0 = no gap risk (good), 5 = high gap risk (bad) ---
    # Per contract Section D: "Lower = better. 0 means no gap risk, 5 means high gap risk."
    risk_gap = _score_risk_gap(question_lower, answer_lower, missing_skills)

    # overall: weighted average, rounded to nearest int, capped at 5
    raw_overall = (relevance * 2 + specificity + evidence_score + structure + (5 - risk_gap)) / 6
    overall = max(0, min(5, round(raw_overall)))

    rubric = {
        "relevance": relevance,
        "specificity": specificity,
        "evidence": evidence_score,
        "structure": structure,
        "risk_gap": risk_gap,
        "overall": overall,
    }

    feedback = _build_feedback(
        answer_text=answer_text,
        question=question,
        rubric=rubric,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_evidence=matched_evidence,
        profile_items=profile_items,
    )

    return rubric, feedback


# ---------------------------------------------------------------------------
# Internal helpers — question generation
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


def _extract_skill_list_raw(raw: Any) -> list:
    if not isinstance(raw, list):
        return []
    return raw


def _parse_skill_info(skill_info: Any) -> tuple[str, str]:
    """Return (skill_name, requirement_type) from a raw skill list item."""
    if isinstance(skill_info, dict):
        skill = str(skill_info.get("skill") or skill_info.get("name") or "")
        req_type = str(skill_info.get("requirement_type") or "nice_to_have")
    elif isinstance(skill_info, str):
        skill = skill_info
        req_type = "nice_to_have"
    else:
        skill = ""
        req_type = "nice_to_have"
    return skill, req_type


def _extract_jd_requirements(result: dict) -> list[str]:
    reqs: list[str] = []
    for item in _extract_skill_list_raw(result.get("missing_skills")) + _extract_skill_list_raw(result.get("matched_skills")):
        if isinstance(item, dict):
            skill = item.get("skill") or item.get("name") or ""
            req_type = item.get("requirement_type", "")
            if skill:
                reqs.append(f"{skill} ({req_type})" if req_type else skill)
        elif isinstance(item, str):
            reqs.append(item)
    return reqs


def _find_jd_requirement(skill: str, requirements: list[str]) -> str:
    skill_lower = skill.lower()
    for req in requirements:
        if skill_lower in req.lower():
            return req
    return skill


def _find_cv_evidence(skill: str, profile_items: list) -> list[str]:
    skill_lower = skill.lower()
    evidence: list[str] = []
    for item in profile_items:
        item_skills = _item_skill_list(item)
        title = getattr(item, "title", "") or ""
        desc = getattr(item, "description", "") or ""
        if (
            any(skill_lower in str(s).lower() for s in item_skills)
            or skill_lower in title.lower()
            or skill_lower in desc.lower()
        ):
            evidence.append(title)
    return evidence[:3]


def _item_skill_list(item: Any) -> list:
    skills_json = getattr(item, "skills_json") or []
    return skills_json if isinstance(skills_json, list) else []


def _skill_in_item(skill: str, item: Any) -> bool:
    skill_lower = skill.lower()
    item_skills = _item_skill_list(item)
    title = str(getattr(item, "title", "") or "").lower()
    desc = str(getattr(item, "description", "") or "").lower()
    return (
        any(skill_lower in str(s).lower() for s in item_skills)
        or skill_lower in title
        or skill_lower in desc
    )


def _extract_existing_prep(result: dict) -> list[dict]:
    prep = result.get("interview_prep")
    if not isinstance(prep, list):
        return []
    out = []
    for q in prep:
        if isinstance(q, dict) and q.get("question"):
            out.append(q)
        elif isinstance(q, str) and q:
            out.append({"question": q})
    return out


def _collect_covered_skills(questions: list[dict]) -> set[str]:
    covered: set[str] = set()
    for q in questions:
        jd_req = q.get("related_jd_requirement", "").lower()
        for part in jd_req.split():
            covered.add(part.strip("().,"))
        for ev in q.get("related_cv_evidence", []):
            covered.add(ev.lower())
    return covered


# ---------------------------------------------------------------------------
# Internal helpers — scoring
# ---------------------------------------------------------------------------

def _extract_keywords(text: str) -> list[str]:
    stop = {"a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "how", "what", "describe", "explain", "your", "you", "would", "did", "do", "can", "is", "are", "was", "were", "this", "that", "it", "be"}
    return [w.strip("?.,'\"") for w in text.split() if len(w) > 3 and w not in stop]


def _score_specificity(answer_text: str) -> int:
    score = 0
    # numeric detail
    if any(c.isdigit() for c in answer_text):
        score += 1
    # length > 100 chars suggests substance
    if len(answer_text) > 100:
        score += 1
    # named tools/frameworks heuristic: capital words that aren't sentence starts
    words = answer_text.split()
    capitalized_mid = sum(
        1 for i, w in enumerate(words)
        if i > 0 and w and w[0].isupper() and not w.endswith(".")
    )
    if capitalized_mid >= 2:
        score += 1
    # specific outcome language
    outcome_words = {"result", "outcome", "achieved", "reduced", "improved", "increased", "delivered", "completed", "deployed", "shipped", "built", "created"}
    if any(ow in answer_text.lower() for ow in outcome_words):
        score += 1
    # action verbs
    action_words = {"used", "implemented", "designed", "developed", "configured", "integrated", "migrated", "refactored", "tested", "automated", "solved", "fixed", "led", "managed"}
    if any(aw in answer_text.lower() for aw in action_words):
        score += 1
    return min(5, score)


def _score_evidence(answer_lower: str, profile_items: list, matched_skills: list[str]) -> tuple[int, list[str]]:
    matched: list[str] = []
    for item in profile_items:
        title = str(getattr(item, "title", "") or "").lower()
        desc = str(getattr(item, "description", "") or "").lower()
        if title and title in answer_lower:
            matched.append(getattr(item, "title", ""))
        elif desc and any(word in answer_lower for word in desc.split() if len(word) > 4):
            matched.append(getattr(item, "title", ""))
    for skill in matched_skills:
        if skill.lower() in answer_lower:
            if skill not in matched:
                matched.append(skill)
    score = min(5, len(matched) + (1 if matched else 0))
    return score, matched[:5]


def _score_structure(answer_text: str) -> int:
    text_lower = answer_text.lower()
    score = 0
    # STAR markers
    star_keywords = {
        "situation": 1, "context": 1,
        "task": 1, "challenge": 1, "goal": 1,
        "action": 1, "approach": 1, "i used": 1, "i implemented": 1, "i decided": 1,
        "result": 1, "outcome": 1, "impact": 1,
    }
    hits = sum(1 for kw in star_keywords if kw in text_lower)
    score += min(3, hits)
    # Multiple sentences imply some structure
    sentences = [s.strip() for s in answer_text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) >= 3:
        score += 1
    # Connector words
    connectors = {"first", "then", "finally", "additionally", "however", "therefore", "because", "as a result", "in order to"}
    if any(c in text_lower for c in connectors):
        score += 1
    return min(5, score)


def _score_risk_gap(question_lower: str, answer_lower: str, missing_skills: list[str]) -> int:
    risk = 0
    for skill in missing_skills:
        if skill.lower() in question_lower:
            # Question is about a missing skill
            if skill.lower() not in answer_lower:
                risk += 2
            else:
                risk += 1
            break
    # Generic vague answer markers
    vague_phrases = {"i don't know", "not sure", "haven't used", "no experience", "never worked", "never used"}
    if any(vp in answer_lower for vp in vague_phrases):
        risk += 2
    # Very short answer is risky
    if len(answer_lower) < 40:
        risk += 1
    return min(5, risk)


def _build_feedback(
    answer_text: str,
    question: str,
    rubric: dict,
    matched_skills: list[str],
    missing_skills: list[str],
    matched_evidence: list[str],
    profile_items: list,
) -> dict:
    strengths: list[str] = []
    missing_evidence: list[str] = []
    suggested_improvements: list[str] = []
    sample_outline: list[str] = []
    risk_notes: list[str] = []

    answer_lower = answer_text.lower()

    # Strengths
    if matched_evidence:
        ev_names = ", ".join(matched_evidence[:2])
        strengths.append(f"Answer references evidence from your profile or CV: {ev_names}.")
    if rubric["specificity"] >= 3:
        strengths.append("Answer includes specific details such as tools, outcomes, or context.")
    if rubric["structure"] >= 3:
        strengths.append("Answer demonstrates a structured approach (STAR-like flow detected).")
    if rubric["relevance"] >= 3:
        strengths.append("Answer is relevant to the question topic.")
    if not strengths:
        strengths.append("You attempted to answer the question — that's a good start.")

    # Missing evidence
    question_lower = question.lower()
    for skill in matched_skills:
        if skill.lower() in question_lower and skill.lower() not in answer_lower:
            missing_evidence.append(
                f"The question references {skill}, which is in your CV — consider referencing it explicitly."
            )
    for skill in missing_skills:
        if skill.lower() in question_lower:
            missing_evidence.append(
                f"{skill} is a JD requirement not found in your CV. Be honest about your current level."
            )
    if rubric["evidence"] <= 2 and not missing_evidence:
        missing_evidence.append(
            "No specific CV or profile evidence was referenced. Try to anchor your answer in real experience."
        )

    # Suggested improvements
    if rubric["specificity"] <= 2:
        suggested_improvements.append(
            "Add specific details: tool names, scale, measurable outcomes, or concrete challenges."
        )
    if rubric["structure"] <= 2:
        suggested_improvements.append(
            "Try a STAR structure: Situation → Task → Action → Result."
        )
    if rubric["relevance"] <= 2:
        suggested_improvements.append(
            "Make sure your answer directly addresses what the question is asking."
        )
    if rubric["evidence"] <= 2:
        suggested_improvements.append(
            "Reference a specific project or experience from your career profile to ground your answer."
        )
    if not suggested_improvements:
        suggested_improvements.append(
            "Consider adding a measurable outcome (e.g., impact on performance, delivery timeline, or team size) if true."
        )

    # Sample outline — use the user's own context only
    profile_project = next(
        (getattr(item, "title", "") for item in profile_items if getattr(item, "item_type", "") in ("project", "experience")),
        None,
    )
    situation_ref = f"project: {profile_project}" if profile_project else "a relevant experience from your background"
    sample_outline = [
        f"Situation: {situation_ref}",
        "Task: describe the specific goal or challenge you faced",
        "Action: explain the steps you took, tools you used, and decisions you made",
        "Result: describe a real, verifiable outcome — do not fabricate metrics",
    ]

    # Risk notes
    if rubric["risk_gap"] >= 3:
        gap_skills = [s for s in missing_skills if s.lower() in question_lower]
        if gap_skills:
            risk_notes.append(
                f"If a real interviewer presses on {gap_skills[0]}, you will need to be honest about your current level. "
                "Practice explaining your learning plan clearly."
            )
        else:
            risk_notes.append(
                "This answer has areas that may be difficult to elaborate on in a real interview. "
                "Prepare specific examples in advance."
            )
    if rubric["overall"] <= 2:
        risk_notes.append(
            "This answer is currently weak. Revisit with more specific evidence before your actual interview."
        )
    if not risk_notes:
        risk_notes.append(
            "Ensure you can elaborate on any claim in this answer with a specific real example."
        )

    return {
        "strengths": strengths,
        "missing_evidence": missing_evidence,
        "suggested_improvements": suggested_improvements,
        "sample_outline": sample_outline,
        "risk_notes": risk_notes,
        "disclaimer": FEEDBACK_DISCLAIMER,
    }
