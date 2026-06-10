# Expected Behavior — Interview Practice Case IP2_10: Behavioral — Leadership Experience

## Case Context
This case evaluates interview prep for a candidate with strong leadership and teamwork evidence from non-work experience. The JD mentions team collaboration as a requirement.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `behavioral` questions about leadership experiences
  - Question about managing team conflicts
  - Question about delegating tasks to team members
  - `related_cv_evidence` should reference: "Led a team of 15 members organizing technical events"
  - `related_jd_requirement` should reference: "Team collaboration skills"

- Questions connecting leadership to technical work
  - How leadership skills apply to technical projects

#### Must NOT Include
- Questions fabricating corporate leadership experience
- Questions downplaying non-traditional leadership experience

### Question Structure
```
type: behavioral
question: non-empty string
related_cv_evidence: list referencing leadership evidence
related_jd_requirement: non-empty string (team collaboration)
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer about hackathon leadership:
- Describes specific leadership actions (task breakdown, delegation)
- Mentions conflict resolution approach
- Provides quantifiable outcome (50+ participants)
- Shows understanding of team management principles

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses team collaboration requirement |
| specificity | strong | Names specific actions and outcomes |
| evidence | strong | References leadership experience from CV |
| structure | strong | STAR format with situation, action, result |

### Expected Feedback Points
- Praise for concrete leadership examples
- Highlight conflict resolution and delegation skills
- Note connection to JD team collaboration requirement
- Suggest how these skills transfer to technical teams

## Guardrail Checks
- Questions should acknowledge non-traditional leadership experience
- Questions must not require corporate management experience
- Answer outlines should validate varied leadership sources
