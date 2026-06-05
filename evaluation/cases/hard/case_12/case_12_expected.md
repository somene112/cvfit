# Expected Behavior — Hard Case 12

## CV Summary
CV is vague with generic language and no specific Python/FastAPI/Flask details. Skills listed (Java, C++, Node.js, Spring Boot, React) are from different tech stacks. Only Docker and AWS have overlap. The CV shows breadth but not the depth required.

## Expected Fit Score Range
- Expected: 40–55 (partial)
- fit_level: `weak`

## Expected Matched Skills
- Docker (nice_to_have) — should be matched
- AWS (partial) — partial match

## Expected Missing Skills
- Python (core must_have) — not mentioned
- FastAPI or Flask (core must_have) — not mentioned
- PostgreSQL (must_have) — not mentioned
- Redis (nice_to_have) — not mentioned
- REST APIs (core responsibility) — generic, not specific

## Expected Evidence
- Evidence for Docker
- No evidence for Python, FastAPI, PostgreSQL, Redis

## Expected Guardrails
- No guarantee language
- Breadth of skills must NOT be conflated with backend depth
- Do NOT infer Python from "many programming languages"
- Missing skill wording: "not found in parsed CV"

## Score Components
- skill_match: very low
- responsibility_match: low
- cv_quality: low (vague descriptions, no metrics)
