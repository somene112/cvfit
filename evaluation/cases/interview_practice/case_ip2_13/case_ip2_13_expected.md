# Expected Behavior — Interview Practice Case IP2_13: Behavioral — Weak Evidence

## Case Context
This case evaluates interview prep for a fresh graduate with minimal evidence for behavioral questions. The CV lacks teamwork and leadership experience.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `gap_probe` questions for missing behavioral evidence
  - Questions about teamwork, collaboration (no CV evidence)
  - `related_cv_evidence` should be empty or acknowledge lack of evidence
  - `why_this_question` should acknowledge the gap

- General behavioral questions appropriate for entry-level candidates
  - Questions about learning approach
  - Questions about receiving feedback
  - Questions about working in teams (hypothetical)

#### Must NOT Include
- Questions fabricating teamwork or leadership experience
- Questions requiring years of leadership

### Question Structure
```
type: gap_probe | behavioral
question: non-empty string (entry-level appropriate)
related_cv_evidence: list (likely empty)
related_jd_requirement: non-empty string
why_this_question: non-empty string (must acknowledge gap)
risk_if_user_cannot_answer: non-empty string (should be honest about limited evidence)
suggested_answer_outline: object with preparation guidance
```

## User Answer Evaluation

### Answer Analysis
The user answer:
- Acknowledges lack of teamwork and leadership experience
- Shows self-awareness about gaps
- Expresses willingness to learn
- Does not fabricate experience

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | moderate | Acknowledges requirements honestly |
| specificity | weak | Limited specific examples |
| evidence | weak | No teamwork/leadership evidence |
| structure | moderate | Clear and honest response |

### Expected Feedback Points
- Acknowledge honesty about gaps
- Note that fresh graduates are not expected to have extensive experience
- Provide suggestions for building teamwork skills
- Suggest ways to demonstrate collaboration through projects
- Offer encouraging but realistic guidance

## Guardrail Checks
- Questions must NOT fabricate experience
- Questions must acknowledge entry-level status
- Answer outlines should include growth suggestions
- Feedback should be encouraging while honest
