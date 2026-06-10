# Expected Behavior — Interview Practice Case IP2_07: Project Deep-Dive — Weak Project Evidence

## Case Context
This case evaluates interview prep for a candidate with vague project descriptions. Both CV and user answer lack specific details.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `gap_probe` questions for FastAPI/Django, PostgreSQL (missing from CV)
  - Must honestly acknowledge lack of evidence
  - `why_this_question` should explain why these skills are needed

- `project_deep_dive` question probing for specifics about the "backend project"
  - Must ask for concrete details (what kind of endpoints? what database design?)
  - `risk_if_user_cannot_answer` should warn about significant risk due to weak evidence
  - `related_cv_evidence` should reference the vague "Backend Project" mention

#### Must NOT Include
- Questions assuming detailed FastAPI/PostgreSQL knowledge
- Questions fabricating project requirements

### Question Structure
```
type: gap_probe | project_deep_dive
question: non-empty string (probing for specifics)
related_cv_evidence: list (may be empty or reference vague mentions)
related_jd_requirement: non-empty string
why_this_question: non-empty string (must acknowledge evidence weakness)
risk_if_user_cannot_answer: non-empty string (should indicate significant risk)
suggested_answer_outline: object with preparation guidance
```

## User Answer Evaluation

### Answer Analysis
The user answer:
- Does not provide any specific details about the project
- Mentions only vague categories (endpoints, user data)
- No mention of specific technologies beyond "Python and some SQL"
- No quantifiable achievements or technical depth
- Cannot be evaluated for relevance to JD requirements

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | cannot_assess | No specific details to evaluate |
| specificity | weak | Extremely vague description |
| evidence | weak | No concrete project evidence from CV |
| structure | weak | Single vague paragraph |

### Expected Feedback Points
- Flag the lack of specific details
- Explain the risk this poses for technical evaluation
- Reference JD requirements that cannot be addressed
- Provide guidance on how to strengthen project descriptions
- Suggest learning paths for missing technical skills

## Guardrail Checks
- Questions must probe for specifics, not assume expertise
- `risk_if_user_cannot_answer` should indicate high risk
- Answer outlines must include honest guidance for improvement
- Feedback should be encouraging but clear about gaps
