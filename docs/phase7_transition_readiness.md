# Phase 7 Transition Readiness

Status snapshot after PR #87 (Admin Monitoring + Vietnamese demo flow), PR #88
(Admin Analytics v2), and the Priority 2 demo-hardening PR
(`fix/demo-flow-priority-2`).

> Payment is **not** live. Real rollout remains paused.

## What is now ready

- **Admin Monitoring** works (`/admin`, `/v1/admin/me|overview|recent-activity`):
  read-only, aggregate-only, privacy-safe.
- **Admin Analytics v2** works: product funnel, conversion rates, 7/30-day
  activity, analysis health, engagement depth, and billing readiness — all
  derived from PostgreSQL (no GA4), with zero-denominator safety.
- **Vietnamese-first demo flow** works end to end: login → CV analysis →
  result/history → interview practice → applications (cover letter / package) →
  usage/billing/pricing → help → admin. UI is Vietnamese; demo-flow generated
  content is Vietnamese when `language=vi`.
- **Priority 2 demo bugs fixed**: interview session detail renders backend
  `question_text`/feedback correctly (and auto-generates questions); the package
  page renders `readiness_summary`; the help page uses the real
  `/v1/help/assistant` + `/v1/help/suggestions` endpoints; cover-letter edits
  persist (free, ungated, owner-scoped).
- **Google Login** production is done.
- **Payment MVP code** is implemented through controlled-rollout readiness
  (checkout, payOS webhook + credit granting, credit gating, billing/pricing UI),
  behind flags.

## What remains paused / off

- `ENABLE_BILLING = false`
- `ENABLE_CREDIT_GATING = false`
- `ENABLE_PHASE6_SHARE_LINKS = false`
- No real or sandbox payOS payment has been executed in this work.
- No Render environment / production flags changed.

## Remaining Phase 7 work (next steps)

1. **Controlled payment enablement** — enable `ENABLE_BILLING` (and later
   `ENABLE_CREDIT_GATING`) for a limited cohort in a non-production/staging env
   first, gated and reversible.
2. **Real/sandbox payment QA** — exercise the payOS sandbox checkout → webhook →
   credit-grant path against the existing QA checklist; verify idempotency and
   the manual-review path.
3. **Optional UX polish** — minor demo-flow refinements (e.g., persisting prior
   interview answers across reloads; package readiness empty states).
4. **Optional admin analytics expansion** — time-series charts, cohort/retention
   views (kept out of the MVP).
5. **Optional GA4 future tracking** — once GA4 has accumulated history, correlate
   it with the PostgreSQL-derived metrics (DB metrics remain the source of truth
   for now).

## Recommended next human action

Review and merge the Priority 2 PR, then schedule a **staging** controlled
payment-enablement test (step 1 + 2). Do not enable billing in production until
sandbox QA passes.
