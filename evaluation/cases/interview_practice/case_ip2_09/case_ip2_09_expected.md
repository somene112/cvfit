# Expected Behavior — Interview Practice Case IP2_09: Project Deep-Dive — No Industry Projects

## Case Context
This case evaluates interview prep for a fresh graduate with only academic projects. Questions should focus on coursework and class projects without fabricating industry experience.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `project_deep_dive` questions about academic projects (Library Management, Quiz App)
  - Must clearly reference these as coursework projects
  - `why_this_question` should acknowledge academic nature
  - `risk_if_user_cannot_answer` should be moderate, reflecting academic experience

- Questions about algorithm problem-solving (LeetCode practice)
  - Can probe technical skills without requiring industry experience

- Questions acknowledging the entry-level nature

#### Must NOT Include
- Questions requiring production-scale experience
- Questions about enterprise tools (Kubernetes, AWS production)
- Questions fabricating internship or industry experience

### Question Structure
```
type: project_deep_dive | technical_concept | behavioral
question: non-empty string
related_cv_evidence: list referencing academic projects
related_jd_requirement: non-empty string
why_this_question: non-empty string (must acknowledge academic context)
risk_if_user_cannot_answer: non-empty string (moderate risk acceptable)
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer:
- Discusses both Library Management System and Quiz Application
- Shows understanding of database design principles
- Mentions Flask, SQLite, CRUD operations
- Demonstrates basic backend development concepts

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | moderate | Addresses database and API topics from JD |
| specificity | moderate | Shows understanding but limited depth |
| evidence | moderate | Academic projects are valid evidence |
| structure | strong | Organized by project with clear explanations |

### Expected Feedback Points
- Acknowledge academic projects as valid starting point
- Note connection between coursework and JD requirements
- Suggest ways to expand academic projects for portfolio
- Provide encouraging but realistic expectations

## Guardrail Checks
- Questions must NOT fabricate industry experience
- Questions must acknowledge academic nature of experience
- Answer outlines should be appropriate for entry-level
- Feedback should be encouraging while honest about gaps
