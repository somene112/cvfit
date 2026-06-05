# Expected Behavior — Hard Case 15

## CV Summary
Significant role mismatch: Candidate is in cybersecurity. Python is present but in security scripting context, not backend API development. OAuth2 and JWT show API concept awareness but not backend service development. No FastAPI, PostgreSQL, Redis, Docker in backend context.

## Expected Fit Score Range
- Expected: 40–52 (partial)
- fit_level: `weak` or `partial`

## Expected Matched Skills
- Python (must_have) — matched text-wise
- JWT (REST API concepts) — partial match for API awareness

## Expected Missing Skills
- FastAPI — not mentioned
- PostgreSQL — not mentioned (security focus, not DB admin)
- Redis — not mentioned
- Docker — not mentioned in deployment context
- REST API development — OAuth2/JWT show API awareness but not FastAPI development

## Expected Evidence
- Evidence for Python (security scripts)
- Evidence for JWT (authentication context)

## Expected Guardrails
- No guarantee language
- Security tools (Metasploit, Burp Suite, Nmap) are NOT backend skills — must not inflate score
- Missing skill wording: "not found in parsed CV"
- System must differentiate "knows Python" from "uses Python for backend API development"

## Score Components
- skill_match: low to moderate
- responsibility_match: low
- cv_quality: moderate to good (clear CV structure)

## Special Expectations
- A strong CV in cybersecurity should NOT score highly for a backend engineer role
- Domain knowledge overlap is partial but not sufficient
