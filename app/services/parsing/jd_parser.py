from __future__ import annotations

import re
from typing import List, Dict

from app.services.ontology.skill_ontology import get_skill_ontology


REQUIRED_HINTS = [
    "required", "must have", "must-have", "mandatory", "need", "needs",
    "strong experience with", "proficient in", "experience with"
]

PREFERRED_HINTS = [
    "preferred", "nice to have", "plus", "bonus", "good to have",
    "preferred qualifications"
]


def parse_jd(jd_text: str) -> dict:
    """
    JD parser v2:
    - detect skill groups with OR logic (e.g. TensorFlow or PyTorch)
    - separate must-have / nice-to-have
    - extract responsibility lines
    """
    ontology = get_skill_ontology()
    text = jd_text.strip()
    lower = text.lower()

    lines = [x.strip("•-* \t") for x in text.splitlines()]
    lines = [x for x in lines if x]

    responsibilities = [l for l in lines if len(l) >= 20][:40]

    skill_groups = []
    seen_groups = set()

    # 1) detect OR groups line-by-line
    for line in lines:
        line_lower = line.lower()
        groups = _extract_or_groups(line_lower, ontology)
        for g in groups:
            g = sorted(set(g))
            if not g:
                continue
            key = tuple(g)
            if key not in seen_groups:
                seen_groups.add(key)
                skill_groups.append({
                    "group": g,
                    "type": _infer_requirement_type(line_lower),
                    "source_line": line
                })

    # 2) detect standalone skills in lines not already covered
    all_detected = ontology.detect_skills_in_text(text)

    grouped_skills = set()
    for sg in skill_groups:
        grouped_skills.update(sg["group"])

    remaining = sorted(all_detected - grouped_skills)
    for s in remaining:
        skill_groups.append({
            "group": [s],
            "type": "preferred" if _is_preferred_context(lower, s) else "required",
            "source_line": None
        })

    must_groups = [x["group"] for x in skill_groups if x["type"] == "required"]
    nice_groups = [x["group"] for x in skill_groups if x["type"] == "preferred"]

    return {
        "role": _infer_role(text),
        "must_have_skill_groups": must_groups,
        "nice_to_have_skill_groups": nice_groups,
        "responsibilities": responsibilities,
        "skill_group_details": skill_groups,
    }


def _extract_or_groups(line: str, ontology) -> List[List[str]]:
    """
    Example:
      "Experience with TensorFlow or PyTorch"
      "Docker / Kubernetes"
      "FastAPI, Flask or Django"
    """
    separators = [" or ", "/", "|"]
    groups = []

    normalized = line
    for sep in separators:
        if sep in normalized:
            parts = [p.strip(" ,.;:()[]{}") for p in normalized.split(sep)]
            detected = []
            for p in parts:
                found = ontology.detect_skills_in_text(p)
                if found:
                    detected.extend(list(found))
            detected = sorted(set(detected))
            if len(detected) >= 2:
                groups.append(detected)

    return groups


def _infer_requirement_type(line: str) -> str:
    l = line.lower()
    for hint in PREFERRED_HINTS:
        if hint in l:
            return "preferred"
    return "required"


def _is_preferred_context(full_text: str, skill: str) -> bool:
    skill = skill.lower()
    for hint in PREFERRED_HINTS:
        if hint in full_text:
            # lightweight heuristic: if preferred section exists, standalone skills
            # may lean preferred
            return True
    return False


def _infer_role(text: str) -> str | None:
    lower = text.lower()
    patterns = [
        r"\bbackend engineer\b",
        r"\bsoftware engineer\b",
        r"\bmachine learning engineer\b",
        r"\bdata scientist\b",
        r"\bcomputer vision engineer\b",
        r"\bai engineer\b",
        r"\bfull stack developer\b",
        r"\bbackend developer\b",
    ]
    for p in patterns:
        m = re.search(p, lower)
        if m:
            return m.group(0).title()
    return None