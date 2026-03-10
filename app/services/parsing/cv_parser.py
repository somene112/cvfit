from pathlib import Path
from pypdf import PdfReader
import docx2txt

def parse_cv_to_text(storage_path: str) -> dict:
    p = Path(storage_path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(storage_path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n".join(pages)
    elif suffix in (".docx", ".doc"):
        # docx2txt supports docx; for .doc you may need extra converter later
        text = docx2txt.process(storage_path) or ""
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    text = text.strip()
    sections = _naive_section_split(text)
    return {"text": text, "sections": sections, "confidence": 0.80 if text else 0.2}

def _naive_section_split(text: str) -> dict:
    # MVP heuristic. Replace with robust parser later.
    keys = ["summary", "experience", "projects", "skills", "education", "certifications"]
    lower = text.lower()
    out = {k: "" for k in keys}
    out["raw"] = text

    # Very simple: just keep raw for now
    return out