# Expected Behavior — Application Package Case 06: Interview Prep Present

## CV Profile
Strong profile with Microservices Platform project demonstrating FastAPI, PostgreSQL, Redis. Skills include Python, FastAPI, PostgreSQL, Redis.

## JD Context
Backend engineer requiring FastAPI, PostgreSQL, Redis, Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `ready` because `fit_score` is 78 (>= 75).

### Critical Behavior: interview_prep_pack Must Have 5 Questions
The `interview_prep_pack.questions` array must contain exactly 5 questions:
- 3 technical questions (project_deep_dive type)
- 2 behavioral questions

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="ready", fit_score=78
2. `best_cv_analysis` — with fit_score=78, matched_skills (Python, FastAPI, PostgreSQL, Redis)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — **with 5 questions (3 technical, 2 behavioral)**
5. `learning_roadmap` — must be `[]` (no roadmap in analysis)
6. `evidence_checklist` — items for matched skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 78
- readiness_summary.readiness_level = "ready"
- best_cv_analysis.fit_score = 78
- best_cv_analysis.matched_skills includes Python, FastAPI, PostgreSQL, Redis
- **interview_prep_pack.questions has exactly 5 items**
- Technical questions (3) must be type="project_deep_dive" with related_cv_evidence
- Behavioral questions (2) must be type="behavioral"
- Each question must include: question, type, related_cv_evidence, related_jd_requirement, why_this_question, risk_if_user_cannot_answer
- cover_letter_draft = null
- disclaimer is present

### Must NOT Include
- interview_prep_pack.questions with more or fewer than 5 items
- questions about skills not in analysis (e.g., Docker interview questions)
- fabricated project evidence
- questions without all required fields
