# Expected Behavior — Interview Practice Case IP2_11: Behavioral — Communication Skills

## Case Context
This case evaluates interview prep for a candidate with strong communication evidence through technical blog and meetup speaking. The JD mentions documentation and collaboration.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `behavioral` questions about technical communication
  - Question about explaining complex technical concepts
  - Question about documentation practices
  - `related_cv_evidence` should reference: "Published 20+ articles on Python best practices"
  - `related_cv_evidence` should reference: "Presented 'Building Scalable APIs with FastAPI' to 80+ attendees"
  - `related_jd_requirement` should reference: "Technical documentation skills"

- Questions connecting communication to technical work

#### Must NOT Include
- Questions assuming poor communication skills
- Questions requiring management experience

### Question Structure
```
type: behavioral
question: non-empty string
related_cv_evidence: list referencing communication evidence
related_jd_requirement: non-empty string (documentation/collaboration)
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer about documentation:
- Describes specific documentation practices (tutorials, references, diagrams)
- Mentions concrete tools (OpenAPI/Swagger)
- Provides quantifiable impact (40% reduction in support tickets)
- Shows understanding of developer experience

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses documentation requirement |
| specificity | strong | Names specific tools and approaches |
| evidence | strong | References communication work from CV |
| structure | strong | Organized with tools, techniques, and results |

### Expected Feedback Points
- Praise for quantifiable documentation impact
- Highlight specific tools and techniques mentioned
- Note connection to technical blog and speaking experience
- Suggest how these skills benefit team collaboration

## Guardrail Checks
- Questions should validate communication experience
- Questions must not dismiss non-traditional communication evidence
- Answer outlines should reflect communication expertise
