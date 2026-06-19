# Phase 6 Deployed E2E Execution Report

> **Date:** 2026-06-19
> **Backend URL:** `https://cvfit.onrender.com`
> **Main commit at time of run:** `a1aa4ca` (PR #71 merged)
> **Expected migration head:** `20260620_0001`
> **Tool:** `scripts/smoke_phase6_e2e.py`

## Summary verdict: **BLOCKED_BY_ENV**

The backend **code on `main` is complete and green** (all Phase 6 modules merged; 158 local
tests pass; every PR passed Backend Checks + PostgreSQL Migration Checks). However, the **deployed
Render instance has not been redeployed to the Phase 6 backend** — Phase 6 routes return 404. This
is a deploy/ops gap, **not a code defect**.

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

## Required deploy actions (ops, no code change)

1. Redeploy the backend service from `main` at commit `a1aa4ca` (or later).
2. Run `alembic upgrade head` so the deploy DB reaches `20260620_0001` **before** the app boots.
3. Confirm Phase 6 feature-flag env on Render: `ENABLE_PHASE6_SHARE_LINKS=false` (keep off until
   privacy review); other Phase 6 flags default on.
4. Re-run this smoke (read-only, then mutating with a synthetic account) and expect all PASS/SKIP.

## Privacy observations

- **No JWT printed** — login token is reported as `<redacted, len=N>` only.
- **No share token / token_hash printed.**
- **No raw CV / JD / interview answer text printed.**
- Synthetic throwaway accounts and short demo-safe JD snippets only.

## Notes

- Smoke tooling hardened in this PR: token redaction now reveals zero token bytes, and a
  false-pass bug (target-job create failure previously returned a passing result) was fixed so the
  script now exits non-zero on a genuine failure — which is why the mutating run correctly reported
  FAIL against the stale deployment.
