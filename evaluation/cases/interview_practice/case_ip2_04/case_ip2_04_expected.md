# Expected Behavior — Interview Practice Case IP2_04: Technical Question — SQL Expertise

## Case Context
This case evaluates interview prep for a database-focused developer with strong SQL expertise. The user provides a detailed answer about PostgreSQL optimization.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `project_deep_dive` question about the ERP database design
  - Must reference PostgreSQL and query optimization from CV
  - Must reference database design from JD
  - `related_cv_evidence` should reference: "Optimized slow queries reducing execution time by 80%"

- Technical questions about PostgreSQL optimization techniques
  - Indexing strategies (B-tree, partial indexes)
  - Query analysis using EXPLAIN ANALYZE
  - Monitoring with pg_stat_statements

- Questions about database design principles (normalization, transactions)

#### Must NOT Include
- Questions about FastAPI/web frameworks (not in CV)
- Questions about AWS/cloud services (not mentioned)

### Question Structure
```
type: project_deep_dive | technical_concept
question: non-empty string
related_cv_evidence: list of relevant CV evidence
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer about query optimization:
- Mentions specific PostgreSQL tools (EXPLAIN ANALYZE, pg_stat_statements)
- Describes concrete optimization techniques (B-tree indexes, partial indexes)
- Provides specific metrics (45 seconds to 500ms)
- Shows proactive monitoring approach
- Directly matches JD requirement for query optimization

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses database optimization requirement |
| specificity | strong | Names specific techniques and tools |
| evidence | strong | Reflects database work from CV |
| structure | strong | Problem-solution-results format |

### Expected Feedback Points
- Praise for using PostgreSQL-specific tools
- Highlight quantifiable improvements
- Note connection to ERP system experience
- Could probe about transaction handling or concurrent access

## Guardrail Checks
- Questions should focus on database expertise (candidate's strength)
- Questions should not require web framework experience
- Answer outlines should reflect database specialist level
