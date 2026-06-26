# PHUC_RUNBOOK_READY

> **Status banner:** Phase 7A is in **demo-integrity blocker state** pending production deploy + retest. Phase 7B (controlled payment rollout) is **NOT** authorized to begin until every Phase 7A blocker is confirmed fixed on production and the Section 4 go/no-go criteria are met. Payment rollout flags remain `ENABLE_BILLING=false` and `ENABLE_CREDIT_GATING=false`.

This runbook is the operator-facing checklist for Phúc. It covers two phases:

- **Phase 7A** — Demo-integrity retest of latest `main` (PR #91 merged) on production.
- **Phase 7B** — Controlled payment rollout of the payOS credit-pack MVP.

It deliberately does **not** authorize code changes. The fix owner for the Section 6 blockers is Quân / the implementation PR; Phúc's role here is to document, deploy, retest, and only then sign off.

---

## 1. Current Status

The repository state at the time this runbook was written is:

- **PR #91 merged into `main`** at commit `7b93278` ("Merge pull request #91 from aumi102/fix/pre-phase7-learning-vietnamese-qa"). The merge contains the Learning + Vietnamese QA fixes that need to be retested on production.
- **Payment rollout is NOT started.** No `ENABLE_BILLING=true` and no `ENABLE_CREDIT_GATING=true` events have occurred on Render.
- Production Render environment continues to hold:
  - `ENABLE_BILLING=false`
  - `ENABLE_CREDIT_GATING=false`
- **Phase 7A demo-integrity blockers still need production confirmation** before Phase 7B can start. The two open blockers are:
  1. **Fake marketing metrics** on the public landing page must be removed or replaced with honest copy.
  2. **Learning detail status update** must be confirmed working on production after the PR #91 deploy.

  These are documented in detail in section 6.
- **Sections 4–8 of the manual QA previously looked acceptable** at the local validation stage (Help Assistant, Interview, Cover Letter, Application Package, Flags), but they **must be regression-checked after the latest deploy** to make sure PR #91 did not break anything that was already green.

---

## 2. Render Deploy Checklist

This is the first step of the retest. It is a deploy-and-verify checklist only; no env flags change here.

### 2.1 Backend

- [ ] Deploy latest `main` to the Render backend service.
- [ ] Confirm the deployed commit includes PR #91 (`7b93278`).
- [ ] Confirm the deployed commit includes any subsequent Phase 7A fix PR(s) for the Section 6 blockers, if such PR(s) have been merged by the time of deploy.
- [ ] **Keep `ENABLE_BILLING=false`.**
- [ ] **Keep `ENABLE_CREDIT_GATING=false`.**
- [ ] Confirm `GET https://cvfit.onrender.com/health` returns `200` with `{"status":"ok"}`.

### 2.2 Frontend

- [ ] Deploy latest `main` to the Render frontend service.
- [ ] Confirm the landing/stat area renders honestly (no fake metrics). If the fix has shipped, the "10,000+ CV đã phân tích" / "98% Độ chính xác AI" / "30s Thời gian phân tích" / "4.9★ Đánh giá người dùng" stats bar must no longer be presented as if they were real measurements.
- [ ] Confirm `/learning` behaves correctly after a fresh CV analysis (Vietnamese empty-state CTA, not a raw "Not Found", and tasks are generated and updatable).

---

## 3. Phase 7A Production Retest Checklist

Run every step in order. Each item is binary pass/fail. Do **not** skip sections 4–8 even if they passed locally; PR #91 changed the result/learning pipeline.

- [ ] Open the landing/public/dashboard area; confirm fake metrics are **gone or replaced with honest copy** (see Section 6 blocker a).
- [ ] Run a **fresh** CV analysis as the demo user.
- [ ] Confirm the generated Vietnamese result quality remains acceptable (summary, score labels, explanations, limitations, missing-skill reasons/suggestions, improvement actions, safe-rewrite suggestions, interview-prep questions, learning-roadmap text are Vietnamese; skill/tech/JD tokens stay untranslated).
- [ ] Open `/learning`.
- [ ] If the empty state is shown, generate tasks from the latest analysis using the Vietnamese CTA ("Tạo lộ trình học tập từ phân tích gần nhất").
- [ ] Open a task detail.
- [ ] Change the task status (e.g., from `todo` → `in_progress` → `done`).
- [ ] Confirm there is **no "Không thể cập nhật trạng thái."** error banner (see Section 6 blocker b).
- [ ] Refresh the page; confirm the new status persists.
- [ ] Confirm **Section 4 — Help Assistant** still works (`/help` suggestions load, choosing one returns a Vietnamese response, no raw CV/JD/answer text is required as input).
- [ ] Confirm **Section 5 — Interview** still works (create a session → detail shows Vietnamese questions, no "undefined — undefined"; submit a short answer → feedback/score/strengths/improvements render).
- [ ] Confirm **Section 6 — Cover Letter** still works (Vietnamese diacritics correct, edit → "Lưu thay đổi" → refresh → edit persists, no credit/payment required).
- [ ] Confirm **Section 7 — Application Package** still works (`readiness_summary`, fit score, readiness level, next actions render; no `undefined`, no raw JSON).
- [ ] Confirm **Section 8 — Flags** remain false (no privacy/quality/billing flags were raised by the regenerations above).

If any item fails, Phase 7A is **blocked**. Record the failure, route it to Quân as a follow-up implementation PR, and re-run this entire checklist after that PR is merged and deployed. Do **not** proceed to Section 4 with a failing item.

---

## 4. Go / No-Go Decision

Set the verdict to `READY_TO_START_PHASE_7_PAYMENT_ROLLOUT` **only** when **every** item below is true:

- [ ] **Fake metrics fixed** on the landing page and confirmed on production (blocker a in Section 6 is closed).
- [ ] **Learning status update fixed** on production (blocker b in Section 6 is closed; PATCH succeeds, status persists, no "Không thể cập nhật trạng thái." error).
- [ ] **Fresh analysis retest passes** (Section 3, steps 1–3 plus the Vietnamese result quality gate).
- [ ] **Sections 1–8 pass** the full Section 3 retest (landing + learning + analysis + help + interview + cover letter + package + flags).
- [ ] `ENABLE_BILLING=false` is still in place on Render before any rollout step begins.
- [ ] `ENABLE_CREDIT_GATING=false` is still in place on Render before any rollout step begins.
- [ ] No privacy / raw-content issue was observed during the retest (no raw CV/JD/answer/cover-letter/package text was leaked to logs, errors, or analytics).
- [ ] No payment / payOS code changed unexpectedly during the PR #91 deploy window (the diff between the last-known-good payment commit and current `main` touches no payment provider code paths).

If any of these is false, the verdict is `BLOCKED`. Phase 7B must not start. Update this runbook with the blocker, route the fix to the implementation owner, redeploy, and re-run the retest.

---

## 5. Phase 7B Controlled Payment Rollout Checklist

This section is the actual rollout plan once Section 4 returns `READY_TO_START_PHASE_7_PAYMENT_ROLLOUT`. The rollout is **three ordered windows**: billing-only, webhook verification, then credit gating. Do not collapse the windows; do not skip the rollback rehearsal in your head.

### 5.1 Billing-only window

- [ ] Set `ENABLE_BILLING=true` on the Render backend env.
- [ ] **Keep `ENABLE_CREDIT_GATING=false`** throughout this window.
- [ ] Redeploy the backend.
- [ ] Verify `/pricing` renders with the two Vietnamese plan names ("Gói khởi đầu" / "Gói demo Pro") and the published prices (20.000đ / 49.000đ).
- [ ] Verify `/billing` renders safely (no crash, no "live payment" implication).
- [ ] As an authenticated test user, create a checkout. The backend order must end up `pending`. **Do not expose, log, screenshot, or paste the `checkout_url`** — only verify that a redirect exists.
- [ ] Exercise the cancel flow; confirm no credits were added.
- [ ] Confirm the `/billing/success` page alone **does not grant credits** — credits must only be granted after the verified webhook, never from the browser redirect.

### 5.2 Webhook verification window

This window performs **one** authorized payment under operator authorization. No smoke-test payments; no repeated retries.

- [ ] Complete **exactly one** authorized payment (Starter Pack or Pro Demo Pack, per the approved plan for this run).
- [ ] Confirm the **verified webhook** flips the order to `paid` and grants credits exactly once.
- [ ] **Duplicate webhook** (e.g., a provider resend) **does not double-grant** credits — idempotency holds.
- [ ] **Invalid signature** webhook is rejected; **no credits** are granted.
- [ ] Order status transitions correctly (`pending` → `paid`) and is readable through normal user/admin paths.
- [ ] **No raw webhook payload** is leaked into logs, error responses, analytics events, or admin views. Only redacted metadata is allowed.

### 5.3 Credit-gating window

Only open this window after Section 5.2 passes.

- [ ] Confirm the webhook was verified before any gating change.
- [ ] Set `ENABLE_CREDIT_GATING=true` on the Render backend env.
- [ ] Redeploy the backend.
- [ ] Verify a user **with credits** can perform gated actions normally.
- [ ] Verify a user **without credits** sees the Vietnamese credit/upgrade message (no raw 402 stack trace in the UI; the frontend must render the safe pricing CTA / Vietnamese copy).
- [ ] Verify previously generated artifacts (analyses, cover letters, interview feedback, application packages) **remain accessible** — gating must not retroactively hide already-paid content.

### 5.4 Rollback

If any window above shows an unexpected behavior, roll back in the reverse order of risk.

- [ ] Disable `ENABLE_CREDIT_GATING` **first** (this stops blocking users immediately).
- [ ] Then disable `ENABLE_BILLING` if new checkout or webhook processing must be stopped.
- [ ] Redeploy the backend after each flag change.
- [ ] Confirm free / demo flows still work end-to-end (analysis, learning, cover letter, package, help, interview).
- [ ] Record the rollback reason, time, operator, observed impact, and any new blocker that triggered it in `payment_closeout_report.md`.

Do **not** delete `payment_orders`, `payment_webhook_events`, `user_entitlements`, or `usage_events` during rollback — these tables must remain intact for reconciliation and postmortem.

---

## 6. Current Phase 7A Blockers (from audit)

These are factual observations from a code audit. They are documented here as evidence so the deploy + retest in Sections 2–3 has something concrete to verify against. They are **not** fixed by this runbook. The fix owner is Quân / the implementation PR; Phúc's role is to deploy the fix when it ships and verify on production.

### 6.1 Blocker (a) — Fake marketing metrics on the landing page

**Where:** `frontend/src/components/landing/LandingPage.jsx`, the "Stats Bar" block at lines 150–173.

**Evidence (shortest decisive lines):**

- `frontend/src/components/landing/LandingPage.jsx:154` — `<div className={styles.statNum}>10,000+</div>`
- `frontend/src/components/landing/LandingPage.jsx:155` — `<div className={styles.statLabel}>CV đã phân tích</div>`
- `frontend/src/components/landing/LandingPage.jsx:159` — `<div className={styles.statNum}>98%</div>`
- `frontend/src/components/landing/LandingPage.jsx:160` — `<div className={styles.statLabel}>Độ chính xác AI</div>`
- `frontend/src/components/landing/LandingPage.jsx:164` — `<div className={styles.statNum}>30s</div>`
- `frontend/src/components/landing/LandingPage.jsx:165` — `<div className={styles.statLabel}>Thời gian phân tích</div>`
- `frontend/src/components/landing/LandingPage.jsx:169` — `<div className={styles.statNum}>4.9★</div>`
- `frontend/src/components/landing/LandingPage.jsx:170` — `<div className={styles.statLabel}>Đánh giá người dùng</div>`

**Why this is a blocker:** these four numbers ("10,000+ CV đã phân tích", "98% Độ chính xác AI", "30s Thời gian phân tích", "4.9★ Đánh giá người dùng") are hard-coded marketing claims with no underlying measurement. Showing them on the public landing page is a hard-rule violation (no fake data or fake metrics in production code) and will surface in the demo.

**Acceptable resolutions (any one is acceptable; not enforced by this runbook):**

1. Remove the stats bar entirely.
2. Replace the four hard-coded numbers with honest copy that does not imply a measured quantity (for example, an honest statement of what the product actually does in the trial phase, or a "Bản demo — số liệu minh họa, chưa phải số liệu vận hành" disclaimer, or simply the product tagline).
3. Replace the numbers with values that are actually measured and sourced from backend metrics (only if those measurements exist and are accurate).

The choice is the implementation owner's. Phúc just verifies on production that the block is gone or is honest.

### 6.2 Blocker (b) — Learning detail status update

**Where:** the user-visible failure surfaces in the frontend at `frontend/src/app/learning/[id]/page.js` around lines 70–92, which calls `updateLearningTask` from `frontend/src/services/learningApi.js` (lines 47–50), which `PATCH`es `/v1/learning/tasks/{task_id}`. The backend handler is `patch_task` in `backend/app/api/routes/learning.py` (lines 250–274).

**Evidence (shortest decisive lines):**

- Frontend handler at `frontend/src/app/learning/[id]/page.js:73`: `const updated = await updateLearningTask(id, { status: newStatus });`
- Frontend fallback message at `frontend/src/app/learning/[id]/page.js:87`: `const { message } = extractApiError(err, 'Không thể cập nhật trạng thái.');`
- Service call at `frontend/src/services/learningApi.js:48`: `const response = await apiClient.patch(\`/v1/learning/tasks/${id}\`, payload);`
- Backend route at `backend/app/api/routes/learning.py:250`: `@router.patch("/tasks/{task_id}", response_model=LearningTaskResponse, dependencies=[Depends(require_learning_enabled)])`
- Backend persistence at `backend/app/api/routes/learning.py:261-262`: `if body.status is not None: task.status = body.status`
- Backend commit at `backend/app/api/routes/learning.py:273`: `db.commit()`

**Why this is a blocker:** the user reported that changing the status on a learning task detail page surfaced "Không thể cập nhật trạng thái." and the status did not persist across refresh. PR #91 is intended to land the fix; this runbook is the verification gate. The retest in Section 3 (steps "Change status", "Confirm no 'Không thể cập nhật trạng thái.'", "Refresh; confirm status persists") is exactly what confirms the fix on production.

**Acceptable resolutions (any one; not enforced by this runbook):** the implementation PR may fix the frontend request shape, the backend schema, the route guard, the commit/refresh sequence, or the require-feature-flag gate. Phúc only verifies the user-observable outcome.

### 6.3 What Phúc does and does not own here

- **Phúc owns:** documenting the blockers (this section), deploying the fix when it ships, running the production retest in Section 3, recording pass/fail per item, and updating the verdict.
- **Phúc does not own:** writing the fix, opening the implementation PR, choosing between alternative resolutions, or modifying production env outside the approved rollout window.

---

## 7. Hard Rules

These are non-negotiable. Any violation is a stop-the-line event.

- **No enabling `ENABLE_BILLING` or `ENABLE_CREDIT_GATING`** without explicit Phúc authorization recorded in writing before the flag flip.
- **No mutating Render env** outside the approved rollout window described in Section 5.
- **No payOS provider changes.** payOS-side configuration is read-only from Phúc's perspective. Any change to provider credentials, webhook URL, return URL, cancel URL, or account mode is owned by the implementation owner; Phúc verifies, does not change.
- **No real payment during smoke.** The disabled smoke, the billing-only window, and any pre-webhook verification must use safe / unavailable responses. Real payments only happen during the single authorized webhook verification in Section 5.2.
- **No fake data or fake metrics in production code.** This is what blocker (a) is about; the rule extends to every future change. Marketing copy must be honest or absent.
- **No secrets / tokens in commits or PRs.** No JWTs, no `AUTH_TOKEN`, no payOS `CLIENT_ID` / `API_KEY` / `CHECKSUM_KEY`, no full `checkout_url`, no raw webhook payload, no `DATABASE_URL`, no raw CV/JD text, no interview answers, no cover-letter body, no application-package content. If a value would let a reader impersonate a user, charge a card, read a CV, or replay a webhook, it does not go in chat, in a doc, in a screenshot, or in a commit message.
- **No staging or committing GitNexus / Caveman local files.** `.gitnexus/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, caveman run logs, and similar local-tool artifacts are operator-local only.

---

## 8. Verdict

**Verdict: PHASE7A_BLOCKED_BY_DEMO_INTEGRITY**

Phase 7A is currently blocked by the two demo-integrity items documented in Section 6 (fake landing metrics, learning status update on detail page). Both blockers are fix-owned by Quân / the implementation PR; PR #91 has merged and is the candidate fix to verify. Until the retest in Section 3 passes on the production deploy and every Section 4 go/no-go criterion is true, Phase 7B (controlled payment rollout) must not begin. Re-evaluate this verdict after each redeploy.