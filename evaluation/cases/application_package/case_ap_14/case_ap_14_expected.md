# Expected Behavior — Application Package Case 14: Application With No Analysis Jobs Attached

## CV Profile
Profile has 1 project (Portfolio Website with Python) and 1 skill (Python), but no analysis job is attached.

## JD Context
No job description attached (no analysis job).

## Expected Application Package Output

### Readiness Level
`readiness_level` must be `not_started` because `fit_score` is `null` (no analysis attached).

### Critical Behavior: Profile Exists But Analysis Does Not
Even though the profile has content (1 project, 1 skill), the application package must reflect `not_started` because no analysis job is attached. The profile content should not be used to fabricate an analysis.

### Required Sections
The application package must contain ALL of the following sections:
1. `readiness_summary` — with readiness_level="not_started", fit_score=null, next_actions about attaching analysis
2. `best_cv_analysis` — with job_id=null, fit_score=null, empty arrays
3. `cover_letter_draft` — must be `null`
4. `interview_prep_pack` — must be `{"questions": []}`
5. `learning_roadmap` — must be `[]`
6. `evidence_checklist` — must be `[]`
7. `disclaimer` — non-empty string

### Must Include
- readiness_summary.readiness_level = "not_started"
- readiness_summary.fit_score = null
- readiness_summary.next_actions includes "attach an analysis job" or similar
- best_cv_analysis.job_id = null
- best_cv_analysis.fit_score = null
- best_cv_analysis.matched_skills = [] (empty, not fabricated from profile)
- best_cv_analysis.missing_skills = [] (empty, not fabricated)
- **profile content should NOT be used to generate skills or evidence**
- disclaimer is present

### Must NOT Include
- readiness_level other than "not_started"
- non-null fit_score values
- matched_skills or missing_skills populated from profile
- interview_prep_pack.questions with questions (array empty)
- learning_roadmap with items (array empty)
- fabricated analysis based on profile content
