# Expected Behavior — Profile Evidence Case 10: Achievement with Fabricated Revenue Claim

## CV Profile
Python developer with FastAPI and Flask experience.

## JD Profile
Requires Python, FastAPI for backend developer role.

## Profile Evidence Expected Behavior

### Vague Achievement Analysis
The profile achievement has problematic characteristics:

| Issue | Details |
|-------|---------|
| Vague description | "Made the company successful" |
| Unverifiable metric | "Increased revenue by 300%" |
| No context | No project, team, or technical details |
| Low confidence | Description lacks specificity |

### has_profile_evidence Expected Values
- `has_profile_evidence.fastapi`: **false** (not in profile)
- `has_profile_evidence.python`: **false** (not in profile)
- `has_profile_evidence.business`: **true** (in skills_json)
- `has_profile_evidence.problem_solving`: **true** (in skills_json)

### Hallucination Risk Flag
This case should trigger hallucination risk warnings:

1. **Revenue claim**: "300% increase" is unverifiable
2. **Vague attribution**: "Made the company successful"
3. **No technical context**: No mention of how revenue was increased

### Cover Letter Behavior — Critical Anti-Fabrication Rules

**SHOULD NOT:**
- ❌ Reference the "300% revenue increase" in cover letter
- ❌ Claim credit for business revenue impact
- ❌ Fabricate context around this achievement
- ❌ Use this as evidence for technical skills

**SHOULD:**
- ✅ Ignore or treat as weak evidence
- ✅ Flag as potential hallucination risk
- ✅ Not include in cover letter claims
- ✅ Use actual technical evidence instead

### Guardrail Checks — Revenue Claims
- System should NOT use unverifiable revenue metrics
- Revenue claims require external verification
- Vague achievements should be flagged, not used
- System should prefer concrete technical achievements

### Expected System Behavior
- `review_notes` should include warning about vague achievement
- `review_notes` should flag potential hallucination risk
- Cover letter should not reference revenue claims
- System should not fabricate business impact
