# Expected Behavior — Hard Case 13

## CV Summary
The CV is overqualified — it lists an extremely broad set of skills including many technologies beyond what the JD requires (Kafka, Elasticsearch, GCP, Terraform, GraphQL, gRPC, Go). This creates a challenge: the system must correctly identify relevant matches without being confused by irrelevant breadth.

## Expected Fit Score Range
- Expected: 60–75 (good)
- fit_level: `partial`

## Expected Matched Skills
- Python (must_have) — matched
- FastAPI (must_have) — matched
- Flask (similar to FastAPI) — matched
- PostgreSQL (must_have) — matched
- Redis (nice_to_have) — matched
- Docker (nice_to_have) — matched

## Expected Missing Skills
- Very few; the CV covers all major requirements

## Expected Evidence
- Multiple evidence snippets for Python, FastAPI, PostgreSQL
- Evidence quality should be good

## Expected Guardrails
- No guarantee language even for high scores
- The overqualification should NOT inflate the score beyond the fit level
- System must not be confused by irrelevant skills (Kafka, GCP, etc.) — they simply aren't scored

## Score Components
- skill_match: high
- responsibility_match: high
- cv_quality: good to very good

## Special Expectations
- fit_level should NOT be `excellent` if experience level is misaligned (JD wants 2-3 years, CV shows 7+ years at BigTech)
- The system should handle overqualification gracefully — score high but acknowledge possible mismatch
