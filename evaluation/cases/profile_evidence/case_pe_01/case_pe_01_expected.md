# Expected Behavior — Profile Evidence Case 01: Project Evidence Relevant to JD

## CV Profile
Python, FastAPI developer with 3 years of experience. Has E-Commerce Product API project in CV.

## JD Profile
Requires Python, FastAPI, PostgreSQL, Docker for backend engineer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile project "E-Commerce API" should match the following JD requirements:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| FastAPI | Project skills_json, description | ✅ Should match |
| PostgreSQL | Project skills_json, description | ✅ Should match |
| Python | Implicit from FastAPI project | ✅ Should match |
| Docker | Project skills_json | ✅ Should match |

### has_profile_evidence Expected Values
- `has_profile_evidence.fastapi`: **true** (matched via skills_json and description)
- `has_profile_evidence.postgresql`: **true** (matched via skills_json and description)
- `has_profile_evidence.docker`: **true** (matched via skills_json)
- `has_profile_evidence.python`: **true** (implied from FastAPI)

### Evidence Strength Assessment
- **FastAPI**: Strong — explicit in skills_json AND in description
- **PostgreSQL**: Strong — explicit in skills_json AND in description
- **Docker**: Medium — listed in skills_json only

### Expected Evidence Text Usage
- evidence_text should be usable as supporting evidence in cover letter
- The 10,000+ daily requests and 60% reduction metrics should be accessible
- Cover letter should NOT fabricate additional metrics not in profile

### Guardrail Checks
- System should NOT fabricate FastAPI features not described
- System should NOT claim expertise levels not indicated
- Profile evidence should be used but not exaggerated
