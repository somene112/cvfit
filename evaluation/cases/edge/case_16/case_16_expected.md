# Expected Behavior — Edge Case 16: Ultra-Short CV

## CV Summary
Extremely minimal CV — only 2 sentences. This tests the system's behavior with minimal parsed content.

## Expected Fit Score Range
- Expected: 30–42 (weak to partial)
- fit_level: `weak`

## Expected Matched Skills
- None or very few; text is too short for reliable matching

## Expected Missing Skills
- Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, AWS — all missing

## Expected Evidence
- Minimal evidence due to lack of content

## Expected Guardrails
- No guarantee language
- Missing skill wording: "not found in parsed CV"
- Limitation notice: parser confidence should be LOW
- System must NOT fabricate evidence from 2 sentences

## Score Components
- skill_match: very low
- responsibility_match: very low
- cv_quality: very low (text too short)

## Special Expectations
- fit_level MUST be `weak`
- Confidence score should reflect thin CV
- System should output limitation warnings about low text content
