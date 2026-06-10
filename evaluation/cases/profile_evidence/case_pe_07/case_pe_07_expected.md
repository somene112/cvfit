# Expected Behavior — Profile Evidence Case 07: Skill Evidence Not Fabrication

## CV Profile
Python developer with Flask experience. CV does not mention FastAPI. FastAPI skill exists only in profile.

## JD Profile
Requires Python and FastAPI for backend API developer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile skill "FastAPI" should match the JD requirement:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| FastAPI | Profile skill item | ✅ Should match |
| Python | Profile skills_json | ✅ Should match |
| REST API | Profile skills_json | ✅ Should match (related) |

### has_profile_evidence Expected Values
- `has_profile_evidence.fastapi`: **true** (matched via skill item)
- `has_profile_evidence.python`: **true** (matched via skills_json)
- `has_profile_evidence.rest_api`: **true** (matched via skills_json)

### Evidence Strength Assessment
- **FastAPI**: **Medium** — skill item with description, no project context
- **Python**: **Medium** — in skills_json

### No Fabrication Expected Behavior
The FastAPI skill has NO project attached. System should:

1. ✅ Recognize FastAPI skill from profile
2. ✅ Use FastAPI for matching
3. ❌ NOT fabricate a specific project name for FastAPI
4. ❌ NOT claim "Built X project with FastAPI" unless in profile

### Cover Letter Behavior
- Can mention FastAPI skill from profile
- Should NOT invent project context for FastAPI
- If project context is needed, use general language
- Should be transparent about skill-only evidence

### Guardrail Checks — No Project Fabrication
- System should NOT say "I built the E-Commerce API with FastAPI" if no such project
- System should NOT reference a project name not in profile
- Skill-only evidence is valid but should be handled carefully
- No invented context or project details
