# Expected Behavior — Application Package Case 15: Interview Prep Empty But Roadmap Present

## CV Profile
Profile with Blog Application project using Python and Flask. Skills include Python, Flask.

## JD Context
Backend engineer requiring Python, Flask, FastAPI, PostgreSQL.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `almost_ready` because `fit_score` is 67 (55 <= 67 < 75).

### Critical Behavior: interview_prep_pack.questions Is Empty, learning_roadmap Has 2 Items
Even though fit_score is 67 (close to ready), the analysis result has:
- interview_prep: [] (empty — no interview prep generated)
- learning_roadmap: 2 items (FastAPI, PostgreSQL)

The package should faithfully reflect the analysis result:
- **interview_prep_pack.questions must be empty array**
- **learning_roadmap must have 2 items**

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="almost_ready", fit_score=67
2. `best_cv_analysis` — with fit_score=67, matched_skills (Python, Flask), missing_skills (FastAPI, PostgreSQL)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — **with questions=[] (empty)**
5. `learning_roadmap` — **with 2 items (FastAPI, PostgreSQL)**
6. `evidence_checklist` — items for skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 67
- readiness_summary.readiness_level = "almost_ready"
- best_cv_analysis.fit_score = 67
- best_cv_analysis.matched_skills = ["Python", "Flask"]
- best_cv_analysis.missing_skills = ["FastAPI", "PostgreSQL"]
- **interview_prep_pack.questions = []** (empty, no questions)
- **learning_roadmap has exactly 2 items**
- roadmap items: FastAPI (high priority, 2-3 weeks) and PostgreSQL (high priority, 2-3 weeks)
- disclaimer is present

### Must NOT Include
- interview_prep_pack.questions with any questions (array must be empty despite fit_score)
- learning_roadmap with more or fewer than 2 items
- readiness_level = "ready" (67 < 75)
- readiness_level = "needs_work" (67 >= 55)
