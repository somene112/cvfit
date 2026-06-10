# Expected Behavior — Application Package Case 04: Not Started

## CV Profile
Empty profile with no projects, skills, certifications, or education.

## JD Context
No job description attached (no analysis job).

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `not_started` because `fit_score` is `null` (no analysis attached).

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="not_started", fit_score=null, next_actions about attaching analysis
2. `best_cv_analysis` — with job_id=null, fit_score=null, empty arrays for skills
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no prep without analysis)
5. `learning_roadmap` — must be `[]` (no roadmap without analysis)
6. `evidence_checklist` — must be `[]` (no evidence without skills)
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.readiness_level = "not_started"
- readiness_summary.fit_score = null
- readiness_summary.summary mentions no analysis attached
- readiness_summary.next_actions includes "attach an analysis job" or similar
- best_cv_analysis.job_id = null
- best_cv_analysis.fit_score = null
- best_cv_analysis.matched_skills = [] (empty)
- best_cv_analysis.missing_skills = [] (empty)
- best_cv_analysis.strengths = [] (empty)
- best_cv_analysis.improvement_actions = [] (empty)
- interview_prep_pack.questions = [] (empty)
- learning_roadmap = [] (empty)
- evidence_checklist = [] (empty)
- disclaimer is present

### Must NOT Include
- readiness_level = "ready", "almost_ready", or "needs_work" (must be "not_started")
- non-null fit_score values
- non-empty matched_skills or missing_skills arrays
- interview questions without analysis
- roadmap items without analysis
