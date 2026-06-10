# Cover Letter Case 05: Weak Evidence — Conservative Wording Required

## CV Profile
- **Name:** Hoang Van E
- **Email:** hoangvane@email.com
- **Skills:** Python, Flask
- **Projects:**
  - **Web App**
    - Description: "Web App" with no specific details or metrics

## JD Profile
- **Required Skills:** Python, Flask, PostgreSQL, Redis, Docker
- **Experience Level:** Mid-level
- **Focus Areas:** Backend development, API design, containerization

## Profile Items
- No profile items provided

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string
- `why_role_company`: string
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings
- `missing_evidence`: list of strings
- `disclaimer`: string

## Expected Behavior

### Must Include
- `opening` must be neutral/conservative (not overly enthusiastic)
- `relevant_evidence` should contain placeholder evidence about adding more details
- `review_notes` should warn that no strong evidence found for required skills
- `missing_evidence` should list: PostgreSQL, Redis, Docker (skills required by JD but not in CV)
- `contribution_fit` should be minimal/future-focused
- `disclaimer` must be present

### Must NOT Include
- NO fabricated company names
- NO claims about PostgreSQL, Redis, or Docker skills (these are NOT in CV)
- NO fabricated metrics or project details
- NO fabricated skills

## Guardrail Validation
- Skills NOT in CV must NOT be referenced in cover letter content
- All missing skills from JD must appear in `missing_evidence`
- `review_notes` must indicate weak evidence
- `disclaimer` field must be non-empty
