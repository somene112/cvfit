# Cover Letter Case 07: Missing Skill — Not Mentioned in Cover Letter

## CV Profile
- **Name:** Dao Van G
- **Email:** daovang@email.com
- **Skills:** Python, Django, PostgreSQL
- **Missing Skills:** FastAPI, Redis, Docker

## JD Profile
- **Required Skills:** Python, Django, FastAPI, Redis, Docker
- **Experience Level:** Mid-level
- **Focus Areas:** Backend development, microservices, containerization

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
- Cover letter must NOT mention FastAPI, Redis, or Docker (these are NOT in CV)
- `contribution_fit` must be based only on Django and PostgreSQL
- `relevant_evidence` should reference Django/PostgreSQL experience
- `missing_evidence` must include: FastAPI, Redis, Docker
- `review_notes` should indicate missing skills
- `disclaimer` must be present

### Must NOT Include
- NO references to FastAPI in cover letter content
- NO references to Redis in cover letter content
- NO references to Docker in cover letter content
- NO fabricated claims about these skills
- NO misleading statements about qualifications

## Guardrail Validation
- Skills NOT in CV must NOT appear in cover letter content
- Skills from JD that are NOT in CV must appear in `missing_evidence`
- `contribution_fit` must only reference skills from CV
- `disclaimer` field must be non-empty
