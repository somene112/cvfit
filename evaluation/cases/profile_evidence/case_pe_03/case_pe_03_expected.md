# Expected Behavior — Profile Evidence Case 03: Project Evidence with Skills Array

## CV Profile
Python developer with FastAPI experience. CV mentions API Service project with FastAPI, PostgreSQL, Redis.

## JD Profile
Requires Python, FastAPI, Redis, PostgreSQL for backend API developer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile project "API Service" skills_json should match JD requirements:

| JD Requirement | skills_json Match | Expected Result |
|----------------|-------------------|-----------------|
| Python | ["FastAPI", "Redis", "PostgreSQL", "Python"] | ✅ Should match |
| FastAPI | ["FastAPI", "Redis", "PostgreSQL", "Python"] | ✅ Should match |
| Redis | ["FastAPI", "Redis", "PostgreSQL", "Python"] | ✅ Should match |
| PostgreSQL | ["FastAPI", "Redis", "PostgreSQL", "Python"] | ✅ Should match |

### has_profile_evidence Expected Values
- `has_profile_evidence.python`: **true** (matched via skills_json)
- `has_profile_evidence.fastapi`: **true** (matched via skills_json)
- `has_profile_evidence.redis`: **true** (matched via skills_json)
- `has_profile_evidence.postgresql`: **true** (matched via skills_json)

### Evidence Strength Assessment
- **Python**: Strong — in skills_json
- **FastAPI**: Strong — in skills_json AND description
- **Redis**: Strong — in skills_json AND description
- **PostgreSQL**: Strong — in skills_json AND description

### skills_json Matching Logic
The `_is_backed_by_profile()` function should check:
1. Case-insensitive match in skills_json array
2. "fastapi" should match "FastAPI" ✅
3. "redis" should match "Redis" ✅
4. "postgresql" should match "PostgreSQL" ✅

### Cover Letter Behavior
- All four required skills have profile backing
- Cover letter can reference the API Service project
- No fabrication of additional technologies

### Guardrail Checks
- System should match case-insensitively (redis = Redis = REDIS)
- System should NOT add skills not in skills_json
- skills_json entries should be used for matching, not description alone
