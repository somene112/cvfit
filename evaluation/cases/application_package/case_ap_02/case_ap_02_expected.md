# Expected Behavior — Application Package Case 02: Almost Ready

## CV Profile
Minimal profile with only Python listed as a skill. No project experience documented.

## JD Context
Backend engineer role requiring FastAPI, PostgreSQL, Redis, Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `almost_ready` because `fit_score` is 65 (55 <= 65 < 75).

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="almost_ready", fit_score=65, summary about gaps, and next_actions
2. `best_cv_analysis` — with fit_score=65, matched_skills (Python, Flask, SQLite), missing_skills (PostgreSQL, Redis, FastAPI, Docker)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (empty array, no interview prep generated)
5. `learning_roadmap` — must be `[]` (empty array, no roadmap generated)
6. `evidence_checklist` — items for matched skills with appropriate has_profile_evidence values
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 65
- readiness_summary.readiness_level = "almost_ready"
- readiness_summary.next_actions includes actionable steps for missing skills (PostgreSQL, Redis, FastAPI, Docker)
- best_cv_analysis.fit_score = 65
- best_cv_analysis.matched_skills = ["Python", "Flask", "SQLite"]
- best_cv_analysis.missing_skills = ["PostgreSQL", "Redis", "FastAPI", "Docker"]
- best_cv_analysis.strengths mentions Python proficiency
- interview_prep_pack.questions = [] (empty)
- learning_roadmap = [] (empty)
- disclaimer is present and non-empty

### Must NOT Include
- interview_prep_pack.questions with any questions (array must be empty)
- learning_roadmap with any items (array must be empty)
- readiness_level = "ready" (65 < 75)
- readiness_level = "needs_work" (65 >= 55)
