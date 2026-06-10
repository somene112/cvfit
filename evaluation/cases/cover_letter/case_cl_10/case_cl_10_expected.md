# Cover Letter Case 10: Irrelevant CV/JD — No Fabrication

## CV Profile
- **Name:** Le Thi Hang
- **Email:** hang.teacher@email.com
- **Skills:** Microsoft PowerPoint, Microsoft Excel, English (Fluent), Vietnamese (Native), Lesson Planning, Presentation
- **Experience:** English Teacher at Da Nang International School
- **Education:** BA in English Literature

## JD Profile
- **Required Skills:** Python, TensorFlow, PyTorch, SQL, Machine Learning, AWS/GCP
- **Experience Level:** Mid-level data scientist
- **Focus Areas:** ML model development, deep learning, data analysis

## Profile Items
- Experience: "English Teacher" with description about PowerPoint, Excel
- Education: "Bachelor of Arts in English Literature"
- No tech skills, no data science background

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string (conservative, neutral tone)
- `why_role_company`: string (role-focused, no fabricated tech skills)
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference (placeholder only — no overlap)
- `contribution_fit`: string (minimal, acknowledges gap)
- `closing`: string
- `review_notes`: list of strings (should flag no matched skills)
- `missing_evidence`: list of strings (all DS skills: Python, TensorFlow, PyTorch, SQL, ML)
- `disclaimer`: string

## Expected Behavior

### Must Include
- `relevant_evidence` must contain a placeholder item (no tech/data skills overlap)
- `missing_evidence` must list: Python, TensorFlow, PyTorch, SQL, machine learning experience, cloud ML platforms
- `why_role_company` should be very conservative — no claims about data science capability
- If any soft skill from CV is mentioned, it must be genuine (e.g., communication, presentation, lesson planning)
- `review_notes` should flag "No matched skills found"

### Must NOT Include
- NO fabricated data science skills (Python, TensorFlow, PyTorch, SQL, machine learning)
- NO fabricated DS experience or projects
- NO claims that teaching experience equates to data science capability
- NO fabricated metrics about data analysis or model performance
- NO fabrications about SQL, ML, or cloud platforms
- The cover letter must NOT look like it was written for a data scientist

## Guardrail Validation
- All skills referenced must be present in CV (only: PowerPoint, Excel, English fluency, teaching-related skills)
- No fabrications of technical/data science skills
- `missing_evidence` must be comprehensive (all JD skills not in CV)
- `disclaimer` field must be non-empty
- Conservative wording throughout — no over-promising
