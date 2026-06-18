# Phase 6 Help Assistant & Shareable Readiness — Backend Notes

> **PR:** Week 3 bundle (`feat: add help assistant and shareable readiness backend`)
> **Date:** 2026-06-20
> **Scope:** Backend only. No frontend UI; no Usage shell; no payment/recruiter portal.

## Help Assistant / Career Coach v1

- **Endpoints:** `POST /v1/help/assistant`, `GET /v1/help/suggestions`. Flag `ENABLE_PHASE6_HELP_ASSISTANT` (default **true**); 404 when disabled.
- **Guided, not free-form.** `intent` is a fixed `Literal`; unsupported intents → 422. Supported:
  `next_best_action`, `explain_score`, `explain_gap`, `suggest_learning`,
  `suggest_interview_practice`, `explain_application_status`, `help_product_usage`.
- **Data sources:** only the caller's own target jobs/applications, attached analysis + derived
  readiness, learning tasks, and interview sessions. Every referenced id is ownership-checked
  (cross-user → 404).
- **No new table.** Pure deterministic service over existing data.
- **Fallback:** when context is insufficient, returns `fallback_used: true` and
  "I cannot determine this from your current data."
- **Guardrails:** never predicts salary/job-market facts, never guarantees hiring/interview
  outcomes, and never echoes raw CV/JD text, tokens, or secrets. `recommended_actions` are a fixed
  set of product actions (e.g. `open_learning`, `start_interview`, `view_readiness`).

## Shareable Readiness / Recruiter-lite

- **Endpoints:** `POST/GET /v1/share-links`, `GET/PATCH/DELETE /v1/share-links/{id}`,
  and public `GET /v1/public/share/{token}`. Flag `ENABLE_PHASE6_SHARE_LINKS` (default **false**
  until privacy review passes); every route (including public) returns 404 when disabled.
- **New table `share_links`** (migration `20260620_0001`). `target_type` ∈ {`target_job`,
  `application`}, both resolving to an owned `Application` row.
- **Token rules (mirrors the existing access-token pattern in `jobs.py`):**
  - Raw token = `secrets.token_urlsafe(32)`; stored value = `sha256` hex in `token_hash`.
  - Raw token is **returned once** on create (with a relative `public_path`) and **never** stored,
    logged, or echoed again. `token_hash` is **never** exposed in any response.
  - Public lookup hashes the incoming token and compares with `hmac.compare_digest`.
- **Revoke/expiry:** DELETE is a **soft revoke** (sets `revoked_at`, row preserved). Revoked,
  expired, or unknown tokens all return an indistinguishable **404**.
- **Public redaction (default):** returns job title, company, readiness level, and summary only.
  Raw CV/JD text is never included. `fit_score`/`score_breakdown` appear only when
  `include_score_breakdown` is set; `learning_focus` only when `include_learning_roadmap` is set.
  `hide_raw_cv`/`hide_raw_jd` default true.

## Migration

- `20260620_0001_add_share_links` — additive `CREATE TABLE share_links` + indexes
  (`user_id`, `(target_type,target_id)`, unique `token_hash`, `revoked_at`, `expires_at`).
- `down_revision = 20260619_0001`; `EXPECTED_ALEMBIC_HEAD` → `20260620_0001` (single linear head).
- No existing table altered → fully backward compatible.

## Analytics / logging privacy

Never send to analytics or logs: raw CV text, raw JD text, interview answer text, JWTs,
**raw share tokens**, `token_hash`, private IDs, or secrets.

## Known limitations / deferred

- Frontend `/help/assistant` and `/share/[token]` UIs deferred to Quân.
- Share links stay flag-off until Đạt's privacy review passes.
- Usage shell, payment, and recruiter portal remain out of scope.
