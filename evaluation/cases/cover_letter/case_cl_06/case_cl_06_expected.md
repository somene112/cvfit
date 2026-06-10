# Cover Letter Case 06: Weak Evidence — No Fabricated Claims

## CV Profile
- **Name:** Nguyen Thi F
- **Email:** nguyenthif@email.com
- **Skills:** JavaScript, React
- **Projects:** Frontend-focused work only

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL
- **Experience Level:** Mid-level
- **Focus Areas:** Backend development, API design, database management

## Profile Items
- Skill: "JavaScript" only (no Python, FastAPI, or PostgreSQL)

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
- Cover letter must be very conservative in tone
- `missing_evidence` must list: Python, FastAPI, PostgreSQL
- `contribution_fit` should be minimal or based only on general software skills
- `relevant_evidence` should be minimal or indicate transition interest
- `review_notes` should warn about significant skill gaps
- `disclaimer` must be present

### Must NOT Include
- NO claim that user knows Python (JavaScript is the only skill in CV)
- NO claim that user knows FastAPI
- NO claim that user knows PostgreSQL
- NO fabricated backend experience
- NO fabricated metrics or claims
- NO misleading statements about qualifications

## Guardrail Validation
- Skills NOT in CV must NOT be referenced as known
- All missing skills from JD must appear in `missing_evidence`
- `contribution_fit` must not overstate qualifications
- `disclaimer` field must be non-empty
