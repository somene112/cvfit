# Expected Behavior — Interview Practice Case IP2_12: Behavioral — Problem Solving

## Case Context
This case evaluates interview prep for a candidate with strong problem-solving evidence through a specific incident. The JD mentions problem-solving and debugging.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `behavioral` questions about problem-solving approach
  - Question about debugging methodology
  - Question about resolving production issues
  - `related_cv_evidence` should reference: "Identified root cause of production outage affecting data sync"
  - `related_jd_requirement` should reference: "Problem-solving skills" and "Debugging abilities"

- Technical questions about the specific problem (race conditions, connection pooling)

#### Must NOT Include
- Questions dismissing junior-level problem-solving experience
- Questions requiring senior-level architecture experience

### Question Structure
```
type: behavioral | technical_concept
question: non-empty string
related_cv_evidence: list referencing problem-solving evidence
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer about debugging:
- Describes systematic approach (logs, queries, analysis)
- Identifies specific technical issue (race condition, connection pool)
- Shows solution implementation (context manager, locking, monitoring)
- Provides quantifiable results (500+ errors to near zero)

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses problem-solving requirement |
| specificity | strong | Names specific debugging steps and solutions |
| evidence | strong | References specific incident from CV |
| structure | strong | Systematic problem-solving narrative |

### Expected Feedback Points
- Praise for systematic debugging approach
- Highlight specific technical solutions mentioned
- Note connection to JD problem-solving requirements
- Suggest areas for deeper technical exploration

## Guardrail Checks
- Questions should validate junior-level problem-solving
- Questions must not require years of experience
- Answer outlines should reflect appropriate expectations
