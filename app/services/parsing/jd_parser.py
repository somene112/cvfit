import re

COMMON_SKILLS = [
    "python","java","javascript","typescript","sql","postgresql","mysql",
    "docker","kubernetes","redis","fastapi","django","flask","nodejs","nestjs",
    "aws","gcp","azure","git","linux","pytorch","tensorflow"
]

def parse_jd(jd_text: str) -> dict:
    t = jd_text.strip()
    lower = t.lower()

    must = []
    nice = []
    for s in COMMON_SKILLS:
        if re.search(rf"\b{re.escape(s)}\b", lower):
            must.append(s)

    # MVP: treat all found as must-have; refine with pattern (required/preferred) later
    return {
        "role": None,
        "must_have_skills": sorted(set(must)),
        "nice_to_have_skills": sorted(set(nice)),
        "responsibilities": _extract_bullets(t),
    }

def _extract_bullets(text: str) -> list[str]:
    lines = [x.strip("•-* \t") for x in text.splitlines()]
    return [l for l in lines if len(l) >= 20][:30]