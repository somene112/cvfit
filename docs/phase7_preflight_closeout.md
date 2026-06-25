# Phase 7 Preflight Closeout

Pre-Phase-7 readiness audit. Payment rollout is **paused** — this document does
not enable billing or perform any payment.

## 1. Current main commit

- `9aa1856` — Merge pull request #89 (`fix/demo-flow-priority-2`), containing
  `58cd67a fix: harden demo flow before phase 7`.
- Working tree clean at audit time. No new migration required (none added).
- Payment flags remain default false: `ENABLE_BILLING=false`,
  `ENABLE_CREDIT_GATING=false`.

## 2. Merged PRs on main

- **PR #87** — Admin Monitoring MVP + Vietnamese demo flow (`b04087f`).
- **PR #88** — Admin Analytics v2 (`f42fb61`).
- **PR #89** — Priority 2 Demo Hardening (`58cd67a` via merge `9aa1856`).

## 3. What PR #89 fixed

- **Interview detail empty/undefined** — auto-generate Vietnamese questions on
  first open; normalize backend `question_text → text` and `score`/`feedback`
  (rubric scaled 0-5 → 0-10).
- **Package `readiness_summary` mismatch** — read
  `payload.readiness_summary.{summary,fit_score,readiness_level,next_actions}`;
  safe fit-score formatting.
- **Help endpoint mismatch** — use `GET /v1/help/suggestions` +
  `POST /v1/help/assistant` (intent-based) instead of the non-existent
  `/v1/help/ask`. Only owned-object IDs sent as context; no raw CV/JD/answer text.
- **Cover-letter save** — persist JSONB via `flag_modified` (free, ungated,
  owner-scoped, no extra artifact); NFC-normalize generated + saved Vietnamese
  text (fixes broken diacritics); Vietnamese-safe editor font.
- **Learning "Not Found"** — fix API paths `/v1/learning` → `/v1/learning/tasks`;
  a 404 now shows the Vietnamese empty-state CTA.
- **Pricing/Billing English plan names** — `plan_code` → Vietnamese mapping
  (`starter_pack` → "Gói khởi đầu", `pro_demo_pack` → "Gói demo Pro"); prices and
  payment authority unchanged.

## 4. Local validation results (this audit)

| Check | Result |
| --- | --- |
| `python -m compileall backend/app` | ✅ exit 0 |
| `test_cover_letter_save_edits.py` | ✅ |
| `test_phase5_package_cover_letter.py` | ✅ |
| `test_phase6_interview_sessions.py` | ✅ |
| `test_phase6_help_assistant.py` | ✅ |
| `test_phase5_applications_profile.py` | ✅ |
| `test_vietnamese_generation.py` | ✅ |
| `test_admin_overview.py` | ✅ |
| Combined targeted suites | ✅ **152 passed** |
| `npm run lint` | ✅ clean (pre-existing font warning only) |
| `npm run build` | ✅ 25/25 pages |
| Privacy/security grep (changed files) | ✅ no secrets; only the pre-existing pricing `checkout_url` redirect |

> CI on PRs #87/#88/#89 was green (Backend Checks + PostgreSQL Migration Checks).
> Locally, the full suite needs `python-docx`, `sentence_transformers`,
> `passlib`/`bcrypt`, and `alembic`; those are present in CI (source of truth).

## 5. Production deploy requirement

Public checks (unauthenticated) at audit time:

- `GET https://cvfit.onrender.com/health` → **200** `{"status":"ok"}`
- `GET https://cvfit-frontend.onrender.com/` `/admin` `/pricing` `/learning`
  `/help` `/help/assistant` → all **200** (page shells served).

Production is **reachable and serving**, but these client-rendered pages do not
expose the deployed commit, so we **cannot confirm production is on latest main
(PR #89)** from public checks alone.

**Operator action (do NOT mutate Render env automatically):**

1. Deploy backend latest `main` on Render.
2. Deploy frontend latest `main` on Render.
3. Keep `ENABLE_BILLING=false` and `ENABLE_CREDIT_GATING=false`.
4. Keep `ADMIN_EMAILS` set for the demo/admin account.

Then run the manual QA below — it will visibly confirm PR #89 is live (Vietnamese
plan names, interview questions render, cover-letter edits persist, learning shows
the empty-state CTA rather than "Not Found").

## 6. Manual QA checklist (summary)

Run on the deployed site after step 5. Full details in
`docs/vietnamese_demo_flow_qa.md`.

1. **Login** — normal demo user, and admin demo user.
2. **/admin** — Analytics v2 renders; no raw private content; billing "Chưa bật".
3. **Dashboard/result** — VI copy; cards + improvement render; no `undefined`.
4. **Interview** — create session → detail shows questions (no "undefined —
   undefined"), Vietnamese; submit a short answer → feedback (score/rubric/
   strengths/improvements) renders.
5. **Cover letter** — Vietnamese diacritics correct; edit a word → "Lưu thay đổi"
   → refresh → edit persists; no credit/payment required.
6. **Package** — readiness summary + fit score/level/next actions render; no
   `undefined`, no raw JSON.
7. **Learning** — `/learning` shows no raw "Not Found"; empty → VI empty state +
   CTA; tasks → list renders.
8. **Help** — `/help/assistant` suggestions load; choose one → response renders;
   no raw CV/JD prompt required.
9. **Pricing/Billing** — `/pricing` shows "Gói khởi đầu" / "Gói demo Pro" at
   **20.000đ** / **49.000đ**; `/billing` safe state; not live.
10. **Payment flags** — production backend still `ENABLE_BILLING=false`,
    `ENABLE_CREDIT_GATING=false`.

Items 1–9 are **not automatable** here (require auth + deployed runtime); item 10
is verified via Render env (operator).

## 7. Payment status

- `ENABLE_BILLING=false`
- `ENABLE_CREDIT_GATING=false`
- Real/sandbox payment **not live**. No payOS provider logic touched.

## 8. Remaining out of scope

- Real payOS rollout.
- Credit-gating live rollout.
- Full GA4 historical reconstruction.
- Enterprise admin analytics (charts/cohorts/retention).
- Old historical generated artifacts may remain English / non-NFC unless
  regenerated or re-saved (only newly generated/saved text is localized + NFC).

## 9. Verdict rules

- **READY_TO_START_PHASE_7** — only after local validation passes **and** the
  latest `main` is deployed **and** the deployed manual QA checklist (section 6)
  fully passes.
- **BLOCKED_BY_MANUAL_QA** — manual QA has not been completed, or a demo-critical
  QA item fails.
- **BLOCKED_BY_DEPLOY** — latest `main` (PR #89) is not confirmed deployed to
  production.
- **BLOCKED_BY_LOCAL_TESTS** — backend/frontend validation fails.

### Current state

- **Local validation: PASS** (section 4) → not `BLOCKED_BY_LOCAL_TESTS`.
- **Production: reachable**, but deploy-freshness vs latest `main` is
  **unconfirmed** from public checks (section 5).
- **Manual QA: pending** operator run on the deployed site (section 6).

**Verdict now:** the codebase/local level is READY, but Phase 7 is **not**
`READY_TO_START_PHASE_7` yet. Confirm/redeploy latest `main` (else
`BLOCKED_BY_DEPLOY`), then run the manual QA. Until manual QA passes, treat as
**BLOCKED_BY_MANUAL_QA**. Do not start Phase 7 payment rollout until this document
can be marked `READY_TO_START_PHASE_7`.
