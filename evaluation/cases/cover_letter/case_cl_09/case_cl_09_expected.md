# Cover Letter Case 09: Irrelevant CV/JD — Neutral Tone

## CV Profile
- **Name:** Tran Thi Mai
- **Email:** mai.Graphic@email.com
- **Skills:** Adobe Photoshop, Adobe Illustrator, Figma, Brand Identity Design, UI/UX Design
- **Projects:** Brand Identity Package (logo design, color palette, marketing materials)

## JD Profile
- **Required Skills:** Python, FastAPI or Django, PostgreSQL, RESTful APIs, Docker
- **Experience Level:** Mid-level backend developer
- **Focus Areas:** Server-side development, API design, database optimization

## Profile Items
- Project: "Brand Identity Package" with skills [Adobe Photoshop, Adobe Illustrator, Figma]
- Project description: "Complete brand identity design for a local cafe"

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string (neutral, brief — no strong fit claims since skills are irrelevant)
- `why_role_company`: string (conservative, role-focused only)
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference (should contain placeholder since no backend evidence matches)
- `contribution_fit`: string (minimal — no specific backend contribution claims)
- `closing`: string
- `review_notes`: list of strings
- `missing_evidence`: list of strings (ALL backend skills must appear here)
- `disclaimer`: string

## Expected Behavior

### Must Include
- `relevant_evidence` must contain a placeholder item since no CV/JD skill overlap exists
- `missing_evidence` must list: Python, FastAPI/Django, PostgreSQL, Docker, RESTful APIs
- `why_role_company` should be brief and role-focused, not claim strong fit
- `contribution_fit` should be minimal, acknowledging skill gaps
- Neutral, non-committal tone — no false enthusiasm about backend role

### Must NOT Include
- NO fabricated backend skills (e.g., don't claim FastAPI, Django, PostgreSQL, Docker, Python experience)
- NO claims that design skills translate to backend development
- NO strong fit language ("strong match", "ideal candidate")
- NO fabricated metrics about backend performance
- NO fabrications about Python, API development, or database experience

## Guardrail Validation
- All skills referenced in the cover letter must be present in CV (design tools only)
- `missing_evidence` must include all JD-required skills not in CV
- No fabrications about skills, metrics, or experience not in CV or profile
- `disclaimer` field must be non-empty
