# Expected Behavior — Profile Evidence Case 14: Conflicting Evidence CV vs Profile

## CV Profile
Python developer claims Flask experience. No FastAPI mentioned in CV.

## JD Profile
Requires Python and FastAPI (not Flask).

## Profile Evidence Expected Behavior

### Conflicting Evidence Analysis
CV has Flask, Profile has Flask, but JD requires FastAPI:

| Source | Has Flask | Has FastAPI | Expected |
|--------|-----------|-------------|----------|
| CV | ✅ Yes | ❌ No | Flask matched |
| Profile | ✅ Yes | ❌ No | Flask matched |
| JD requires | ❌ No | ✅ Yes | FastAPI missing |

### has_profile_evidence Expected Values
- `has_profile_evidence.flask`: **true** (matched from CV and profile)
- `has_profile_evidence.python`: **true** (matched from CV and profile)
- `has_profile_evidence.fastapi`: **false** (not in CV or profile)

### Expected missing_skills
- `missing_skills` MUST include: FastAPI

### Critical Anti-Fabrication Rule
System should NOT fabricate FastAPI evidence:

**MUST NOT:**
- ❌ Say "Flask translates to FastAPI experience"
- ❌ Claim similar frameworks mean FastAPI competency
- ❌ Fabricate FastAPI projects or experience
- ❌ Use Flask as substitute for FastAPI requirement

**MUST:**
- ✅ Acknowledge FastAPI is missing
- ✅ Match Flask where appropriate
- ✅ Clearly indicate FastAPI in missing_skills
- ✅ Be transparent about the gap

### Cover Letter Behavior
- Can reference Flask experience from profile
- Should NOT claim FastAPI experience if not present
- Should acknowledge the technology gap
- System should not conflate Flask and FastAPI

### Guardrail Checks — No Framework Substitution
- System should NOT claim "Flask is similar to FastAPI"
- System should NOT fabricate FastAPI skills
- Missing skills should include FastAPI
- CV + Profile gap for FastAPI must be visible
