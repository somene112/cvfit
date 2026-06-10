# Expected Behavior — Interview Practice Case IP2_05: Technical Question — Cloud Infrastructure

## Case Context
This case evaluates interview prep for a DevOps engineer with strong cloud and containerization experience. The user provides a detailed answer about Kubernetes deployment.

## Expected Interview Prep Output

### Questions Generated
The `build_interview_prep` function should generate questions that:

#### Must Include
- `project_deep_dive` question about the AWS EKS implementation
  - Must reference Kubernetes, AWS EKS from CV
  - Must reference container orchestration from JD
  - `related_cv_evidence` should reference: "Built Kubernetes clusters on AWS EKS for microservice deployments"

- Technical questions about AWS services (ECS, RDS, S3, Lambda)
- Questions about CI/CD pipelines and GitHub Actions
- Questions about Terraform and Infrastructure as Code

#### Must NOT Include
- Questions about Python web frameworks (Flask, FastAPI)
- Questions about frontend technologies

### Question Structure
```
type: project_deep_dive | technical_concept | system_design
question: non-empty string
related_cv_evidence: list of relevant CV evidence
related_jd_requirement: non-empty string
why_this_question: non-empty string
risk_if_user_cannot_answer: non-empty string
suggested_answer_outline: object
```

## User Answer Evaluation

### Answer Analysis
The user answer about Kubernetes deployment:
- Demonstrates deep knowledge of EKS cluster design
- Mentions specific Kubernetes features (HPA, pod disruption budgets, topology spread)
- Shows production-grade considerations (high availability, resource management)
- References AWS services integration (Secrets Manager, CSI driver)
- Directly matches JD requirement for Kubernetes and AWS expertise

### Expected Rubric Scores
| Dimension | Score | Justification |
|-----------|-------|---------------|
| relevance | strong | Directly addresses container orchestration requirement |
| specificity | strong | Names specific Kubernetes features and configurations |
| evidence | strong | Reflects EKS work from CV |
| structure | strong | Comprehensive coverage of deployment considerations |

### Expected Feedback Points
- Praise for production-grade approach
- Highlight specific Kubernetes features mentioned
- Note connection to AWS infrastructure experience
- Could probe about failure scenarios or cost optimization

## Guardrail Checks
- Questions should focus on DevOps/Cloud expertise (candidate's strength)
- Questions should not require web application development experience
- Answer outlines should reflect DevOps engineer level
