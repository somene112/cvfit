from docx import Document

def build_docx_report(result: dict, out_path: str):
    doc = Document()
    doc.add_heading("CV Fit Report (CV vs JD)", level=1)

    scores = result.get("scores", {})
    doc.add_heading("Scores", level=2)
    for k, v in scores.items():
        doc.add_paragraph(f"{k}: {v}")

    gap = result.get("skill_gap", {})
    doc.add_heading("Missing Skills", level=2)
    doc.add_paragraph("Must-have missing: " + ", ".join(gap.get("missing_must_have", [])) or "None")
    doc.add_paragraph("Nice-to-have missing: " + ", ".join(gap.get("missing_nice_to_have", [])) or "None")

    doc.add_heading("Suggestions to Learn", level=2)
    for item in gap.get("learn_suggestions", []):
        doc.add_paragraph(f"- {item['skill']}: {item['reason']} ({item['resources_level']})")

    doc.add_heading("CV Improvements", level=2)
    for item in result.get("cv_improvements", []):
        doc.add_paragraph(f"- {item['issue']} → {item['fix']}")

    doc.add_heading("Evidence", level=2)
    for e in result.get("evidence", []):
        doc.add_paragraph(f"- [{e.get('skill','')}] {e.get('text','')}")

    doc.save(out_path)