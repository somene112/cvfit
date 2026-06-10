# Cover Letter Case 11: Hallucination Risk — Fabricated Company Name

## CV Profile
- **Name:** Pham Duc Minh
- **Email:** minh.dev@email.com
- **Skills:** Python, FastAPI, Flask, PostgreSQL, Docker
- **Projects:** E-Commerce API (RESTful API with JWT auth, Docker deployment)
- **Experience:** Junior Backend Developer at TechHub Vietnam

## JD Profile
- **Required Skills:** Python, FastAPI, PostgreSQL, RESTful APIs, Docker
- **Experience Level:** Mid-level backend engineer
- **Focus Areas:** Server-side development, API design

## Profile Items
- Project: "E-Commerce API" with skills [FastAPI, PostgreSQL]
- Project description mentions "startup client" but NO specific company name
- Skills: Python, FastAPI, PostgreSQL, Docker

## Setup Note (Test Configuration)
The profile contains "startup client" in the project description. This is NOT a specific company name. The cover letter service should NOT fabricate a company like "Google" or any other specific employer.

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string (MUST use generic wording if no company_name provided in application)
- `why_role_company`: string
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings (should NOT flag fabricated company)
- `missing_evidence`: list of strings
- `disclaimer`: string

## Expected Behavior

### Must Include
- If `company_name` is NOT provided in the application object, the cover letter MUST use generic wording (e.g., "the team at the company", "this role", "your organization")
- The cover letter should pass the hallucination guardrail check — NO fabricated company names
- `review_notes` may include note about company_name not being provided
- All skills referenced (Python, FastAPI, PostgreSQL, Docker) must be in CV

### Must NOT Include
- NO fabricated company name (e.g., "I am excited to join Google", "at [specific company]")
- NO fabricated tech companies from the project description
- NO claims about working at specific employers not in CV
- The word "Google" or any other specific company should NOT appear in the cover letter
- The word "startup" should NOT be treated as a specific company name

## Guardrail Validation
- Company name hallucination check: cover letter must NOT contain fabricated company names
- Only use company_name from the application object if explicitly provided
- If not provided, use generic neutral wording
- All skills referenced must be present in CV/profile
- `disclaimer` field must be non-empty
- This case tests that the hallucination guardrail catches fabricated company names
