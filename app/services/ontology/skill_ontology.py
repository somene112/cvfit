from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml


class SkillOntology:
    def __init__(self, skills: Dict[str, dict]):
        self.skills = skills
        self.alias_to_canonical: Dict[str, str] = {}
        self.related_map: Dict[str, List[str]] = {}

        for canonical, meta in skills.items():
            c = canonical.strip().lower()
            self.alias_to_canonical[c] = c
            for alias in meta.get("aliases", []):
                self.alias_to_canonical[alias.strip().lower()] = c
            self.related_map[c] = [x.strip().lower() for x in meta.get("related", [])]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SkillOntology":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(data)

    def normalize(self, skill: str) -> str:
        s = skill.strip().lower()
        return self.alias_to_canonical.get(s, s)

    def expand_candidates(self, skill: str) -> Set[str]:
        """
        Return all strings that should be checked for this skill:
        canonical + aliases + related.
        """
        canonical = self.normalize(skill)
        candidates = {canonical}

        for alias, c in self.alias_to_canonical.items():
            if c == canonical:
                candidates.add(alias)

        for rel in self.related_map.get(canonical, []):
            candidates.add(rel)

        return candidates

    def detect_skills_in_text(self, text: str) -> Set[str]:
        lower = text.lower()
        found = set()

        for alias, canonical in self.alias_to_canonical.items():
            if _has_phrase(lower, alias):
                found.add(canonical)

        return found


def _has_phrase(text: str, phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(phrase.lower())}(?!\w)"
    return re.search(pattern, text.lower()) is not None


_ontology_cache: SkillOntology | None = None


def get_skill_ontology() -> SkillOntology:
    global _ontology_cache
    if _ontology_cache is None:
        base = Path(__file__).resolve().parent
        _ontology_cache = SkillOntology.from_yaml(base / "skills.yaml")
    return _ontology_cache