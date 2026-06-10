# Expected Behavior — Profile Evidence Case 05: Project Evidence with Vague Description

## CV Profile
Backend developer with Python experience. CV mentions vague "Web App" project with minimal details.

## JD Profile
Requires Python, FastAPI, PostgreSQL for backend engineer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile project "Web App" is vague and provides weak evidence:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| Python | skills_json | ✅ Should match (weak) |
| FastAPI | Not in profile | ❌ Should NOT match |
| PostgreSQL | Not in profile | ❌ Should NOT match |

### has_profile_evidence Expected Values
- `has_profile_evidence.python`: **true** (matched via skills_json — weak evidence)
- `has_profile_evidence.fastapi`: **false** (not in profile)
- `has_profile_evidence.postgresql`: **false** (not in profile)

### Evidence Strength Assessment
- **Python**: **Weak** — only in skills_json, no supporting description
- **FastAPI**: None — not mentioned anywhere
- **PostgreSQL**: None — not mentioned anywhere

### Expected missing_skills
- `missing_skills` should include: FastAPI, PostgreSQL

### Cover Letter Behavior — Critical
- System should NOT fabricate FastAPI experience
- System should NOT fabricate PostgreSQL experience
- System should NOT claim the "Web App" did more than described
- System should be transparent about weak evidence

### Guardrail Checks — No Fabrication
- System should NOT say "Built REST APIs with FastAPI" if not in profile
- System should NOT say "Implemented PostgreSQL database" if not in profile
- System should NOT expand "web app" to mean specific technologies
- If evidence is weak, cover letter should acknowledge this

### Weak Evidence Handling
- Profile is usable (not broken)
- But evidence should be marked as weak in review_notes
- No fabrication of specific technologies
