# Cover Letter Case 03: Good Evidence — Multiple Projects Referenced

## CV Profile
- **Name:** Le Van C
- **Email:** levanc@email.com
- **Skills:** Python, FastAPI, Docker, Kubernetes, AWS
- **Projects:**
  - **Product API**
    - Description: E-commerce product management API
  - **Auth Service**
    - Description: AWS-based authentication service

## JD Profile
- **Required Skills:** Python, FastAPI, Docker
- **Experience Level:** Senior backend engineer
- **Focus Areas:** Microservices, API development, containerization

## Profile Items
- Project: "Product API" with skills [FastAPI, PostgreSQL]
- Project: "Auth Service" with skills [Python, AWS]

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
- References to multiple projects (Product API and Auth Service)
- `relevant_evidence` must have evidence items from both profile projects
- `cv_reference` should reference both projects
- `contribution_fit` should mention FastAPI and Docker experience
- `review_notes` should confirm multiple strong evidence matches
- `disclaimer` must be present

### Must NOT Include
- NO fabricated company names
- NO fabricated metrics not in CV
- NO fabricated skills not in CV (e.g., don't claim Redis if not in CV)

## Guardrail Validation
- All skills referenced must be present in CV
- `relevant_evidence` should include items from multiple projects
- `disclaimer` field must be non-empty
- `review_notes` field must be non-empty
