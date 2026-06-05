# Expected Behavior — Medium Case 06

## CV Summary
Partial mismatch: CV mentions Node.js, MongoDB, Express — not Python. Only Docker aligns. This is a technology stack mismatch but the candidate has relevant API development skills.

## Expected Fit Score Range
- Expected: 50–65 (partial)
- fit_level: `partial`

## Expected Matched Skills
- Docker (nice_to_have) — matched
- REST API concepts (indirect) — partial

## Expected Missing Skills
- Python (core must_have) — not mentioned
- FastAPI/Flask (core must_have) — not mentioned
- PostgreSQL (must_have) — MongoDB is not the same

## Expected Evidence
- Evidence for Docker
- No evidence for Python, FastAPI, PostgreSQL

## Expected Guardrails
- No guarantee language
- Missing skill wording: "not found in parsed CV"
- Do NOT say "candidate does not know Python" — say "Python evidence was not found"

## Score Components
- skill_match: low to moderate
- responsibility_match: moderate (has API dev experience)
- cv_quality: moderate (clear structure)
