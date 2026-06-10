# Expected Behavior — Profile Evidence Case 08: Skill Related to Project

## CV Profile
Backend developer with FastAPI experience. CV mentions API projects.

## JD Profile
Requires Python, FastAPI, PostgreSQL, Redis for backend engineer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile has both a skill "FastAPI" and a project "API Service" with FastAPI:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| FastAPI | Skill + Project | ✅ Strong match |
| Python | Skill + Project | ✅ Strong match |
| PostgreSQL | Project skills_json | ✅ Match |
| Redis | Project skills_json | ✅ Match |

### has_profile_evidence Expected Values
- `has_profile_evidence.fastapi`: **true** (strong — multiple sources)
- `has_profile_evidence.python`: **true** (strong — multiple sources)
- `has_profile_evidence.postgresql`: **true** (matched via project)
- `has_profile_evidence.redis`: **true** (matched via project)

### Evidence Strength Assessment
- **FastAPI**: **Very Strong** — skill item AND project with same skill
- **Python**: **Very Strong** — in both skill and project skills_json
- **PostgreSQL**: **Strong** — in project skills_json
- **Redis**: **Strong** — in project skills_json

### Skill + Project Combination Effect
When a skill has related project evidence:
1. Skill confirms the competency
2. Project provides concrete context
3. Evidence strength is multiplicative

### Cover Letter Behavior
- FastAPI and Python skills have strong backing
- Project details can be referenced
- Evidence from both skill and project can be combined
- System should leverage the combined evidence

### Guardrail Checks
- System should recognize when skill and project align
- Should not duplicate claims from both items
- Should use combined evidence for stronger cover letter
- No fabrication needed — evidence is strong
