# Expected Behavior — Interview Practice Case IP2_02: Technical Question — Strong Answer (Experienced Dev)

## Case Context
This case evaluates interview prep for a senior backend engineer with extensive experience. The user provides a detailed technical answer about PostgreSQL sharding architecture.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- Senior-level technical questions appropriate for 5+ years experience
- Architecture and system design questions
- Questions about scalability, microservices, AWS

- At least 1 `project_deep_dive` question about the e-commerce platform (matching CV)
  - Must reference FastAPI, PostgreSQL, Redis from CV
  - Must reference system design from JD
  - `related_cv_evidence` should reference: "Led architecture design for high-traffic e-commerce platform serving 100K+ daily users"

- Questions about AWS services mentioned in CV (ECS, RDS, Lambda)
- Questions about team leadership and mentoring

#### Must NOT Include
- Entry-level algorithm questions
- Questions about skills not in CV or JD

### Question Structure
```
type: project_deep_dive | technical_concept | system_design | behavioral
question: non-empty string (senior-level complexity)
related_cv_evidence: list of relevant CV evidence
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: non-empty object
```

## User Answer Evaluation

### Answer Analysis
The user answer about PostgreSQL sharding:
- Demonstrates deep understanding of horizontal partitioning
- Shows practical experience with production-scale systems (100K+ users)
- Mentions specific metrics (75% load reduction, 500ms to 50ms improvement)
- Addresses data consistency and compliance challenges

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses database scalability requirement |
| specificity | strong | Includes concrete numbers and technical approach |
| evidence | strong | Reflects extensive backend experience from CV |
| structure | strong | Logical explanation of problem, solution, and challenges |

### Expected Feedback Points
- Praise for quantifiable metrics
- Acknowledge sophisticated understanding of database scaling
- Note connection to e-commerce platform experience
- Could probe deeper into failure scenarios or edge cases

## Guardrail Checks
- Questions must be senior-level, not junior
- Questions must NOT downplay the candidate's experience
- Answer outlines must reflect enterprise-scale considerations
