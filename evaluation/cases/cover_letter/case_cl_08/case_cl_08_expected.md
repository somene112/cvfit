# Cover Letter Case 08: Missing Skill — Conditional Suggestion Wording

## CV Profile
- **Name:** Bui Thi H
- **Email:** buithih@email.com
- **Skills:** Python, Flask, SQLite
- **Missing Skills:** FastAPI (required by JD)

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL
- **Experience Level:** Mid-level
- **Focus Areas:** Backend development, API development, database management

## Profile Items
- Skill: "Python" with no project

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
- Cover letter must NOT claim FastAPI experience
- `missing_evidence` must contain: "FastAPI: required by JD but not found"
- `contribution_fit` should be conditional/future-focused about learning
- `relevant_evidence` should reference Python and Flask experience
- `review_notes` should note the FastAPI skill gap
- `disclaimer` must be present

### Must NOT Include
- NO claims about FastAPI skills
- NO fabricated FastAPI experience
- NO misleading statements about qualifications
- NO claims about PostgreSQL (not in CV either)

## Guardrail Validation
- Skills NOT in CV must NOT be referenced as known
- FastAPI must appear in `missing_evidence` with explanation
- `contribution_fit` must indicate learning orientation
- `disclaimer` field must be non-empty
