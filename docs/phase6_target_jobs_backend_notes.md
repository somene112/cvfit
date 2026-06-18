# Phase 6 Target Jobs — Backend Implementation Notes

> **PR:** 67 (`feat: add target jobs backend foundation`)
> **Date:** 2026-06-18
> **Scope:** Backend foundation only. No frontend UI; no other Phase 6 modules.

## Architecture decision

Target Jobs **reuse the existing `applications` table** as a Phase 6 product layer
rather than introducing a duplicate `target_jobs` table. The Phase 5 `Application`
model already carries job title, company, JD text, target role, status, and the
`best_analysis_job_id` relation — close enough that a parallel table would only
duplicate Phase 5 concepts and complicate ownership/readiness/package reuse.

The route/service/schema layer lives alongside (not on top of) the Phase 5
applications route, which is left **untouched**:

- `app/api/routes/target_jobs.py` — router (`/v1/target-jobs`)
- `app/schemas/target_jobs.py` — request/response schemas
- `app/services/target_jobs/` — shared readiness derivation

## Migration decision

One small **additive** migration: `20260618_0001_extend_applications_for_target_jobs`.

- New nullable columns on `applications`: `source_url`, `last_readiness_score`,
  `archived_at`.
- New `application_status` enum values: `saved`, `interviewing`, `rejected`, `offer`
  (added via `ALTER TYPE ... ADD VALUE` inside an autocommit block, PostgreSQL only).
- Phase 5 statuses and rows are preserved. `downgrade()` drops the new columns;
  enum values are intentionally left in place (PostgreSQL cannot drop enum values),
  which is safe because they are additive and unused by Phase 5.
- `EXPECTED_ALEMBIC_HEAD` updated to `20260618_0001` (single linear head).

## Endpoints

All require auth and are scoped by `user_id`; cross-user access returns **404**.

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/v1/target-jobs` | Create (default status `saved`). |
| GET | `/v1/target-jobs` | List own jobs, newest first; optional `?status=` filter. |
| GET | `/v1/target-jobs/{id}` | Get own job. |
| PATCH | `/v1/target-jobs/{id}` | Update safe fields + status (validated). |
| DELETE | `/v1/target-jobs/{id}` | **Soft-archive** (sets `archived_at`, preserves row). |
| POST | `/v1/target-jobs/{id}/attach-analysis/{analysis_job_id}` | Attach own analysis; caches `last_readiness_score`. |
| GET | `/v1/target-jobs/{id}/readiness` | Derived readiness; safe `not_started` payload when none. |
| GET | `/v1/target-jobs/{id}/package` | Latest package artifact; safe `has_package: false` payload when none. |

## Ownership / privacy behavior

- Cross-user job or analysis → 404 (never reveals existence), matching Phase 5.
- Readiness is **derived** from the attached analysis result only — no invented scores.
- No logging or `print` in the new code; no raw CV/JD/answer text, tokens, or secrets
  are logged or returned.

## Feature flag

`ENABLE_PHASE6_TARGET_JOBS` (default `true`) gates the router via a dependency;
when disabled, all `/v1/target-jobs` routes return 404.

## Known limitations / deferred

- List includes archived jobs by default (consistent with the Phase 5 applications
  list); clients filter via `?status=`.
- `last_readiness_score` is cached on attach; it is not recomputed on every read.
- Frontend `/jobs` UI is deferred to a later PR (Quân).
- Learning, Interview v2, Help Assistant, Share Links, and Usage remain out of scope.
