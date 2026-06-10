# Expected Behavior — Interview Practice Case IP2_16: Answer References Non-Existent Project

## Case Context
This case evaluates feedback for a user who claims FastAPI experience that is not present in their CV. The CV only mentions Flask, but the answer discusses extensive FastAPI work.

## Expected Feedback Format

### Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Addresses FastAPI requirement from JD |
| specificity | strong | Names specific FastAPI features |
| evidence | fabrication_risk | No FastAPI in CV - potential fabrication |
| structure | strong | Well-structured technical description |

### Red Flags
- CV lists Flask experience, not FastAPI
- No mention of FastAPI projects in CV
- Discrepancy between CV evidence and answer claims

### Feedback Must Include
- Clear flagging of potential fabrication
- Reference to CV evidence (Flask, not FastAPI)
- Request for clarification about FastAPI experience
- Note that if experience is real, it should be added to CV
- Warning about fabrication risk in interviews
- Suggestion to update CV with actual experience

### Feedback Must NOT Include
- Assuming fabrication is intentional
- Dismissing the candidate
- Fabricating FastAPI experience

## Guardrail Checks
- Feedback must flag discrepancy clearly
- Feedback must reference CV evidence
- Feedback must acknowledge Flask experience as relevant
- Feedback must not fabricate experience
- Feedback should be firm but constructive
