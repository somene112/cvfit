import re

def score(cv_text: str, jd_struct: dict) -> dict:
    cv_lower = cv_text.lower()
    must = jd_struct.get("must_have_skills", [])
    nice = jd_struct.get("nice_to_have_skills", [])

    must_hit = [s for s in must if _has_skill(cv_lower, s)]
    must_miss = [s for s in must if s not in must_hit]

    nice_hit = [s for s in nice if _has_skill(cv_lower, s)]
    nice_miss = [s for s in nice if s not in nice_hit]

    must_cov = (len(must_hit) / max(1, len(must))) * 100
    nice_cov = (len(nice_hit) / max(1, len(nice))) * 100 if nice else 0

    # Simple CV quality checks
    quality_issues = []
    if len(cv_text) < 400:
        quality_issues.append({"issue":"CV text too short / parse may be poor", "fix":"Check file quality or use text-based PDF/DOCX"})
    if "@" not in cv_text and "email" not in cv_lower:
        quality_issues.append({"issue":"Missing email/contact visible", "fix":"Ensure contact section is included"})
    if _count_numbers(cv_text) < 3:
        quality_issues.append({"issue":"Few measurable metrics", "fix":"Add numbers (latency, users, accuracy, revenue, time saved)"})

    # Weighted fit score
    skill_score = 0.85 * must_cov + 0.15 * nice_cov
    cv_quality = 100 - min(40, 15 * len(quality_issues))
    fit_score = round(0.45 * skill_score + 0.10 * cv_quality + 0.45 * _resp_proxy(cv_lower, jd_struct), 1)

    learn_suggestions = [{"skill": s, "reason":"Mentioned/required in JD but not found in CV", "resources_level":"beginner"} for s in must_miss[:8]]

    return {
        "scores": {
            "fit_score": fit_score,
            "skill_match": round(skill_score, 1),
            "cv_quality": round(cv_quality, 1),
            "responsibility_match": round(_resp_proxy(cv_lower, jd_struct), 1),
        },
        "skill_gap": {
            "missing_must_have": must_miss,
            "missing_nice_to_have": nice_miss,
            "learn_suggestions": learn_suggestions
        },
        "cv_improvements": quality_issues,
        "evidence": _evidence_snippets(cv_text, must_hit)
    }

def _has_skill(cv_lower: str, skill: str) -> bool:
    return re.search(rf"\b{re.escape(skill)}\b", cv_lower) is not None

def _count_numbers(text: str) -> int:
    return len(re.findall(r"\b\d+(\.\d+)?%?\b", text))

def _resp_proxy(cv_lower: str, jd_struct: dict) -> float:
    # MVP proxy: % responsibility lines that share >=1 keyword hit in CV
    resp = jd_struct.get("responsibilities", [])[:20]
    if not resp:
        return 50.0
    hits = 0
    for line in resp:
        kws = [w for w in re.findall(r"[a-zA-Z]{4,}", line.lower()) if w not in {"with","and","from","that","have","will"}]
        if any((kw in cv_lower) for kw in kws[:8]):
            hits += 1
    return (hits / len(resp)) * 100

def _evidence_snippets(cv_text: str, skills_hit: list[str]) -> list[dict]:
    lines = [l.strip() for l in cv_text.splitlines() if len(l.strip()) > 0]
    out = []
    for s in skills_hit[:8]:
        for l in lines:
            if s.lower() in l.lower():
                out.append({"type":"cv_line", "skill": s, "text": l[:240]})
                break
    return out[:20]