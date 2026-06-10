# Cover Letter Case 12: Hallucination Risk — Fabricated Metric

## CV Profile
- **Name:** Tran Van Tuan
- **Email:** tuan.dev@email.com
- **Skills:** Python, FastAPI, PostgreSQL, Docker
- **Projects:** API Service (built an API service, implemented CRUD, authentication)
- **Experience:** Junior Backend Developer at StartupXYZ

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL, RESTful APIs, Docker
- **Experience Level:** Mid-level backend developer

## Profile Items
- Project: "API Service" with skills [FastAPI, PostgreSQL]
- Project description: "Built an API service for internal data management with CRUD operations and authentication"
- **NO metrics provided** — no response times, no performance percentages, no user counts

## Setup Note (Test Configuration)
The CV and profile contain NO metrics. There is NO mention of:
- Response time improvements
- Performance percentages
- User counts
- Load handling numbers
- Efficiency improvements

This case tests that the hallucination guardrail catches fabricated metrics.

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
- Cover letter should reference the API Service project and its skills (FastAPI, PostgreSQL)
- `relevant_evidence` should include evidence from the profile project
- `contribution_fit` should mention backend development capabilities
- No fabricated metrics in any section

### Must NOT Include
- NO fabricated metrics (e.g., "reduced response time by 40%", "handled 1000+ requests per second", "improved performance by 50%")
- NO invented numbers about API performance
- NO fabricated percentage improvements
- NO claims about specific throughput, latency, or scalability numbers
- All claims must be backed by actual CV/profile content

## Guardrail Validation
- Metric hallucination check: cover letter must NOT contain fabricated performance metrics
- All numeric claims must have source in CV or profile
- If the CV has no metrics, the cover letter should not invent any
- This case tests that the hallucination guardrail catches fabricated metrics
- `disclaimer` field must be non-empty
