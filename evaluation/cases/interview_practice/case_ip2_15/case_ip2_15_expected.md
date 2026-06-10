# Expected Behavior — Interview Practice Case IP2_15: Too Vague Answer

## Case Context
This case evaluates feedback for a user who provides an extremely vague answer with no specific details.

## Expected Feedback Format

### Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | cannot_assess | No specific skills mentioned to evaluate |
| specificity | weak | No concrete details about Python usage |
| evidence | weak | No project evidence from CV to reference |
| structure | weak | Single vague paragraph |

### Feedback Must Include
- Clear statement that answer lacks specificity
- Reference to JD requirements (FastAPI, PostgreSQL, REST API)
- Suggestion to add concrete examples from CV
- Note that "knowing Python" without context doesn't demonstrate proficiency
- Guidance on what specific details would strengthen the answer

### Feedback Must NOT Include
- Fabricated details or experience
- Praise for vague answers
- False encouragement about matching requirements

## Guardrail Checks
- Feedback must flag vagueness clearly
- Feedback must reference CV/JD evidence
- Feedback must provide constructive suggestions
- No fabrication of experience
