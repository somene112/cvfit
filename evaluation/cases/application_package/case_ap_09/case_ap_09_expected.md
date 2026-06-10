# Expected Behavior — Application Package Case 09: Evidence Checklist — No Profile Evidence

## CV Profile
Empty profile with no projects, skills, certifications, or education.

## JD Context
Backend engineer requiring Python, FastAPI, PostgreSQL, Redis, Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `almost_ready` because `fit_score` is 72 (55 <= 72 < 75).

### Critical Behavior: evidence_checklist All Items Have No Profile Evidence
All skills in the `evidence_checklist` must have `has_profile_evidence=false` because the profile is empty — no skills, no projects, nothing.

The `note` field for each item should indicate "No profile evidence found" or similar.

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="almost_ready", fit_score=72
2. `best_cv_analysis` — with fit_score=72, matched_skills (Python, FastAPI), missing_skills (PostgreSQL, Redis, Docker)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no interview prep)
5. `learning_roadmap` — must be `[]` (no roadmap)
6. `evidence_checklist` — **all items have has_profile_evidence=false**
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 72
- readiness_summary.readiness_level = "almost_ready"
- best_cv_analysis.fit_score = 72
- best_cv_analysis.matched_skills = ["Python", "FastAPI"]
- best_cv_analysis.missing_skills = ["PostgreSQL", "Redis", "Docker"]
- **evidence_checklist items for ALL skills (matched and missing) have has_profile_evidence=false**
- **note field for each item says "No profile evidence found" or similar**
- disclaimer is present

### Must NOT Include
- evidence_checklist items with has_profile_evidence=true when profile is empty
- evidence_checklist items for skills not in matched_skills or missing_skills
- fabricated evidence notes claiming profile evidence exists
