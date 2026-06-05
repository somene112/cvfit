# Expected Behavior — Easy Case 02

## CV Summary
Good match: CV mentions Python, Flask, SQLite — core requirements. SQL keyword in SQLite should match the generic SQL requirement.

## Expected Fit Score Range
- Expected: 50–65 (partial fit)
- fit_level: `partial`

## Expected Matched Skills
- Python (must_have) — should be matched
- Flask (must_have) — should be matched (direct mention)
- SQLite (must_have / SQL variant) — should be matched

## Expected Missing Skills
- PostgreSQL (not mentioned) — may appear as missing

## Expected Evidence
- Evidence snippet referencing Flask
- Evidence snippet referencing Python

## Expected Guardrails
- No guarantee language
- Missing skill phrasing: "not found in parsed CV"

## Score Components
- skill_match: moderate to high
- responsibility_match: moderate alignment
- cv_quality: moderate (has action verbs, metrics missing)
