# Cover Letter Case 16: Disclaimer Check — Present and Correct

## CV Profile
- **Name:** Pham Thi Mai
- **Email:** mai.web@email.com
- **Skills:** Python, Flask, SQLite, MySQL, HTML, CSS, JavaScript, Git
- **Projects:** Personal Portfolio Website (Flask, Jinja2)
- **Experience:** Junior Web Developer at WebDesign Corp

## JD Profile
- **Required Skills:** Python, Flask, SQL, HTML/CSS/JS, Git
- **Experience Level:** Entry-level web developer

## Profile Items
- Profile is EMPTY (no projects, no skills, no experience entries)

## Setup Note (Test Configuration)
The profile.json is empty — no projects, no skills, no experience entries. The cover letter service should still generate output but rely on CV analysis. The disclaimer is critical in this case because the draft is generated with minimal profile backing.

## Expected Output Format
The cover letter service must produce JSON with ALL required sections:
- `opening`: string
- `why_role_company`: string
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings
- `missing_evidence`: list of strings
- `disclaimer`: string (MUST be non-empty and contain required language)

## Expected Behavior

### Must Include
- `disclaimer` MUST be non-empty
- `disclaimer` MUST contain at least one of these phrases:
  - "must be reviewed" (or "must be reviewed and edited")
  - "does not guarantee"
  - "before submission"
- The cover letter should still produce all sections even with an empty profile
- `review_notes` should flag lack of profile evidence
- Skills should come from CV analysis when profile is empty

### Must NOT Include
- NO empty `disclaimer` field
- `disclaimer` must NOT be just whitespace
- The disclaimer must be a meaningful warning, not just an empty string

## Required Disclaimer Language
The disclaimer must contain one of these exact phrases (case-insensitive):
- "must be reviewed" (e.g., "must be reviewed and edited before submission")
- "does not guarantee" (e.g., "does not guarantee any hiring outcome")
- "before submission" (e.g., "review before submission")

## Guardrail Validation
- Disclaimer presence check: `disclaimer` field must be non-empty
- Disclaimer content check: must contain "must be reviewed" OR "does not guarantee" OR "before submission"
- This case tests the disclaimer guardrail is working correctly
- ALL 8 sections must be present
- `disclaimer` is the KEY field being tested in this case
