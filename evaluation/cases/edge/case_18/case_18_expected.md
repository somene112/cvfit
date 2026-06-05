# Expected Behavior — Edge Case 18: CV Not Relevant to JD

## CV Summary
This CV lists every technology possible but provides no specific evidence. The language is vague ("built things", "various stuff", "can do everything"). The candidate claims universal expertise but provides no concrete details. Despite listing Python, FastAPI, PostgreSQL, and Docker, there is no evidence these are real or specific.

## Expected Fit Score Range
- Expected: 50–65 (partial)
- fit_level: `partial` or `weak`

## Expected Matched Skills
- Python (text match)
- FastAPI (text match)
- PostgreSQL (text match)
- Docker (text match)
- SQL (text match)

## Expected Missing Skills
- While the CV lists these skills, the LACK OF EVIDENCE means the system may score them lower or mark them as having weak evidence
- "I know Python" is not the same as demonstrated Python backend experience

## Expected Evidence
- Evidence may be weak or vague
- System must NOT fabricate strong evidence from vague claims

## Expected Guardrails
- No guarantee language
- Despite listing many skills, the CV lacks concrete evidence
- System must be careful not to score too highly based on keyword listing alone
- The self-description "I can do any job" must NOT generate a high confidence score

## Score Components
- skill_match: low to moderate (skills listed but no evidence)
- responsibility_match: low (vague "built things" descriptions)
- cv_quality: low to moderate (long but vague)
- confidence: should be LOW due to lack of concrete evidence

## Special Expectations
- This case tests whether the system can distinguish between "listing a skill" and "having real evidence of a skill"
- A candidate who claims "I know everything" should NOT score the same as someone with concrete evidence
- The fit_level should reflect weak evidence, even if the keyword list is comprehensive
