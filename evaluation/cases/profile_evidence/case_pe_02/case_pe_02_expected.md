# Expected Behavior — Profile Evidence Case 02: Project Evidence with Detailed Metrics

## CV Profile
Backend developer with data pipeline experience. CV mentions analytics systems but no specific metrics.

## JD Profile
Requires Python, FastAPI, PostgreSQL, and data pipeline experience.

## Profile Evidence Expected Behavior

### Expected Matches
The profile project "Analytics Pipeline" should provide strong evidence:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| Python | Project skills_json, description | ✅ Should match |
| PostgreSQL | Project skills_json, description | ✅ Should match |
| FastAPI | Not in profile | ⚠️ May match from CV context |
| Data Pipelines | Project description context | ✅ Should match |

### has_profile_evidence Expected Values
- `has_profile_evidence.python`: **true** (explicit in profile)
- `has_profile_evidence.postgresql`: **true** (explicit in profile)
- `has_profile_evidence.fastapi`: **true** (from CV context)

### Evidence Strength Assessment
- **Python**: Strong — explicit in skills_json and description
- **PostgreSQL**: Strong — explicit in skills_json and description
- **Overall**: **Strong evidence** — metrics provided

### Expected Metrics Accessibility
The following metrics from profile should be accessible:

- **10GB**: Daily data processing volume
- **40%**: Processing time reduction

### Cover Letter Behavior
- Cover letter MAY reference the 10GB processing and 40% time reduction
- Metrics should be attributed to profile evidence, not invented
- System should NOT add additional metrics not in profile

### Guardrail Checks
- System should NOT claim "10TB" if profile says "10GB"
- System should NOT claim "60% improvement" if profile says "40%"
- Metrics must match exactly what is in the profile
