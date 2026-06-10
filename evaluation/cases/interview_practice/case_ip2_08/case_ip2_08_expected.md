# Expected Behavior — Interview Practice Case IP2_08: Project Deep-Dive — Multiple Projects

## Case Context
This case evaluates interview prep for a developer with multiple strong projects covering different domains. The user focuses on one project but has evidence for others.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- Multiple `project_deep_dive` questions, one for each significant project
  - At least 1 question about E-Commerce Product API (FastAPI, Redis, PostgreSQL)
  - At least 1 question about Analytics Dashboard (Flask, ETL, data warehousing)
  - At least 1 question about Auth Microservice (JWT, OAuth2, microservices)

- Each question must reference the relevant project evidence from CV
- Questions should cover different technical aspects (API design, data pipelines, auth)

#### Must NOT Include
- Questions mixing up details from different projects
- Questions about skills not present in any CV project

### Question Structure
```
type: project_deep_dive
question: non-empty string
related_cv_evidence: list referencing specific project from CV
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer focuses on the E-Commerce API:
- Discusses CQRS pattern, caching strategy, deployment
- Matches CV evidence for E-Commerce project
- Shows architectural thinking
- Does not address other projects (Analytics Dashboard, Auth Microservice)

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Addresses API and architecture requirements |
| specificity | strong | Mentions CQRS, caching, transactions |
| evidence | strong | Matches E-Commerce project from CV |
| structure | moderate | Well-structured but only covers one project |

### Expected Feedback Points
- Praise for architectural depth on E-Commerce API
- Note that other projects could be discussed
- Suggest exploring Analytics or Auth projects for breadth
- Reference other JD requirements (microservices architecture)

## Guardrail Checks
- Questions should cover multiple projects, not just one
- Each project should have relevant questions
- No fabrication of project details across projects
