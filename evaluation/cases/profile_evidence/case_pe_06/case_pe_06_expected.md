# Expected Behavior — Profile Evidence Case 06: Skill Evidence Matched to JD

## CV Profile
Python developer. CV mentions Docker knowledge but not prominently. No specific Docker projects in CV.

## JD Profile
Requires Python, FastAPI, Docker, Kubernetes for senior backend engineer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile skill "Docker" should match the JD Docker requirement:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| Docker | Profile skill item | ✅ Should match |
| Containerization | Profile skills_json | ✅ Should match (related) |
| Python | Not in profile skill | ⚠️ From CV context |
| FastAPI | Not in profile | ❌ From CV context only |
| Kubernetes | Not in profile | ❌ Should NOT match |

### has_profile_evidence Expected Values
- `has_profile_evidence.docker`: **true** (matched via skill item)
- `has_profile_evidence.containerization`: **true** (matched via skills_json)
- `has_profile_evidence.kubernetes`: **false** (not in profile)

### Evidence Strength Assessment
- **Docker**: **Medium-Strong** — explicit skill item with description
- **Kubernetes**: **None** — not in profile

### Skill Item Type Handling
- `item_type: "skill"` should be recognized
- `_is_backed_by_profile()` should check skill items
- Skill without project context is valid evidence

### Expected missing_skills
- `missing_skills` should include: Kubernetes, FastAPI (if not in CV)

### Cover Letter Behavior
- Docker skill can be used from profile
- Cover letter should NOT fabricate Kubernetes experience
- No project context needed for skill matching
- If project context is needed, it should be noted

### Guardrail Checks
- System should NOT fabricate Kubernetes if not in profile
- Skill item type should be handled correctly
- Docker should match even without project attachment
