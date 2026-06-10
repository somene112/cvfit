# Expected Behavior — Profile Evidence Case 11: Education with Relevant Context

## CV Profile
Recent CS graduate. CV mentions education and coursework but no professional experience.

## JD Profile
Requires Python, Django, SQL for junior backend developer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile education should provide contextual evidence:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| Python | Education skills_json | ✅ Should match (academic) |
| SQL | Education skills_json | ✅ Should match (academic) |
| Database | Education skills_json | ✅ Should match (related) |
| Django | Not in education | ❌ Should NOT match |
| Data Structures | Education skills_json | ✅ Related skill |

### has_profile_evidence Expected Values
- `has_profile_evidence.python`: **true** (academic evidence)
- `has_profile_evidence.sql`: **true** (academic evidence)
- `has_profile_evidence.database`: **true** (academic evidence)
- `has_profile_evidence.django`: **false** (not in profile)

### Evidence Strength Assessment
- **Python**: **Medium** — academic coursework, not professional
- **SQL**: **Medium** — academic coursework
- **Django**: **None** — not mentioned anywhere

### Education Evidence Handling
Education can be used for:
1. Context (CS background provides foundation)
2. Skills learned during education
3. Supplementing CV with academic evidence

Education should NOT be used to:
1. Claim professional experience
2. Fabricate industry experience
3. Exaggerate academic achievements

### Expected missing_skills
- `missing_skills` should include: Django

### Cover Letter Behavior
- Can reference CS education and Python coursework
- Should NOT claim professional Django experience
- Should acknowledge being a recent graduate
- Can use academic projects as evidence

### Guardrail Checks
- System should not claim "2 years Django experience" from education
- Education evidence should be labeled as academic
- System should not fabricate work experience
