# Cover Letter Case 01: Good Evidence — Matched Skills with Strong Project Detail

## CV Profile
- **Name:** Nguyen Van A
- **Email:** nguyenvana@email.com
- **Skills:** Python, FastAPI, PostgreSQL, Redis, Docker
- **Projects:**
  - **E-Commerce Product API**
    - Description: Built API with 500+ endpoints for product management
    - Details: PostgreSQL indexing for product search, Redis caching for session management, Docker with health checks for production deployment

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL, Redis, Docker
- **Experience Level:** Mid-level backend engineer
- **Focus Areas:** API development, database optimization, caching

## Profile Items (from application)
- Project: "E-Commerce API" with skills [FastAPI, PostgreSQL, Redis]
- Project description: "Built API with 500+ endpoints"

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
- References to FastAPI, PostgreSQL, Redis, Docker in the cover letter content
- `relevant_evidence` list must include evidence items from the profile/project
- `cv_reference` should point to "E-Commerce Product API" project
- `contribution_fit` should mention the 500+ endpoints experience and optimization skills
- `review_notes` should confirm strong evidence match
- `disclaimer` must be present

### Must NOT Include
- NO fabricated company names (only generic terms like "the team at the company" if company_name is not provided)
- NO fabricated metrics not in CV (e.g., don't claim "99.9% uptime" if not in CV)
- NO fabricated skills not in CV (e.g., don't claim Kubernetes if not in CV)
- NO claims about specific performance gains not documented in CV

## Guardrail Validation
- All skills referenced must be present in CV
- All metrics/claims must have source in CV
- `disclaimer` field must be non-empty
- `review_notes` field must be non-empty
- If skills from JD are missing from CV, they must appear in `missing_evidence`
