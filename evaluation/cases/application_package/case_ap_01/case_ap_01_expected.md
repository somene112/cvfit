# Expected Behavior — Application Package Case 01: Complete Readiness

## CV Profile
Strong backend profile with 2 projects demonstrating FastAPI, PostgreSQL, Redis, Docker, and Python. E-Commerce API has concrete metrics (500+ endpoints, 10K+ requests/day). Data Pipeline shows ETL experience.

## JD Context
Standard backend engineer role requiring FastAPI, PostgreSQL, Redis, and Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 82 (>= 75).

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=82, non-empty summary, and next_actions
2. `best_cv_analysis` — with fit_score=82, matched_skills (Python, FastAPI, PostgreSQL, Redis, Docker), missing_skills (empty array)
3. `cover_letter_draft` — must be `null` (generated separately via cover_letter.py)
4. `interview_prep_pack` — with 3 questions (all project_deep_dive type)
5. `learning_roadmap` — with 2 items (Kubernetes, AWS)
6. `evidence_checklist` — items for each matched skill with has_profile_evidence=true
7. `disclaimer` — non-empty string explaining AI-generated content limitations

### Must Include
- readiness_summary.fit_score = 82
- readiness_summary.readiness_level = "ready"
- readiness_summary.next_actions should mention adding profile evidence (skills already matched)
- best_cv_analysis.fit_score = 82
- best_cv_analysis.matched_skills includes Python, FastAPI, PostgreSQL, Redis, Docker
- best_cv_analysis.missing_skills = [] (empty array)
- interview_prep_pack.questions has exactly 3 items
- Each interview question must include: type, related_cv_evidence, related_jd_requirement, why_this_question, risk_if_user_cannot_answer
- learning_roadmap has 2 items with skill, priority, topics, estimated_effort
- evidence_checklist items for FastAPI, PostgreSQL, Redis, Docker all have has_profile_evidence=true
- disclaimer contains phrases like "must be reviewed", "do not include", or "guarantee"

### Must NOT Include
- fabricated skills not present in analysis result
- fabricated project evidence not in the CV profile
- interview questions about skills not in analysis (e.g., Kubernetes, AWS as interview questions)
- readiness_level values other than "ready"
