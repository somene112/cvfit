# Expected Behavior — Medium Case 07

## CV Summary
Partial match: Python and SQL mentioned, but in data analysis context, not API/backend service context. Missing FastAPI, PostgreSQL (SQL is generic), Redis, Docker. Skills are present but in wrong context.

## Expected Fit Score Range
- Expected: 48–60 (partial)
- fit_level: `partial`

## Expected Matched Skills
- Python (must_have) — matched text-wise, but context may affect score
- SQL (may match PostgreSQL group) — partial

## Expected Missing Skills
- FastAPI — not mentioned
- PostgreSQL (JD wants PostgreSQL specifically) — may be marked missing
- Redis — not mentioned
- Docker — not mentioned

## Expected Evidence
- Evidence for Python
- Evidence for SQL (may or may not count as PostgreSQL)

## Expected Guardrails
- No guarantee language
- Missing skill: "FastAPI evidence was not found in the parsed CV"
- Do NOT fabricate: "the system did not find FastAPI evidence" is fine; "candidate doesn't know FastAPI" is not

## Score Components
- skill_match: low to moderate
- responsibility_match: low (scripts, not services)
- cv_quality: moderate (clear but limited scope)
