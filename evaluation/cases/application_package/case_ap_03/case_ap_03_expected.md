# Expected Behavior — Application Package Case 03: Needs Work

## CV Profile
Empty profile with no projects, skills, certifications, or education listed.

## JD Context
Backend engineer role requiring FastAPI, PostgreSQL, Redis, Docker, AWS, Kubernetes.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `needs_work` because `fit_score` is 35 (0 < 35 < 55).

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="needs_work", fit_score=35, summary about significant gaps, long next_actions list
2. `best_cv_analysis` — with fit_score=35, matched_skills=["Python"], missing_skills (FastAPI, PostgreSQL, Redis, Docker, AWS, Kubernetes)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no prep for incomplete profiles)
5. `learning_roadmap` — must be `[]` (no roadmap for empty profiles)
6. `evidence_checklist` — items for matched and missing skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 35
- readiness_summary.readiness_level = "needs_work"
- readiness_summary.summary mentions significant skill gaps
- readiness_summary.next_actions has at least 4 actionable items for missing skills
- best_cv_analysis.fit_score = 35
- best_cv_analysis.matched_skills = ["Python"] (only skill)
- best_cv_analysis.missing_skills includes FastAPI, PostgreSQL, Redis, Docker, AWS, Kubernetes
- best_cv_analysis.strengths is empty or mentions only Python basics
- best_cv_analysis.improvement_actions has at least 4 items
- interview_prep_pack.questions = [] (empty)
- learning_roadmap = [] (empty)
- disclaimer is present

### Must NOT Include
- readiness_level = "ready" or "almost_ready" (35 < 55)
- interview questions when no significant matched skills
- roadmap items when profile is empty
- fabricated project evidence
