# Phase 6 Backend Closeout

> **Date:** 2026-06-19
> Status of the Phase 6 backend after the Week 4 bundle.

## Merged backend modules

| Module | Endpoints | Flag (default) | GitHub PR |
|--------|-----------|----------------|-----------|
| Target Jobs | `/v1/target-jobs/*` (8) | `ENABLE_PHASE6_TARGET_JOBS` (on) | #68 |
| Learning Roadmap | `/v1/learning/*`, `/v1/target-jobs/{id}/learning/generate` (5) | `ENABLE_PHASE6_LEARNING` (on) | #69 |
| Interview Practice v2 | `/v1/interview/sessions/*` (7) | `ENABLE_PHASE6_INTERVIEW_V2` (on) | #69 |
| Help Assistant | `/v1/help/*` (2) | `ENABLE_PHASE6_HELP_ASSISTANT` (on) | #70 |
| Shareable Readiness | `/v1/share-links/*`, `/v1/public/share/{token}` (6) | `ENABLE_PHASE6_SHARE_LINKS` (**off**) | #70 |
| Usage / Plan shell | `/v1/usage/me`, `/v1/plans` (2) | `ENABLE_PHASE6_USAGE_SHELL` (on) | #71 |

> **Status:** All six modules are **merged on `main`** (commit `a1aa4ca`). Backend is closeout-ready.
> Frontend (Quân), privacy/analytics/QA sign-off (Đạt), and the deployed Render rollout remain.
> See [phase6_deployed_e2e_execution_report.md](phase6_deployed_e2e_execution_report.md) for the
> deployed smoke result.

## Migrations

| Revision | Adds |
|----------|------|
| `20260618_0001` | Target Jobs columns + enum values on `applications` |
| `20260619_0001` | `learning_tasks`, `interview_sessions`, `interview_session_questions`, `interview_session_answers` |
| `20260620_0001` | `share_links` (token hash only) |

- **Current head: `20260620_0001`.** The Usage shell adds **no migration** (usage is computed).
- All migrations are additive and backward compatible; Phase 5 tables/flows untouched.

## Tests

- Per-module ownership/guardrail tests: target jobs, learning, interview v2, help assistant,
  share links, usage. Cross-user access returns 404 throughout.
- Backend Checks + PostgreSQL Migration Checks green on each merged PR.

## Privacy posture

- No raw CV/JD/answer text, JWTs, share tokens, or `token_hash` in responses or logs.
- Share links store only the SHA-256 token hash; raw token returned once on create.
- Usage shell is read-only counts + static copy — no payment/checkout/enforcement.

## Known deferred / remaining work

- **Quân (frontend):** `/jobs`, `/learning`, `/interview/sessions`, `/help/assistant`,
  `/share/[token]`, `/usage` UIs; GA4 event wiring per the analytics event plan.
- **Đạt (QA/privacy):** share-links privacy review (gates flipping `ENABLE_PHASE6_SHARE_LINKS`
  on); analytics no-PII verification; deployed E2E execution report.
- **Share Links stay flag-off** until the privacy review passes.

## Deployment requirement

- Render must run `alembic upgrade head` (to `20260620_0001`) **before** booting new app code —
  `init_db()` enforces the expected head and refuses to start otherwise.
