# Phase 7A Demo Integrity Fix

> Scope: this PR closes the two remaining demo-integrity blockers before Phase 7B controlled payment rollout begins.
> Payment flags unchanged. No payOS changes. No new admin endpoints. No fake metrics, no fake data.

## 1. Status

- Branch: `fix/phase7-demo-integrity-learning-status`
- Base: `main` at `7b93278` (PR #91 merged)
- Payment flags unchanged: `ENABLE_BILLING=false`, `ENABLE_CREDIT_GATING=false`
- GitNexus / Caveman local files: untouched, untracked, not staged
- Working tree: only the four intended files modified

## 2. Blocker 1 — Fake marketing metrics

### Observation
`frontend/src/components/landing/LandingPage.jsx` previously rendered a hard-coded stats bar with four unsupported claims:

- `10,000+` — CV đã phân tích
- `98%` — Độ chính xác AI
- `30s` — Thời gian phân tích
- `4.9★` — Đánh giá người dùng

These are not backed by any real measurement and constitute fake marketing claims. They cannot be shown on the public landing page.

### Root cause
Direct hard-coded numeric marketing copy inside the public `LandingPage` component. The CSS classes `.statsBar / .statsInner / .statItem / .statLabel / .statDivider` were designed to render a value strip but had been misused to render fake quantitative claims.

### Fix
Replaced the four numeric items with honest, non-numeric product-positioning labels that describe real, demonstrated product capabilities already covered in Sections 2–7 of the demo flow:

- Phân tích CV theo JD
- Gợi ý cải thiện có kiểm soát
- Lộ trình học tập cá nhân hoá
- Thanh toán đang thử nghiệm

The "Thanh toán đang thử nghiệm" label is an honest disclosure that the credit-pack MVP is not yet generally available — it does not advertise any number.

- No `10,000+`, `98%`, `30s`, `4.9★`, or equivalent fake numeric claims remain anywhere in `frontend/src`.
- No fake metric was replaced with a different fake metric.
- The visual rhythm of the section is preserved via the existing `.statItem / .statLabel / .statDivider` rules.

## 3. Blocker 2 — Learning detail status update

### Observation
On `/learning/<task_id>`, changing the status dropdown surfaced the Vietnamese message:

> Không thể cập nhật trạng thái.

…but the backend PATCH endpoint (`PATCH /v1/learning/tasks/{task_id}`) was already correct and covered by passing tests. The detail-page status badge often appeared unchanged after a click, and a refresh sometimes still showed the previous status even when the server had accepted the update.

### Root cause
Three defects in the React handler in `frontend/src/app/learning/[id]/page.js` (and a parallel one in `frontend/src/app/learning/page.js`):

1. **Sticky error state.** The `error` state was set on initial GET load failures (e.g. an auth race 401) and was never cleared on a subsequent successful PATCH. The page-level `<ErrorBanner>` therefore kept showing the stale Vietnamese message even when the update succeeded.
2. **No optimistic update.** The dropdown value only changed after the server returned. While the request was in flight, the `<select>` showed the old value and a second click could fire before `isUpdating` flipped back, producing a confused user experience.
3. **Fallback copy fired too easily.** The literal `Không thể cập nhật trạng thái.` was the `fallback` argument to `extractApiError`, which is only returned when no `detail` shape was matched and no friendly HTTP status applied. That happens when the request never reached the server (network blip, auth race, CORS preflight) — the user then saw the same generic message regardless of root cause.

### Fix

**Frontend detail page — `frontend/src/app/learning/[id]/page.js`:**
- Clear `error` before each PATCH attempt.
- Apply the new status to local state immediately (optimistic update).
- Roll back to the previous status if the API rejects the change.
- Gate the request on auth readiness (`isAuthChecking`) so we never fire before the bearer token is attached.
- Strengthen the fallback copy to `Không thể cập nhật trạng thái. Vui lòng thử lại.` and let `extractApiError` continue to translate real backend detail messages and HTTP statuses.

**Frontend list page — `frontend/src/app/learning/page.js`:**
- Same optimistic update + rollback pattern so the list and detail stay consistent and never show a misleading banner.

**Backend — unchanged.** `backend/app/api/routes/learning.py::patch_task` already:
- Accepts the canonical `LearningStatus` enum (`todo | in_progress | done`).
- Enforces ownership (404 on cross-user access — no existence leak).
- Persists and returns the updated `LearningTaskResponse`.

### Backend test additions — `backend/tests/test_phase6_learning.py`
Two new tests under `TestTaskCRUD`:

- `test_patch_status_persists_for_subsequent_get` — PATCH then GET must agree on the new status. This is the regression that would have caught a silent partial write.
- `test_patch_status_unknown_task_returns_404` — PATCH against an unknown id returns 404. Confirms the frontend's rollback path is the correct safety net (no leaked existence).

Existing tests already covered `test_patch_status_progression`, `test_patch_invalid_status_returns_422`, `test_patch_invalid_priority_returns_422`, and `test_patch_cross_user_task_returns_404`.

## 4. Validation run

| Check | Result |
|---|---|
| `python -m pytest backend/tests/test_phase6_learning.py` | **19 passed** (17 existing + 2 new) |
| `npm.cmd run lint` (frontend) | clean (only the pre-existing layout.js font warning) |
| `npm.cmd run build` (frontend) | green — `/learning` and `/learning/[id]` static/dynamic pages compile |
| `git diff --check` | no whitespace errors |
| Privacy / trust grep on changed files | no PAYOS keys, no JWTs, no checkout URLs, no raw CV/JD/answer text, no fake numeric metrics |

`python -m compileall backend/app` was attempted but Windows held an exclusive lock on a `.pyc` file under `backend/app/workers/__pycache__/`. Pytest ran the test suite independently and passed, which gives equivalent assurance for the touched modules.

## 5. Privacy / trust audit on changed files

- No secrets, no tokens, no JWTs introduced.
- No raw CV, JD, interview answer, cover letter, or application package content surfaced.
- No new admin mutation endpoints.
- No payOS / checkout / webhook code touched.
- No `10,000+ / 98% / 30s / 4.9★` visible numeric claims remain in `frontend/src`. The remaining `CV đã phân tích` occurrences live inside product-copy strings describing the user's own analyzed CV, not marketing claims.
- The existing `RAW_JD_SENTINEL` privacy-guard test is unchanged.

## 6. Manual production retest checklist (after merge + deploy)

After the PR is merged and Render redeploys latest `main`, the production retest is:

1. Open `/` — confirm landing value strip shows the four new honest labels and no numeric scale / rating / accuracy claims.
2. Run a fresh CV analysis from `/dashboard`. Confirm Vietnamese generated quality remains acceptable.
3. Open `/learning`. Generate a roadmap from the latest analysis if the list is empty.
4. Open a task detail page (`/learning/<task_id>`). Change the status dropdown.
5. Confirm: no "Không thể cập nhật trạng thái." banner appears; the status badge updates immediately; a page refresh preserves the new status.
6. Repeat step 4–5 on the list page dropdown.
7. Regression: Sections 4 (Help Assistant), 5 (Interview), 6 (Cover Letter), 7 (Application Package) still work.
8. Confirm `ENABLE_BILLING=false` and `ENABLE_CREDIT_GATING=false` on Render before declaring Phase 7A closed.

## 7. Payment — untouched

- `ENABLE_BILLING` — not changed.
- `ENABLE_CREDIT_GATING` — not changed.
- Render env — not mutated.
- payOS / checkout / webhook code — not touched (read-only review during diagnosis).
- No real payment performed. No fake data created.

## 8. Out of scope

- Phase 7B controlled payment rollout (separate PR after Phase 7A passes production manual QA).
- Credit gating enablement.
- payOS provider changes.
- Landing redesign beyond removing fake metrics.
- Section 4–8 functionality changes.
