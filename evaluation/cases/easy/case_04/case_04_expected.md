# Expected Behavior — Easy Case 04

## CV Summary
Moderate-to-good match: Python and SQLite match core requirements. Django is similar to FastAPI (Python web framework). No explicit FastAPI mention but Django should be recognized as a Python web framework. REST API mentioned implicitly via CRUD.

## Expected Fit Score Range
- Expected: 50–65 (partial to good)
- fit_level: `partial`

## Expected Matched Skills
- Python (must_have) — matched
- SQLite (must_have / SQL variant) — matched
- Django (similar to FastAPI) — should be matched by ontology aliasing

## Expected Missing Skills
- FastAPI (not explicitly mentioned) — may appear as missing, but Django is a valid Python web framework alternative
- REST API details — partial match

## Expected Evidence
- Evidence for Python
- Evidence for SQLite/Django

## Expected Guardrails
- No guarantee language
- If FastAPI is reported as missing, wording must say "not found in parsed CV", not "you don't know FastAPI"

## Score Components
- skill_match: moderate
- responsibility_match: moderate
- cv_quality: moderate (limited project scope)
