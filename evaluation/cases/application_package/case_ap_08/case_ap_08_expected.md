# Expected Behavior — Application Package Case 08: Evidence Checklist — All Items Have Profile Evidence

## CV Profile
Strong profile with API Service project explicitly listing FastAPI, PostgreSQL, Redis. Python mentioned in project description.

## JD Context
Backend engineer requiring Python, FastAPI, PostgreSQL, Redis.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 80 (>= 75).

### Critical Behavior: evidence_checklist All Items Have Profile Evidence
All skills in the `evidence_checklist` must have `has_profile_evidence=true` because:
- FastAPI: Listed in API Service project skills
- PostgreSQL: Listed in API Service project skills
- Redis: Listed in API Service project skills
- Python: Implied by FastAPI usage (FastAPI is a Python framework)

The `note` field should indicate "Found in career profile" or similar.

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=80
2. `best_cv_analysis` — with fit_score=80, matched_skills (Python, FastAPI, PostgreSQL, Redis)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no interview prep in analysis)
5. `learning_roadmap` — must be `[]` (no roadmap in analysis)
6. `evidence_checklist` — **all items have has_profile_evidence=true**
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 80
- readiness_summary.readiness_level = "ready"
- best_cv_analysis.fit_score = 80
- best_cv_analysis.matched_skills includes Python, FastAPI, PostgreSQL, Redis
- best_cv_analysis.missing_skills = [] (empty)
- **evidence_checklist items for FastAPI, PostgreSQL, Redis all have has_profile_evidence=true**
- **note field for each item says "Found in career profile" or similar**
- disclaimer is present

### Must NOT Include
- evidence_checklist items with has_profile_evidence=false for skills that are in profile
- evidence_checklist items for skills not in matched_skills or missing_skills
- fabricated evidence notes
