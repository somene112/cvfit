# Phase 6 Demo Health Check

> **Date:** 2026-06-19
> Run before any Phase 6 demo. Use synthetic accounts only.

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

## Manual checklist

- [ ] Backend health: `GET /health` → 200
- [ ] Frontend health (if applicable): app loads, no console errors
- [ ] Migration head is `20260620_0001` (`alembic heads` on the deploy DB)
- [ ] Auth: register + login returns a token
- [ ] Target job: create + list works; cross-user id → 404
- [ ] Attach analysis: readiness becomes derived (or `not_started` when none)
- [ ] Learning: `POST /v1/target-jobs/{id}/learning/generate` returns tasks + limitations
- [ ] Interview v2: create session → generate questions → submit answer → summary
- [ ] Help assistant: `next_best_action` returns a scoped answer; out-of-data → `fallback_used: true`
- [ ] Share links: flag-off → all `/v1/share-links` and `/v1/public/share/*` return 404
- [ ] Usage: `GET /v1/usage/me` → counts + `enforcement_enabled: false`; `GET /v1/plans` → free_demo, no checkout
- [ ] Analytics: critical events fire (see event plan); **no raw private text in payloads**
- [ ] Logs: no raw CV/JD/answer text, JWTs, share tokens, or `token_hash`
- [ ] Render smoke: deployed app boots after `alembic upgrade head`

## Sign-off

| Role | Name | Status |
|------|------|--------|
| Backend | Phúc | ☐ |
| Frontend | Quân | ☐ |
| QA/Privacy | Đạt | ☐ |
