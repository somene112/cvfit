# Phase 6 Demo Health Check

> **Date:** 2026-06-22 (updated by Đạt)
> **Status:** IN_PROGRESS — Backend smoke PASS; Phase 6 automated evaluation 14/14 PASS; frontend integration + Đạt sign-off PENDING
> Run before any Phase 6 demo. Use synthetic accounts only.

---

## Automated smoke

```bash
# Read-only (health, auth, usage, plans, share flag-off):
API_BASE_URL=https://<deployed-host> python scripts/smoke_phase6_e2e.py

# Full happy path (creates throwaway demo data under a synthetic user):
API_BASE_URL=https://<deployed-host> PHASE6_SMOKE_ALLOW_MUTATING=1 \
  python scripts/smoke_phase6_e2e.py

# Preview steps without calling the API:
python scripts/smoke_phase6_e2e.py --dry-run
```

The script never prints passwords, JWTs, share tokens, or raw CV/JD/answer text.

---

## Smoke Status

| Run | Date | Result |
|-----|------|--------|
| Backend E2E smoke (mutating) | 2026-06-19 | **PASS** — `phase6_deployed_e2e_execution_report.md` |
| Phase 6 automated evaluation (`evaluate_phase6_cases.py`) | 2026-06-22 | **14/14 PASS** — Target Jobs, Learning, Interview v2, Help Assistant, Share Links, Usage Shell |
| Local smoke | — | PENDING — requires local services running |

---

## Manual Checklist

### Backend (automated by `smoke_phase6_e2e.py`)

- [x] `GET /health` → 200 — PASS 2026-06-19
- [x] `POST /v1/auth/register` (synthetic) — PASS 2026-06-19
- [x] `POST /v1/auth/login` (token redacted) — PASS 2026-06-19
- [x] `GET /v1/plans` → free_demo, no checkout — PASS 2026-06-19
- [x] `GET /v1/usage/me` → `enforcement_enabled: false` — PASS 2026-06-19
- [x] `GET /v1/share-links` → 404 (flag-off) — PASS 2026-06-19
- [x] `POST /v1/target-jobs` → 201, id returned — PASS 2026-06-19
- [x] `GET /v1/target-jobs` → 200, list populated — PASS 2026-06-19
- [x] `POST /v1/target-jobs/{id}/learning/generate` → tasks + limitations — PASS 2026-06-19
- [x] Interview session flow: create → questions → answer → summary — PASS 2026-06-19
- [x] `POST /v1/help/assistant` (`next_best_action`) → `fallback_used: false` — PASS 2026-06-19
- [x] Cross-user access: `GET /v1/target-jobs/<unknown-uuid>` → 404 — PASS 2026-06-19

### Backend Evaluation (`evaluate_phase6_cases.py`, 2026-06-22)

Automated against `https://cvfit.onrender.com` — **14/14 PASS**:

| Case | Module | Result |
|------|--------|--------|
| ph6_tj_01 | Target Jobs create | ✅ PASS |
| ph6_tj_02 | Target Jobs list | ✅ PASS |
| ph6_tj_03 | Target Jobs cross-user → 404 | ✅ PASS |
| ph6_lr_01 | Learning roadmap generate | ✅ PASS |
| ph6_lr_03 | Learning task progress update | ✅ PASS |
| ph6_ip_01 | Interview session + questions + answer | ✅ PASS |
| ph6_ip_03 | Interview cross-user → 404 | ✅ PASS |
| ph6_ha_01 | Help assistant next_best_action | ✅ PASS |
| ph6_ha_02 | Help assistant help_product_usage | ✅ PASS |
| ph6_sl_01 | Share links flag-off → 404 | ✅ PASS |
| ph6_sl_02 | Public share flag-off → 404 | ✅ PASS |
| ph6_sl_04 | Share links cross-user → 404 | ✅ PASS |
| ph6_us_01 | Usage/me endpoint | ✅ PASS |
| ph6_us_02 | Plans endpoint | ✅ PASS |
| **TOTAL** | **All Phase 6 modules** | **14/14 ✅** |

### Frontend (requires Quân to complete frontend pages first)

- [ ] Frontend health: app loads, no console errors — ⏳ PENDING
- [ ] `/jobs` page loads and lists target jobs — ⏳ PENDING
- [ ] `/jobs/new` creates a new target job — ⏳ PENDING
- [ ] `/jobs/[id]` shows job detail with readiness — ⏳ PENDING
- [ ] `/learning` shows learning tasks — ⏳ PENDING
- [ ] `/interview/sessions` shows interview history — ⏳ PENDING
- [ ] `/help/assistant` shows scoped answer — ⏳ PENDING
- [ ] `/usage` shows plan + counts — ⏳ PENDING
- [ ] Share link pages hidden (flag-off, returns 404) — ⏳ PENDING

### Privacy (Đạt to verify in browser devtools after frontend done)

- [ ] GA4 events fire for happy paths — ⏳ PENDING
- [ ] No raw CV/JD text in any GA4 event payload — ⏳ PENDING
- [ ] No JWT or share token in GA4 event payload — ⏳ PENDING
- [ ] `interview_answer_submitted` includes only `attempt_number`, not answer text — ⏳ PENDING
- [ ] `help_assistant_response_generated` includes only `intent` + `fallback_used`, not answer text — ⏳ PENDING
- [ ] `share_link_created` does not include token or `token_hash` — ⏳ PENDING
- [ ] Render logs: no raw CV/JD/answer text, JWTs, share tokens, or `token_hash` — ⏳ PENDING

### Demo Data (synthetic accounts only — Đạt)

- [x] Demo account uses synthetic email: `dat_phase5_demo@demo.app` — ✅ DONE 2026-06-22
- [x] Demo CV uses synthetic content (Nguyen Van A, TechCorp) — ✅ DONE 2026-06-22
- [x] Demo JD uses synthetic content (DemoCorp, Backend Engineer) — ✅ DONE 2026-06-22
- [x] No real user data in any demo screenshot or recording — ✅ synthetic data only

---

## Gate to Demo

All items in the **Backend** section above must be ✅ before declaring the backend ready.
All items in the **Frontend** section must be ✅ before declaring the frontend ready.
All items in the **Privacy** section must be ✅ before declaring the demo privacy-safe.
All items in the **Demo Data** section must be ✅ before any live demo.

---

## Sign-off

| Role | Name | Status | Date |
|------|------|--------|------|
| Backend | Phúc | ☐ | — |
| Frontend | Quân | ☐ | — |
| QA/Privacy | Đạt | ☐ | — |

**Instructions:** Check off each role's section above, then fill in the sign-off table row.
All three must sign before Phase 6 is declared complete.
