# Expected Behavior — Profile Evidence Case 09: Achievement with Metrics as Strong Evidence

## CV Profile
Junior Python developer with Django experience. CV does not mention specific achievements or metrics.

## JD Profile
Requires Python, Django, PostgreSQL for junior backend developer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile achievement should match JD requirements:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| Django | Achievement skills_json | ✅ Should match |
| Performance | Achievement skills_json | ✅ Should match (related) |
| PostgreSQL | Achievement skills_json | ✅ Should match |
| Python | Not in profile | ⚠️ From CV context |

### has_profile_evidence Expected Values
- `has_profile_evidence.django`: **true** (matched via achievement)
- `has_profile_evidence.performance`: **true** (matched via achievement)
- `has_profile_evidence.postgresql`: **true** (matched via achievement)

### Metrics Accessibility — Critical
The following metrics should be accessible:

| Metric | Value | Source |
|--------|-------|--------|
| Page load time reduction | 50% | description |
| API response time improvement | 30% | description |
| Optimization type | Django query optimization | description |

### Evidence Strength Assessment
- **Django**: **Strong** — achievement demonstrates real Django usage
- **Performance**: **Strong** — concrete metric (50%)
- **PostgreSQL**: **Medium** — mentioned in context

### Cover Letter Behavior
- Achievement metrics can be referenced in cover letter
- Should say "Reduced page load time by 50%" if referencing achievement
- Should NOT say "Reduced by 60%" — must match profile exactly
- Achievement demonstrates practical Django skills

### Guardrail Checks
- System should use metrics exactly as stated in profile
- 50% reduction should be used as "50%", not "half"
- System should NOT inflate metrics
- Achievement provides strong evidence for Django competency
