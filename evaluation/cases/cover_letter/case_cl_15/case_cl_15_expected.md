# Cover Letter Case 15: Structure Check — Review Notes Present

## CV Profile
- **Name:** Vo Van Nam
- **Email:** nam.dev@email.com
- **Skills:** Python, FastAPI, PostgreSQL, Docker
- **Projects:** API Service (FastAPI, PostgreSQL, JWT authentication)
- **Experience:** Junior Backend Developer at TechCo Vietnam

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL, Redis, RESTful APIs, Docker
- **Experience Level:** Mid-level backend developer
- **Focus Areas:** Caching, real-time data processing

## Profile Items
- Project: "API Service" with skills [FastAPI, PostgreSQL]
- Skills: Python, FastAPI
- **NOTE:** Redis is NOT in the profile, only in the CV and JD

## Setup Note (Test Configuration)
The JD requires Redis, and the CV mentions PostgreSQL but not Redis in a Redis-specific context. The profile has NO Redis skill. This case tests that `review_notes` is properly populated to warn about skills not backed by profile evidence.

## Expected Output Format
The cover letter service must produce JSON with ALL required sections:
- `opening`: string
- `why_role_company`: string
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings (MUST be non-empty and contain warnings about profile evidence gaps)
- `missing_evidence`: list of strings (Redis should appear here)
- `disclaimer`: string

## Expected Behavior

### Must Include
- `review_notes` MUST be non-empty and include warnings about:
  - Skills (like Redis) that are matched from JD but NOT backed by profile
  - Or a note that no matched skills were found from profile analysis
- `missing_evidence` should include Redis (required by JD but not in profile)
- `relevant_evidence` should include evidence from the API Service project
- `disclaimer` must be present

### Must NOT Include
- NO empty `review_notes` list
- NO fabricated Redis experience
- NO fabricated caching experience
- All claims must be backed by CV or profile content

## Guardrail Validation
- Structure completeness check: ALL 8 sections must be present
- `review_notes` field must be a non-empty list
- `review_notes` should contain meaningful content about evidence verification
- `missing_evidence` should include Redis
- All skills referenced must be present in CV
- `disclaimer` field must be non-empty
- This case tests that `review_notes` is properly populated with verification warnings
