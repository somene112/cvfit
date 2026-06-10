# Expected Behavior — Application Package Case 11: Best CV Recommendation — Highest Score Wins

## CV Profile
Strong profile with 2 projects:
- E-Commerce Platform: FastAPI, PostgreSQL, Redis
- Data Analytics Dashboard: Python, PostgreSQL

Both projects provide evidence for backend skills.

## JD Context
Backend engineer requiring Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 82 (>= 75).

### Critical Behavior: best_cv_analysis.fit_score = 82 (Highest Score)
When multiple analyses exist, the best_cv_analysis should select the analysis with the highest fit_score. In this case, fit_score=82 is the highest, so:
- `best_cv_analysis.fit_score` must equal 82
- `best_cv_analysis.matched_skills` must have at least 3 items (Python, FastAPI, PostgreSQL, Redis = 4 items)

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=82
2. `best_cv_analysis` — **with fit_score=82, matched_skills length >= 3**
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}`
5. `learning_roadmap` — must be `[]`
6. `evidence_checklist` — items for matched skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 82
- readiness_summary.readiness_level = "ready"
- **best_cv_analysis.fit_score = 82**
- **best_cv_analysis.matched_skills has length >= 3** (Python, FastAPI, PostgreSQL, Redis)
- best_cv_analysis.missing_skills includes Docker, Kubernetes
- best_cv_analysis.strengths mentions strong backend foundation
- disclaimer is present

### Must NOT Include
- best_cv_analysis with lower fit_score than available (must be 82, the highest)
- best_cv_analysis with fewer than 3 matched skills
- readiness_level other than "ready" when fit_score >= 75
