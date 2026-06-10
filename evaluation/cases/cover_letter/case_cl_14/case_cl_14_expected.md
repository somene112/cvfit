# Cover Letter Case 14: Structure Check — Opening Present

## CV Profile
- **Name:** Nguyen Thi Lan
- **Email:** lan.dev@email.com
- **Skills:** Python, Django, PostgreSQL, Docker, REST APIs
- **Projects:** Blog Platform (Django, PostgreSQL, Docker), Task Tracker (Django REST Framework)
- **Experience:** Backend Developer at WebTech Vietnam

## JD Profile
- **Required Skills:** Python, Django, PostgreSQL, RESTful APIs, Docker
- **Experience Level:** Mid-level backend developer

## Profile Items
- Project: "Blog Platform" with skills [Django, PostgreSQL, Docker]
- Skills: Python, Django, PostgreSQL, Docker
- Strong alignment between CV, profile, and JD

## Expected Output Format
The cover letter service must produce JSON with ALL required sections:
- `opening`: string (MUST be non-empty — this is the key test)
- `why_role_company`: string (MUST be non-empty)
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference (MUST be non-empty)
- `contribution_fit`: string (MUST be non-empty)
- `closing`: string (MUST be non-empty)
- `review_notes`: list of strings (MUST be non-empty)
- `missing_evidence`: list of strings (can be empty since skills match)
- `disclaimer`: string (MUST be non-empty)

## Expected Behavior

### Must Include
- `opening` section MUST be non-empty and contain a proper introduction
- ALL 8 sections must be present in the output
- `relevant_evidence` should include evidence from the Blog Platform project
- `review_notes` should note skills backed by profile evidence
- All sections must have appropriate content (not just empty strings or empty lists)

### Must NOT Include
- NO empty `opening` string
- NO missing sections
- NO sections with only whitespace
- All sections must contain meaningful content

## Guardrail Validation
- Structure completeness check: ALL 8 sections must be present
- `opening` field must be non-empty
- `why_role_company` field must be non-empty
- `relevant_evidence` field must be a non-empty list
- `contribution_fit` field must be non-empty
- `closing` field must be non-empty
- `review_notes` field must be a non-empty list
- `missing_evidence` field must be present (can be empty list)
- `disclaimer` field must be non-empty
- This case tests that the structure is complete and all required sections are present
