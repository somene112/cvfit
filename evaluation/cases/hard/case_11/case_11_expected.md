# Expected Behavior — Hard Case 11

## CV Summary
Extremely vague CV: no specific technologies, no projects, no experience details. Very short text. This is a hard case to evaluate — the system should recognize the lack of evidence and score appropriately.

## Expected Fit Score Range
- Expected: 25–40 (weak)
- fit_level: `weak`

## Expected Matched Skills
- None or very few; generic "programming" does not match specific tech stack

## Expected Missing Skills
- Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS — all missing

## Expected Evidence
- Minimal or no evidence
- Any evidence should reference the parsed CV text

## Expected Guardrails
- No guarantee language
- System must not fabricate skills
- Must report missing skills with "not found in parsed CV" wording
- Limitation notice about parser quality should be included

## Score Components
- skill_match: very low
- responsibility_match: very low
- cv_quality: very low (too short, vague)

## Special Expectations
- fit_level MUST be `weak` — a vague CV cannot score `good` or `excellent`
- `confidence` in result should reflect low parser confidence
