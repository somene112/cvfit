# Expected Behavior — Interview Practice Case IP2_14: Irrelevant Answer to Technical Question

## Case Context
This case evaluates feedback for a user who provides an irrelevant answer to a FastAPI backend question. The answer discusses frontend/React experience which doesn't match the JD.

## Expected Feedback Format

### Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | weak | Answer discusses frontend, not backend requirements |
| specificity | weak | No specific backend technologies mentioned |
| evidence | not_applicable | Frontend experience not relevant to FastAPI JD |
| structure | weak | Answer doesn't address the question |

### Feedback Must Include
- Clear statement that the answer doesn't address the backend question
- Reference to JD requirements (FastAPI, PostgreSQL, Redis)
- Note that frontend skills, while valuable, don't demonstrate backend expertise
- Suggestion to focus on backend experience when answering backend questions
- Reference CV evidence (Flask) that could have been discussed instead

### Feedback Must NOT Include
- Praise for unrelated skills
- Fabrication of backend relevance
- Downplaying the importance of matching JD requirements

## Guardrail Checks
- Feedback must clearly flag irrelevance
- Feedback must reference CV and JD evidence
- Feedback must provide constructive guidance
- No fabrication of experience or relevance
