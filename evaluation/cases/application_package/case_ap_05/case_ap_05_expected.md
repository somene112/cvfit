# Expected Behavior — Application Package Case 05: Cover Letter is Null (Correct Behavior)

## CV Profile
Profile with 1 project (Backend API Service) using FastAPI and PostgreSQL. Skills include Python, FastAPI, PostgreSQL.

## JD Context
Backend engineer role requiring Python, FastAPI, PostgreSQL, Redis, Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 75 (>= 75).

### Critical Behavior: cover_letter_draft Must Be Null
The `cover_letter_draft` field in the application package must be `null`. This is the **correct behavior** per current implementation — the actual cover letter is generated separately via the cover_letter.py service, not included in the application package.

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=75
2. `best_cv_analysis` — with fit_score=75, matched_skills (Python, FastAPI, PostgreSQL)
3. `cover_letter_draft` — **must be `null`** (cover letter generated separately)
4. `interview_prep_pack` — must be `{"questions": []}` (fit_score=75 meets threshold but no interview prep in analysis)
5. `learning_roadmap` — must be `[]` (no roadmap in analysis)
6. `evidence_checklist` — items for matched skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 75
- readiness_summary.readiness_level = "ready"
- best_cv_analysis.fit_score = 75
- best_cv_analysis.matched_skills includes Python, FastAPI, PostgreSQL
- best_cv_analysis.missing_skills includes Redis, Docker
- **cover_letter_draft = null** (this is correct!)
- disclaimer is present

### Must NOT Include
- cover_letter_draft with any content (must be null even when fit_score is 75)
- interview_prep_pack.questions with any questions (array empty)
- learning_roadmap with any items (array empty)
- fabricated cover letter content

### Note on Cover Letter Behavior
The cover letter draft is intentionally `null` in the application package. Cover letters are generated through a separate service (cover_letter.py) and should not be included in the application package output. This is correct behavior, not a bug.
