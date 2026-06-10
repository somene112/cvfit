# Expected Behavior — Interview Practice Case IP2_06: Project Deep-Dive — Strong Project Evidence

## Case Context
This case evaluates interview prep for a developer with strong, specific project evidence. The CV contains detailed metrics, and the user provides comprehensive project explanation.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `project_deep_dive` question about the E-Commerce API System
  - Must reference FastAPI, PostgreSQL, Redis from CV
  - Must reference REST API design from JD
  - `related_cv_evidence` must reference: "Built comprehensive REST API for e-commerce platform using FastAPI"
  - `related_cv_evidence` should also reference: "Reduced API response time by 40%"
  - `suggested_answer_outline` should include architecture, caching strategy, database optimization

- Technical questions probing specific details mentioned in CV
  - 500+ endpoints organization
  - Caching strategy implementation
  - Database optimization techniques

#### Must NOT Include
- Questions about skills not in CV (AWS Lambda, GraphQL, etc.)
- Questions assuming no project evidence

### Question Structure
```
type: project_deep_dive
question: non-empty string (should probe specific details)
related_cv_evidence: list referencing E-Commerce project evidence
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string (should be moderate, as evidence is strong)
suggested_answer_outline: object with architecture, caching, database sections
```

## User Answer Evaluation

### Answer Analysis
The user answer about E-Commerce API:
- Provides detailed technical explanation matching CV evidence
- Mentions specific technologies (asyncpg, write-through caching, optimistic locking)
- References specific CV claims (500+ endpoints, 40% performance improvement)
- Shows architectural thinking (modular routers, hierarchical categories)
- Demonstrates understanding of backend best practices

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses backend development requirements |
| specificity | strong | Names specific implementations and libraries |
| evidence | strong | Matches detailed CV project evidence |
| structure | strong | Organized by architectural components |

### Expected Feedback Points
- Praise for matching CV claims with technical details
- Highlight specific technical choices mentioned
- Note comprehensive coverage of backend concerns
- Could probe about scalability limits or future improvements

## Guardrail Checks
- Questions should probe the specific claims in CV
- `risk_if_user_cannot_answer` should reflect strong evidence
- Answer outlines can be detailed given the strong project evidence
- No fabrication of unmentioned technologies
