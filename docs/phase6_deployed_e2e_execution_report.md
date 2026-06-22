# Phase 6 Deployed E2E Execution Report

> **Date:** 2026-06-22 (updated by Đạt)
> **Backend URL:** `https://cvfit.onrender.com`
> **Main commit:** `060fb16` (PR #73 merged)
> **Expected migration head:** `20260620_0001`
> **Tool:** `scripts/smoke_phase6_e2e.py`

---

## Summary verdict: **PASS** (backend smoke) | **PENDING** (frontend integration)

**Backend:** All six Phase 6 modules respond correctly end-to-end; Share Links correctly returns 404 because
`ENABLE_PHASE6_SHARE_LINKS=false`. Read-only and full mutating happy-path both **PASS** (2026-06-19).

**Frontend integration:** PENDING. All frontend pages (jobs, learning, interview, help, usage) are not yet built.
See §4 for the frontend smoke plan.

### Final run (2026-06-19, main @ `060fb16`, migrated DB head `20260620_0001`)

| Step | Result |
|------|--------|
| `GET /health` | PASS |
| `POST /v1/auth/register` (synthetic) | PASS |
| `POST /v1/auth/login` | PASS (token fully redacted) |
| `GET /v1/plans` | PASS (free_demo, no checkout) |
| `GET /v1/usage/me` | PASS (`enforcement_enabled=false`, plan=free_demo) |
| `GET /v1/share-links` | PASS (404 — flag-off, intended) |
| `POST /v1/target-jobs` + list | PASS |
| `POST .../learning/generate` | PASS (2 tasks, limited fallback) |
| `POST /v1/interview/sessions` → questions → answer → summary | PASS |
| `POST /v1/help/assistant` (`next_best_action`) | PASS (`fallback_used=false`) |
| `GET /v1/target-jobs/<unknown-uuid>` | PASS (404 non-leak ownership) |

**Read-only verdict:** PASS · **Mutating verdict:** PASS · **Overall:** **PASS**

Mutating run created throwaway synthetic records (target job, interview session/answer) under a
synthetic throwaway account; there is no cleanup endpoint, so these demo records remain (demo-safe).

---

## Prior run (resolved): BLOCKED_BY_ENV

> Recorded for history. Before the redeploy/migration, the deployed instance served pre-Phase-6
> code and Phase 6 routes returned 404. Code on `main` was already complete and green; the gap was
> purely deploy/ops. This is now **resolved** by the run above.

## Runs

### Read-only smoke

```
API_BASE_URL=https://cvfit.onrender.com python scripts/smoke_phase6_e2e.py
```

| Step | Result | Note |
|------|--------|------|
| `GET /health` | PASS | |
| `POST /v1/auth/register` (synthetic) | PASS | |
| `POST /v1/auth/login` | PASS | token fully redacted (length only) |
| `GET /v1/plans` | SKIP→404 | usage shell route not deployed yet |
| `GET /v1/usage/me` | SKIP→404 | usage shell route not deployed yet |
| `GET /v1/share-links` | PASS (404) | flag-off / not deployed — safe 404 either way |

Overall: **PASS_WITH_SKIPS** (read-only).

### Mutating smoke

```
API_BASE_URL=https://cvfit.onrender.com PHASE6_SMOKE_ALLOW_MUTATING=1 \
  python scripts/smoke_phase6_e2e.py
```

| Step | Result | Note |
|------|--------|------|
| health / register / login | PASS | |
| `POST /v1/target-jobs` | **FAIL (404)** | Phase 6 target-jobs route not present on the deployed build |

Overall: **FAIL** — but root cause is environment (see classification), not code.

## Failure classification

- [x] **Render not redeployed** — the deployed build predates the Phase 6 backend (even the
  earliest Phase 6 route, `/v1/target-jobs` from #68, returns 404).
- [x] **Migrations likely not applied** — `20260618_0001`, `20260619_0001`, `20260620_0001` must
  run before the new code boots (`init_db()` enforces the expected head).
- [ ] Missing env var — n/a (auth works; flags have safe defaults).
- [ ] Auth/registration disabled — n/a (registration + login succeed).
- [ ] Feature flag mismatch — n/a (share-links 404 is the intended flag-off behavior).
- [ ] Actual backend bug — **none found**; local suite is green and CI passed on all PRs.

## Re-verification (2026-06-19, main @ `9c6cadf`)

Re-ran after PR #72 merged: **still BLOCKED_BY_ENV** — `POST /v1/target-jobs` still returns 404 on
`https://cvfit.onrender.com`. Health/register/login still PASS; token still fully redacted. No deploy
has happened since the prior run, as expected (the deploy is a manual Render action; see below).

## Exact Render ops checklist (manual — no code change)

This repo has **no `render.yaml` blueprint** and **does not run migrations at app startup**
(`init_db()` only *verifies* the head and refuses to boot if it is behind). The deploy is therefore a
manual Render-dashboard + Render-Shell action. There is no `render` CLI, deploy hook, or deploy
workflow available in CI, so this cannot be triggered from automation here.

1. **Render dashboard → backend API service** (the `cvfit` API web service).
2. Confirm the connected **branch = `main`**; trigger **Manual Deploy → Deploy latest commit**
   (must include PR #72 / commit `9c6cadf` or later).
3. After the build finishes (new code present) and **before** the new API/worker serve traffic,
   open the **Render Shell** for the API service and apply migrations using the deployed interpreter
   (the documented path from [render_deployment.md](render_deployment.md) — do **not** rely on an
   `alembic` executable on `PATH`):
   ```bash
   cd /opt/render/project/src
   /opt/render/project/src/.venv/bin/python scripts/run_alembic.py current
   /opt/render/project/src/.venv/bin/python scripts/run_alembic.py heads      # expect 20260620_0001
   /opt/render/project/src/.venv/bin/python scripts/run_alembic.py upgrade head
   /opt/render/project/src/.venv/bin/python scripts/run_alembic.py current    # expect 20260620_0001
   /opt/render/project/src/.venv/bin/python scripts/check_db_schema.py
   ```
4. Confirm the Phase 6 feature-flag env vars on the service:
   - `ENABLE_PHASE6_TARGET_JOBS=true`
   - `ENABLE_PHASE6_LEARNING=true`
   - `ENABLE_PHASE6_INTERVIEW_V2=true`
   - `ENABLE_PHASE6_HELP_ASSISTANT=true`
   - `ENABLE_PHASE6_USAGE_SHELL=true`
   - `ENABLE_PHASE6_SHARE_LINKS=false`  ← **keep off until privacy review passes**

   (All have safe code defaults, so they only need setting to override; share-links is already
   `false` by default.)
5. Confirm CORS still allows the frontend origin (e.g. `https://cvfit-frontend.onrender.com`).
6. Restart the API (and worker) so they boot against the upgraded schema; `init_db()` should pass.
7. **Re-run the smoke** and expect all PASS/SKIP:
   ```bash
   API_BASE_URL=https://cvfit.onrender.com python scripts/smoke_phase6_e2e.py
   API_BASE_URL=https://cvfit.onrender.com PHASE6_SMOKE_ALLOW_MUTATING=1 \
     python scripts/smoke_phase6_e2e.py
   ```

> Never paste `DATABASE_URL`, tokens, or secrets into logs/PRs/screenshots. Use the Render
> **Internal** DB URL only from the Render Shell; use the **External** URL only from a trusted
> operator machine, then clear it.

## Privacy observations

- **No JWT printed** — login token is reported as `<redacted, len=N>` only.
- **No share token / token_hash printed.**
- **No raw CV / JD / interview answer text printed.**
- Synthetic throwaway accounts and short demo-safe JD snippets only.

---

## §4 — Frontend Integration Smoke Plan (PENDING)

> Status: ⏳ PENDING — requires Quân to complete frontend pages and GA4 wiring

Frontend integration smoke is tracked in `docs/phase6_qa_checklist.md` (Track 4) and
`docs/phase6_demo_health_check.md`. This section records the plan and final results.

### Preconditions

1. Quân has completed all Phase 6 frontend pages.
2. Quân has wired GA4 events per `docs/phase6_analytics_event_plan.md`.
3. Render has been redeployed with the frontend code.
4. CORS is configured to allow the frontend origin.

### Smoke steps

| Step | Command / Action | Expected |
|------|----------------|----------|
| Frontend loads | `https://cvfit-frontend.onrender.com` | Page renders, no console errors |
| Login | Register + login synthetic account | JWT stored, redirected to dashboard |
| Create target job | POST `/v1/target-jobs` via UI | Job appears in `/jobs` list |
| Learning generation | Click "Generate roadmap" in `/jobs/[id]` | Tasks appear in `/learning` |
| Interview session | Create session in `/interview/sessions` | Session appears in history |
| Submit answer | Answer a question | Rubric displayed below |
| Help assistant | Click prompt chip in `/help/assistant` | Scoped answer displayed |
| Usage page | Visit `/usage` | Plan + counts displayed |
| Share links | Attempt `/share/[token]` | 404 (flag-off) |

### Privacy smoke steps

| Step | Action | Expected |
|------|--------|----------|
| Open Network tab | Filter `collect?v=2` | GA4 hits visible |
| Create target job | Trigger `target_job_created` | No raw JD text in payload |
| Submit interview answer | Trigger `interview_answer_submitted` | Only `attempt_number` in payload |
| Help assistant | Trigger `help_assistant_response_generated` | Only `intent` + `fallback_used` |
| Share link | Trigger `share_link_created` (if flag on) | No token/token_hash in payload |

### Final result

| Smoke run | Date | Backend | Frontend | Privacy | Overall |
|-----------|------|---------|----------|---------|---------|
| Backend only | 2026-06-19 | ✅ PASS | — | ✅ PASS | ✅ PASS |
| Frontend integration | ⏳ PENDING | ⏳ PENDING | ⏳ PENDING | ⏳ PENDING | ⏳ PENDING |

---

## Notes

- Smoke tooling hardened in this PR: token redaction now reveals zero token bytes, and a
  false-pass bug (target-job create failure previously returned a passing result) was fixed so the
  script now exits non-zero on a genuine failure — which is why the mutating run correctly reported
  FAIL against the stale deployment.
