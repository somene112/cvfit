# Expected Behavior — Application Package Case 07: Learning Roadmap Present

## CV Profile
Minimal profile with only Python skill listed. No project experience documented.

## JD Context
Backend engineer requiring FastAPI, PostgreSQL, Docker.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `almost_ready` because `fit_score` is 68 (55 <= 68 < 75).

### Critical Behavior: learning_roadmap Must Have 3 Items
The `learning_roadmap` array must contain exactly 3 items, one for each missing skill:
- FastAPI (priority: high, ~2-3 weeks)
- PostgreSQL (priority: high, ~2-3 weeks)
- Docker (priority: medium, ~1-2 weeks)

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="almost_ready", fit_score=68
2. `best_cv_analysis` — with fit_score=68, matched_skills (Python, Flask), missing_skills (FastAPI, PostgreSQL, Docker)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no interview prep)
5. `learning_roadmap` — **with 3 items (FastAPI, PostgreSQL, Docker)**
6. `evidence_checklist` — items for matched and missing skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 68
- readiness_summary.readiness_level = "almost_ready"
- best_cv_analysis.fit_score = 68
- best_cv_analysis.matched_skills = ["Python", "Flask"]
- best_cv_analysis.missing_skills = ["FastAPI", "PostgreSQL", "Docker"]
- **learning_roadmap has exactly 3 items**
- Each roadmap item must include: skill, priority, topics (array), estimated_effort
- roadmap for FastAPI includes topics: REST API design, Pydantic validation, async, middleware
- roadmap for PostgreSQL includes topics: database design, query optimization, indexes, transactions
- roadmap for Docker includes topics: container basics, Dockerfile, docker-compose, networking
- interview_prep_pack.questions = [] (empty)
- disclaimer is present

### Must NOT Include
- learning_roadmap with more or fewer than 3 items
- roadmap items without all required fields (skill, priority, topics, estimated_effort)
- interview_prep_pack.questions with any questions
- roadmap items for skills that are matched (only missing skills should have roadmap)
