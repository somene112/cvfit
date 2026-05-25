# Product Roadmap

This roadmap starts from the Phase 0 final baseline and keeps deployment, product polish, scoring quality, privacy, AI features, and production hardening separated into clear phases.

## Phase 1: MVP Deploy And Team Foundation

Phase 1A completed: the Render MVP deployment smoke test passed against the deployed API, worker, Redis/Postgres, and S3-backed storage. This confirms demo deployment viability only; it is not production readiness.

Phase 1B completed: the access-token MVP passed local and Render smoke tests. Result, report metadata, and report download endpoints now require the per-job access token. Full auth and user accounts remain future work.

Phase 1C / Phase 1.3 migration adoption completed on 2026-05-23: Alembic has been added for the current schema, the initial migration has been validated against disposable local PostgreSQL/pgvector databases, and the existing Render database passed the schema checker before the safe adoption helper stamped it to head. Sanitized closeout evidence: schema checker passed, adoption helper completed `stamp`, and `alembic current` returned `20260522_0001 (head)`.

Phase 1D / Phase 1.4 runtime hardening makes Alembic the intentional schema-management path. API and worker startup verify the schema and Alembic revision instead of silently creating tables or patching columns.

### Goals

- Deploy the current MVP safely to Render.
- Establish team ownership and repeatable smoke-test workflow.
- Add the smallest access-control and database foundation needed before demo use.

### Deliverables

- Render Web Service and Background Worker configured from documented environment variables.
- Render Redis/Key Value and Postgres connected.
- S3-compatible storage configured for both API and worker.
- S3-backed smoke test run against the deployed environment.
- Access-token MVP for protecting job/result/report URLs.
- Alembic baseline migration.
- Updated deployment, smoke-test, and team handoff docs.

### Definition Of Done

- Deployed API health check passes.
- Upload to result to report download flow passes in Render.
- No secrets are committed.
- API and worker use the same storage/database/Redis configuration.
- Team can run local tests and smoke tests from README instructions.

## Phase 2: Product MVP Polish

### Goals

- Make the current workflow easier to understand and safer for demo users.
- Improve frontend loading, failure, result, and report-download experience.

### Deliverables

- Clear upload/JD input states.
- Loading and progress states for queued/running jobs.
- User-friendly failed-job messages.
- Result dashboard with score breakdown and matched/missing skills.
- Report download state and retry behavior.
- Responsive layout pass for common laptop and mobile widths.

### Definition Of Done

- A first-time user can complete the flow without developer guidance.
- All expected API errors have visible UI states.
- Result and report download UX work after page refresh.
- Frontend smoke checklist passes in local Docker and deployed MVP.

## Phase 3: Scoring Quality And Explainability

### Goals

- Improve trust in fit scores without adding unsupported claims.
- Make scoring explainable and grounded in parsed CV/JD evidence.

### Deliverables

- Scoring test fixtures for representative CV/JD pairs.
- Clear score component definitions.
- Evidence-backed matched and missing skill explanations.
- Deterministic regression tests for scoring changes.
- Basic calibration notes for interpreting fit score ranges.

### Definition Of Done

- Score changes are covered by tests.
- Result output explains why the score was assigned.
- Feedback is grounded in parsed CV/JD text, not invented details.
- Product can distinguish low, medium, and high fit examples reliably.

## Phase 4: Account, History, And Privacy

### Goals

- Add user/account concepts and basic history while respecting CV privacy.
- Define retention and deletion behavior for uploaded files and reports.

### Deliverables

- User model and login flow or invite/access-code flow.
- Per-user analysis history.
- Delete-analysis flow that removes DB rows and storage objects.
- Retention policy documentation.
- Privacy copy for CV uploads and report storage.

### Definition Of Done

- Users cannot access other users' jobs by guessing UUIDs.
- Users can view and delete their own history.
- Storage cleanup is tested.
- Privacy and retention behavior is documented.

## Phase 5: AI Assistant Features

### Goals

- Add LLM-powered assistance only after the deterministic baseline is trustworthy.
- Keep AI output grounded in CV/JD evidence.

### Deliverables

- AI feedback service behind a feature flag.
- Prompt templates with evidence inputs.
- Guardrails against unsupported claims.
- Tests or golden examples for AI response shape.
- Cost and latency monitoring notes.

### Definition Of Done

- AI output never replaces the deterministic score.
- AI feedback references evidence from parsed CV/JD data.
- Feature can be disabled without breaking core flow.
- Cost and provider configuration are documented.

## Phase 6: Production Scale, Security, And Monitoring

### Goals

- Prepare for production-grade reliability, observability, and security.
- Move beyond MVP deployment assumptions.

### Deliverables

- Production infrastructure plan for AWS App Runner/ECS, RDS, S3, Redis/ElastiCache, and CloudWatch.
- CI/CD workflow with tests and image build checks.
- Structured logs, metrics, and alerting.
- Backup and restore verification for database and storage.
- Container hardening and non-root runtime.
- Rate limiting and abuse controls.

### Definition Of Done

- Production deployment has documented rollback and recovery paths.
- Logs and metrics can diagnose API, worker, Redis, DB, and storage failures.
- Security review items are tracked and resolved.
- Backups and retention policies are tested.
