# Cover Letter Case 13: Hallucination Risk — Fabricated Skill

## CV Profile
- **Name:** Hoang Van Duc
- **Email:** duc.python@email.com
- **Skills:** Python, Flask, SQLite, Git, basic Linux
- **Projects:** Personal Blog (Flask, SQLite)
- **Experience:** Junior Python Developer at Local Tech Company

## JD Profile
- **Required Skills:** Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL
- **Experience Level:** Senior backend engineer
- **Focus Areas:** Cloud-native microservices, Kubernetes orchestration, AWS

## Profile Items
- Project: "Personal Blog" with skills [Flask, SQLite]
- Skills: Python only
- NO FastAPI, NO Docker, NO Kubernetes, NO AWS, NO PostgreSQL

## Setup Note (Test Configuration)
The CV has NO FastAPI, NO Docker, NO Kubernetes, NO AWS experience. The profile only lists "Python" as a skill. This case tests that the hallucination guardrail catches fabricated skills.

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string
- `why_role_company`: string (should mention Python but NOT fabricate FastAPI)
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings (should flag skills not backed by profile)
- `missing_evidence`: list of strings (FastAPI, Docker, Kubernetes, AWS, PostgreSQL MUST appear here)
- `disclaimer`: string

## Expected Behavior

### Must Include
- `missing_evidence` must include: FastAPI, Docker, Kubernetes, AWS, PostgreSQL
- Only mention Python and Flask (the actual skills from CV)
- `review_notes` should flag skills sourced from CV analysis without profile backing
- The cover letter should acknowledge skill gaps where appropriate

### Must NOT Include
- NO fabricated FastAPI experience (only Flask is in CV)
- NO fabricated Docker experience
- NO fabricated Kubernetes experience
- NO fabricated AWS experience
- NO fabricated PostgreSQL experience
- NO claims about containerization, cloud deployment, or microservices

## Guardrail Validation
- Skill hallucination check: cover letter must NOT contain fabricated technical skills
- All skills referenced must be present in CV
- JD-required skills NOT in CV MUST appear in `missing_evidence`
- This case tests that the hallucination guardrail catches fabricated skills (FastAPI, Docker, Kubernetes, AWS)
- `disclaimer` field must be non-empty
