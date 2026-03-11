from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
import docx2txt

from app.services.ontology.skill_ontology import get_skill_ontology


SECTION_HEADERS = [
    "summary", "objective", "experience", "work experience", "projects",
    "skills", "education", "certifications", "awards"
]


def parse_cv_to_text(storage_path: str) -> dict:
    p = Path(storage_path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(storage_path)
        pages = [(page.extract_text() or "") for page in reader.pages]
        text = "\n".join(pages)
    elif suffix in (".docx", ".doc"):
        text = docx2txt.process(storage_path) or ""
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    text = clean_text(text)
    sections = split_sections(text)
    bullets = extract_bullets(text)
    ontology = get_skill_ontology()
    detected_skills = sorted(ontology.detect_skills_in_text(text))

    confidence = 0.85 if len(text) >= 300 else 0.35

    return {
        "text": text,
        "sections": sections,
        "bullets": bullets,
        "skills_detected": detected_skills,
        "confidence": confidence,
    }


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_sections(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines()]
    out = {"raw": text}
    current = "raw"

    for line in lines:
        lower = line.lower().strip(":")
        if lower in SECTION_HEADERS:
            current = lower.replace(" ", "_")
            out.setdefault(current, "")
            continue

        out.setdefault(current, "")
        out[current] += (line + "\n")

    for k, v in list(out.items()):
        out[k] = v.strip()

    return out


def extract_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("-", "•", "*")):
            line = line.lstrip("-•* ").strip()
        if len(line) >= 25:
            bullets.append(line)

    # fallback: if no bullet-like lines, slice longer lines
    if not bullets:
        bullets = [l.strip() for l in text.splitlines() if len(l.strip()) >= 40]

    return bullets[:80]