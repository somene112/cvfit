# Expected Behavior — Application Package Case 13: Package Does NOT Fabricate Data

## CV Profile
Empty profile with no projects, skills, certifications, or education.

## JD Context
Backend engineer requiring Python, FastAPI, PostgreSQL, Redis.

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `needs_work` because `fit_score` is 40 (0 < 40 < 55).

### Critical Behavior: NO FABRICATED DATA
The application package must NOT contain:
- Fabricated skills not in the analysis result
- Fabricated evidence (e.g., project names, metrics, descriptions)
- Fabricated metrics or achievements
- Fabricated profile content

Only skills from the analysis result should appear:
- matched_skills: ["Python"] (only)
- missing_skills: ["FastAPI", "PostgreSQL", "Redis"]

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="needs_work", fit_score=40
2. `best_cv_analysis` — with fit_score=40, matched_skills=["Python"], missing_skills (FastAPI, PostgreSQL, Redis)
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}` (no prep for low score)
5. `learning_roadmap` — must be `[]` (no roadmap for empty profile)
6. `evidence_checklist` — items for skills
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.fit_score = 40
- readiness_summary.readiness_level = "needs_work"
- best_cv_analysis.fit_score = 40
- **best_cv_analysis.matched_skills = ["Python"]** (only, no fabrication)
- **best_cv_analysis.missing_skills = ["FastAPI", "PostgreSQL", "Redis"]** (no extra skills)
- **no fabricated project names or evidence**
- **no fabricated metrics (e.g., "500+ endpoints", "10K users")**
- **no fabricated certifications or education**
- disclaimer is present

### Must NOT Include
- skills not in analysis result (e.g., "Flask", "Docker", "Kubernetes")
- fabricated project evidence (e.g., "Built e-commerce API with...")
- fabricated metrics or achievements
- interview_prep_pack.questions with fabricated questions
- learning_roadmap with fabricated items
- evidence_checklist items for skills not in analysis
