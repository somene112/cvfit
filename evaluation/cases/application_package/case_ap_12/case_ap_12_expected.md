# Expected Behavior — Application Package Case 12: Package Structure — All Required Sections

## CV Profile
Profile with Backend API project using FastAPI and PostgreSQL. Skills include Python, FastAPI, PostgreSQL.

## JD Context
Backend engineer requiring Python, FastAPI, PostgreSQL, Redis.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 78 (>= 75).

### Critical Behavior: ALL 7 Required Sections Must Be Present
The application package must contain exactly these 7 sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=78
2. `best_cv_analysis` — with fit_score=78
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — with 2 questions
5. `learning_roadmap` — with 1 item (Redis)
6. `evidence_checklist` — items for skills
7. `disclaimer` — non-empty string

### Must Include All Sections
- **readiness_summary**: present with readiness_level, fit_score, summary, next_actions
- **best_cv_analysis**: present with job_id, fit_score, matched_skills, missing_skills, strengths, improvement_actions
- **cover_letter_draft**: null (present but empty)
- **interview_prep_pack**: present with questions array (2 items)
- **learning_roadmap**: present with array (1 item for Redis)
- **evidence_checklist**: present with items for each skill
- **disclaimer**: present with non-empty string

### Must Include
- readiness_summary.fit_score = 78
- readiness_summary.readiness_level = "ready"
- best_cv_analysis.fit_score = 78
- best_cv_analysis.matched_skills includes Python, FastAPI, PostgreSQL
- best_cv_analysis.missing_skills includes Redis
- interview_prep_pack.questions has exactly 2 items
- learning_roadmap has exactly 1 item (Redis)
- disclaimer is present and non-empty

### Must NOT Include
- missing any of the 7 required sections
- extra sections not in the schema
- empty readiness_summary or best_cv_analysis
- interview_prep_pack.questions with more or fewer than 2 items
- learning_roadmap with more or fewer than 1 item
