# Expected Behavior — Application Package Case 10: Disclaimer Present

## CV Profile
Minimal profile with only Python skill listed.

## JD Context
Backend engineer requiring Python, Flask, PostgreSQL, FastAPI, Redis.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 75 (>= 75).

### Critical Behavior: Disclaimer Must Be Present and Contain Required Phrases
The `disclaimer` field must be a non-empty string that contains at least ONE of the following phrases:
- "must be reviewed"
- "do not include"
- "guarantee"

This ensures the user understands AI-generated content must be verified before use.

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=75
2. `best_cv_analysis` — with fit_score=75, matched_skills (Python, Flask, PostgreSQL)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}`
5. `learning_roadmap` — must be `[]`
6. `evidence_checklist` — items for skills
7. `disclaimer` — **non-empty string with required phrases**

### Must Include
- readiness_summary.fit_score = 75
- readiness_summary.readiness_level = "ready"
- best_cv_analysis.fit_score = 75
- best_cv_analysis.matched_skills includes Python, Flask, PostgreSQL
- **disclaimer is present and non-empty**
- **disclaimer contains at least one of: "must be reviewed", "do not include", "guarantee"**
- disclaimer should mention that content is AI-generated

### Must NOT Include
- empty disclaimer string
- disclaimer without any of the required phrases
- disclaimer claiming the content is 100% accurate or verified
