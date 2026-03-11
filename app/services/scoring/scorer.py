from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.services.embedding.engine import embed_texts, cosine_similarity
from app.services.ontology.skill_ontology import get_skill_ontology


def score(cv_parsed: dict, jd_struct: dict) -> dict:
    """
    Hybrid scorer v2:
    - skill matching by OR-groups + aliases + related concepts
    - semantic responsibility matching using embeddings
    - cv quality checks
    - evidence extraction
    """
    cv_text = cv_parsed["text"]
    cv_bullets = cv_parsed.get("bullets", [])
    cv_skills = set(cv_parsed.get("skills_detected", []))

    must_groups = jd_struct.get("must_have_skill_groups", [])
    nice_groups = jd_struct.get("nice_to_have_skill_groups", [])
    responsibilities = jd_struct.get("responsibilities", [])

    skill_result = evaluate_skill_groups(cv_text, cv_skills, must_groups, nice_groups)
    resp_result = evaluate_responsibilities(cv_bullets, responsibilities)
    cv_quality = evaluate_cv_quality(cv_text, cv_bullets)

    skill_match_score = skill_result["score"]
    responsibility_score = resp_result["score"]
    cv_quality_score = cv_quality["score"]
    project_relevance = min(100.0, 40.0 + len(cv_bullets) * 1.2)
    experience_level_score = infer_experience_alignment(cv_text, jd_struct)

    fit_score = round(
        0.35 * skill_match_score
        + 0.30 * responsibility_score
        + 0.15 * experience_level_score
        + 0.10 * project_relevance
        + 0.10 * cv_quality_score,
        1
    )

    learn_suggestions = build_learning_plan(skill_result["missing_must_have"] + skill_result["missing_nice_to_have"])

    return {
        "scores": {
            "fit_score": fit_score,
            "skill_match": round(skill_match_score, 1),
            "responsibility_match": round(responsibility_score, 1),
            "experience_level": round(experience_level_score, 1),
            "project_relevance": round(project_relevance, 1),
            "cv_quality": round(cv_quality_score, 1),
        },
        "skills": {
            "matched_must_groups": skill_result["matched_must_groups"],
            "matched_nice_groups": skill_result["matched_nice_groups"],
        },
        "skill_gap": {
            "missing_must_have": skill_result["missing_must_have"],
            "missing_nice_to_have": skill_result["missing_nice_to_have"],
            "learn_suggestions": learn_suggestions,
        },
        "responsibility_match": {
            "details": resp_result["details"]
        },
        "cv_improvements": cv_quality["issues"],
        "evidence": skill_result["evidence"] + resp_result["evidence"]
    }


def evaluate_skill_groups(
    cv_text: str,
    cv_skills: set[str],
    must_groups: List[List[str]],
    nice_groups: List[List[str]],
) -> dict:
    ontology = get_skill_ontology()
    cv_lower = cv_text.lower()

    matched_must_groups = []
    matched_nice_groups = []
    missing_must_have = []
    missing_nice_to_have = []
    evidence = []

    must_hits = 0
    for group in must_groups:
        matched_skill, ev = _match_group(group, cv_lower, cv_skills, ontology)
        if matched_skill:
            must_hits += 1
            matched_must_groups.append({
                "group": group,
                "matched_by": matched_skill
            })
            if ev:
                evidence.append(ev)
        else:
            missing_must_have.append(" / ".join(group))

    nice_hits = 0
    for group in nice_groups:
        matched_skill, ev = _match_group(group, cv_lower, cv_skills, ontology)
        if matched_skill:
            nice_hits += 1
            matched_nice_groups.append({
                "group": group,
                "matched_by": matched_skill
            })
            if ev:
                evidence.append(ev)
        else:
            missing_nice_to_have.append(" / ".join(group))

    must_cov = (must_hits / max(1, len(must_groups))) * 100 if must_groups else 100.0
    nice_cov = (nice_hits / max(1, len(nice_groups))) * 100 if nice_groups else 100.0

    score = 0.85 * must_cov + 0.15 * nice_cov

    return {
        "score": score,
        "matched_must_groups": matched_must_groups,
        "matched_nice_groups": matched_nice_groups,
        "missing_must_have": missing_must_have,
        "missing_nice_to_have": missing_nice_to_have,
        "evidence": evidence[:20],
    }


