# Expected Behavior — Profile Evidence Case 13: Unrelated Evidence Not Used

## CV Profile
Python developer with FastAPI and Django experience. Profile has unrelated Graphic Design skill.

## JD Profile
Requires Python, FastAPI for backend API developer role.

## Profile Evidence Expected Behavior

### Unrelated Evidence Analysis
The profile skill "Graphic Design" has NO relevance to the JD:

| JD Requirement | Graphic Design Match? | Expected Result |
|----------------|---------------------|-----------------|
| Python | No | ❌ Should NOT match via Graphic Design |
| FastAPI | No | ❌ Should NOT match via Graphic Design |
| REST API | No | ❌ Should NOT match via Graphic Design |
| PostgreSQL | No | ❌ Should NOT match via Graphic Design |

### has_profile_evidence Expected Values
- `has_profile_evidence.python`: **false** (Graphic Design doesn't provide Python evidence)
- `has_profile_evidence.fastapi`: **false** (Graphic Design doesn't provide FastAPI evidence)
- `has_profile_evidence.graphic_design`: **true** (skill exists, but unrelated)

### Evidence Strength Assessment
- **Graphic Design**: **Irrelevant** — no connection to backend development
- **Python**: **None** from profile — need from CV or elsewhere
- **FastAPI**: **None** from profile — need from CV or elsewhere

### System Behavior with Unrelated Evidence

**SHOULD:**
- ✅ Recognize Graphic Design exists but is unrelated
- ✅ NOT use Graphic Design for Python/FastAPI matching
- ✅ Match Python/FastAPI from CV or other profile items
- ✅ Preserve Graphic Design in profile but not use for JD

**SHOULD NOT:**
- ❌ Try to force-fit Graphic Design to backend
- ❌ Claim "Design thinking helps with API design"
- ❌ Fabricate connection between design and backend
- ❌ Use unrelated evidence to fill missing skills

### Cover Letter Behavior
- Graphic Design should NOT appear in backend-focused cover letter
- System should not mention design skills in professional context
- Unrelated evidence should remain unused

### Guardrail Checks — No Forced Matching
- System should NOT match unrelated evidence to requirements
- "Design" should NOT become "API Design" automatically
- No fabrication of connections between unrelated domains
- Clean separation between unrelated profile items
