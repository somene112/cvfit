# Expected Behavior — Interview Practice Case IP2_01: Technical Question — Strong Answer (CS Student)

## Case Context
This case evaluates interview prep generation for a CS student with strong academic projects but no industry internship experience. The user provides a detailed answer about their Algorithm Visualizer project.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- At least 1 `project_deep_dive` question about the Algorithm Visualizer project
  - Must reference Python/Pygame from CV
  - Must reference algorithms knowledge from JD
  - `related_cv_evidence` should reference: "Implemented sorting algorithms (QuickSort, MergeSort, HeapSort) with step-by-step visualization"
  - `why_this_question` should explain the relevance of probing algorithm knowledge
  - `risk_if_user_cannot_answer` should reflect risk of weak industry experience

- Technical questions appropriate for entry-level CS student
  - Questions about time complexity, data structures used
  - Questions about the Flask E-Commerce prototype (relevant backend experience)

#### Must NOT Include
- Questions requiring years of industry experience
- Questions about AWS, Kubernetes, production deployment (not in CV)
- Questions fabricating internship experience

### Question Structure (per question)
```
type: project_deep_dive | technical_concept | behavioral
question: non-empty string
related_cv_evidence: list of relevant CV evidence (can be empty for gap_probe)
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: non-empty object
```

## User Answer Evaluation

### Answer Analysis
The user answer about the Algorithm Visualizer project:
- References QuickSort, MergeSort, HeapSort (matching CV)
- Mentions O(n log n) complexity (matching JD requirement)
- Shows practical understanding of algorithms

### Expected Rubric Scores (Conceptual)
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Answer directly addresses algorithm knowledge required by JD |
| specificity | strong | Names specific algorithms and complexity analysis |
| evidence | strong | References concrete project from CV |
| structure | strong | Logical flow from implementation to optimization |

### Expected Feedback Points
- Highlight strong understanding of algorithm complexity
- Note connection between academic project and JD requirements
- Acknowledge no industry experience honestly
- Suggest ways to bridge academic-to-industry gap

## Guardrail Checks
- Questions must NOT fabricate internship experience
- Questions must NOT ask about production-scale systems
- Answer outlines must reflect entry-level expectations
- Feedback must be encouraging but honest about experience level
