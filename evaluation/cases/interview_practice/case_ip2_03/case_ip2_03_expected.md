# Expected Behavior — Interview Practice Case IP2_03: Technical Question — Weak Answer (Vague CV)

## Case Context
This case evaluates interview prep for a candidate with vague CV and weak answer. The CV lacks concrete details, and the user answer is too generic.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `gap_probe` questions for FastAPI, PostgreSQL, Redis (missing from CV)
  - Must acknowledge lack of evidence in `why_this_question`
  - Must include learning resources in `suggested_answer_outline`

- `project_deep_dive` question about Python scripts (limited CV evidence)
  - Must probe for specifics: what kind of scripts? what libraries used?
  - `risk_if_user_cannot_answer` should warn about weak project evidence

#### Must NOT Include
- Questions assuming FastAPI/Django/PostgreSQL experience
- Questions fabricating backend project experience

### Question Structure
```
type: gap_probe | project_deep_dive
question: non-empty string (probing for specifics)
related_cv_evidence: list (may be empty for gap_probe)
related_jd_requirement: non-empty string
why_this_question: non-empty string (must acknowledge gap)
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object with preparation guidance
```

## User Answer Evaluation

### Answer Analysis
The user answer "I know Python well" is:
- Not specific about what aspects of Python
- Does not mention any frameworks, libraries, or projects
- No connection to JD requirements (FastAPI, PostgreSQL, Redis)
- Does not demonstrate actual Python proficiency

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | weak | Answer doesn't address any JD requirements |
| specificity | weak | No concrete details about Python skills |
| evidence | weak | No project evidence from CV to support claim |
| structure | weak | Single vague statement |

### Expected Feedback Points
- Flag the vagueness of the answer
- Reference specific JD requirements (FastAPI, PostgreSQL, Redis)
- Suggest concrete ways to demonstrate Python knowledge
- Provide learning roadmap for missing skills
- Note the gap between current skills and JD requirements

## Guardrail Checks
- Questions must NOT fabricate FastAPI/PostgreSQL/Redis experience
- Questions must probe for actual experience, not assume it exists
- Answer outlines must include honest learning guidance
- Feedback must be encouraging but realistic about skill gaps
