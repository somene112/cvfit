# Expected Behavior — Edge Case 17: Ultra-Long JD

## CV Summary
This is the opposite extreme from Case 16. The JD is very brief (just 8 requirements). The CV is extremely long and lists every possible technology (100+ skills) across many domains. The system must correctly match the few JD requirements without being overwhelmed by irrelevant skills.

## Expected Fit Score Range
- Expected: 60–72 (good)
- fit_level: `partial`

## Expected Matched Skills
- Python (must_have) — matched
- FastAPI (must_have) — matched
- PostgreSQL (must_have) — matched
- Redis (nice_to_have) — matched
- Docker (nice_to_have) — matched
- REST APIs — matched (implicit)

## Expected Missing Skills
- None from the JD requirements

## Expected Evidence
- Multiple high-quality evidence snippets for key skills

## Expected Guardrails
- No guarantee language even at excellent score
- Irrelevant skills (ML, blockchain, etc.) must NOT inflate score
- System should correctly filter and score only JD-relevant skills

## Score Components
- skill_match: very high
- responsibility_match: high
- experience_level: high
- cv_quality: very good

## Special Expectations
- The overqualification and irrelevant skills should NOT break the scoring
- System should handle skill list explosion gracefully
- fit_level should be `excellent` for a very strong match