def _match_group(group: List[str], cv_lower: str, cv_skills: set[str], ontology) -> Tuple[str | None, dict | None]:
    for skill in group:
        candidates = ontology.expand_candidates(skill)
        for c in candidates:
            if c in cv_skills or _has_phrase(cv_lower, c):
                snippet = _find_evidence_line(cv_lower, c)
                return skill, {
                    "type": "skill_match",
                    "skill_group": group,
                    "matched_skill": skill,
                    "text": snippet or f"Matched by skill/alias: {c}"
                }
    return None, None


def evaluate_responsibilities(cv_bullets: List[str], responsibilities: List[str]) -> dict:
    if not cv_bullets:
        return {"score": 20.0, "details": [], "evidence": []}
    if not responsibilities:
        return {"score": 60.0, "details": [], "evidence": []}

    cv_bullets = cv_bullets[:40]
    responsibilities = responsibilities[:25]

    cv_vecs = embed_texts(cv_bullets)
    jd_vecs = embed_texts(responsibilities)

    details = []
    evidence = []
    sims = []

    for req, req_vec in zip(responsibilities, jd_vecs):
        best_idx = -1
        best_sim = -1.0
        for idx, cv_vec in enumerate(cv_vecs):
            sim = cosine_similarity(req_vec, cv_vec)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        sims.append(best_sim)
        matched_bullet = cv_bullets[best_idx] if best_idx >= 0 else None

        details.append({
            "jd_requirement": req,
            "best_cv_bullet": matched_bullet,
            "similarity": round(best_sim, 4),
        })

        if matched_bullet:
            evidence.append({
                "type": "responsibility_match",
                "jd_requirement": req,
                "text": matched_bullet,
                "similarity": round(best_sim, 4),
            })

    avg_sim = sum(sims) / max(1, len(sims))
    # map cosine similarity to 0..100
    score = max(0.0, min(100.0, avg_sim * 100.0))

    return {
        "score": score,
        "details": details[:15],
        "evidence": evidence[:10],
    }


def evaluate_cv_quality(cv_text: str, cv_bullets: List[str]) -> dict:
    issues = []

    if len(cv_text) < 400:
        issues.append({
            "issue": "CV text too short or parser quality may be low",
            "fix": "Use text-based PDF/DOCX and check whether full CV content is extracted"
        })

    if "@" not in cv_text and "email" not in cv_text.lower():
        issues.append({
            "issue": "Contact/email not clearly visible",
            "fix": "Add a clear contact section with professional email"
        })

    number_count = len(re.findall(r"\b\d+(\.\d+)?%?\b", cv_text))
    if number_count < 3:
        issues.append({
            "issue": "Low number of measurable achievements",
            "fix": "Add metrics such as accuracy, latency, users, cost saved, time reduced"
        })

    action_verbs = ["built", "developed", "designed", "implemented", "optimized", "deployed", "trained"]
    action_hits = sum(1 for b in cv_bullets[:20] if any(v in b.lower() for v in action_verbs))
    if action_hits < 3:
        issues.append({
            "issue": "Bullets are not strongly action-oriented",
            "fix": "Rewrite bullets with strong action verbs and outcomes"
        })

    score = max(40.0, 100.0 - 12.5 * len(issues))
    return {"score": score, "issues": issues}


def infer_experience_alignment(cv_text: str, jd_struct: dict) -> float:
    # lightweight heuristic for v2
    years = _estimate_years_from_text(cv_text)
    if years >= 3:
        return 85.0
    if years >= 1:
        return 70.0
    return 55.0


def build_learning_plan(missing_skills: List[str]) -> List[dict]:
    plans = []
    for s in missing_skills[:8]:
        plans.append({
            "skill": s,
            "reason": "Required or useful in JD but not sufficiently evidenced in CV",
            "resources_level": "beginner",
            "time_estimate_weeks": 2 if "/" not in s else 3
        })
    return plans


def _has_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(phrase.lower())}(?!\w)"
    return re.search(pattern, text.lower()) is not None


def _find_evidence_line(text: str, phrase: str) -> str | None:
    for line in text.splitlines():
        if phrase.lower() in line.lower():
            return line.strip()[:240]
    return None


def _estimate_years_from_text(text: str) -> int:
    years = re.findall(r"\b(20\d{2})\b", text)
    years = sorted({int(y) for y in years})
    if len(years) >= 2:
        return max(0, years[-1] - years[0])
    return 0