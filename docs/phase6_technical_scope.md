# Phase 6 Technical Scope — Planned Surfaces & Flags

> **Version:** 1.0
> **Date:** 2026-06-18
> **Status:** Active — Phase 6 (planning)
> **Companion to:** [phase6_kickoff_plan.md](phase6_kickoff_plan.md)

> ⚠️ **Planning only.** No files below exist yet. This document records the *intended* layout so
> later implementation PRs are predictable. Nothing here is created or modified in this PR.

---

## 1. Backend Route Areas (added later)

| Module | Planned route file |
|--------|--------------------|
| Target Jobs | `backend/app/api/routes/target_jobs.py` |
| Learning Roadmap | `backend/app/api/routes/learning.py` |
| Interview Sessions | `backend/app/api/routes/interview_sessions.py` |
| Help Assistant | `backend/app/api/routes/help_assistant.py` |
| Share Links | `backend/app/api/routes/share_links.py` |
| Usage | `backend/app/api/routes/usage.py` |

---

## 2. Backend Service Areas (added later)

| Module | Planned service package |
|--------|-------------------------|
| Target Jobs | `backend/app/services/target_jobs/` |
| Learning | `backend/app/services/learning/` |
| Interview | `backend/app/services/interview/` |
| Help Assistant | `backend/app/services/help/` |
| Share Links | `backend/app/services/share/` |
| Usage | `backend/app/services/usage/` |

---

## 3. Frontend Route Areas (expected later)

```
/jobs
/jobs/new
/jobs/[id]
/jobs/[id]/compare
/jobs/[id]/learning
/jobs/[id]/interview
/learning
/learning/[id]
/interview/sessions
/interview/sessions/new
/interview/sessions/[id]
/help
/help/assistant
/share/[token]
/usage
```

---

## 4. Feature Flags

| Flag | Default (initial) | Module |
|------|-------------------|--------|
| `ENABLE_PHASE6_TARGET_JOBS` | `true` | Target Jobs |
| `ENABLE_PHASE6_LEARNING` | `true` | Learning Roadmap |
| `ENABLE_PHASE6_INTERVIEW_V2` | `true` | Interview Practice v2 |
| `ENABLE_PHASE6_HELP_ASSISTANT` | `true` | Help Assistant |
| `ENABLE_PHASE6_SHARE_LINKS` | `false` | Share Links (until privacy review passes) |
| `ENABLE_PHASE6_USAGE_SHELL` | `true` | Usage Shell |

> Flags are documented here and owned by Phúc. Defaults may be tuned per environment, but
> `ENABLE_PHASE6_SHARE_LINKS` must remain `false` everywhere until Đạt's privacy review passes.

---

## 5. Architecture Recommendations

- **Reuse the existing `applications` table/model if it already matches Target Jobs closely.**
  A "target job" is conceptually a saved JD + status + optional attached analysis — very close to
  the Phase 5 application model. Prefer extending it (status enum, optional fields) over a new table.
- **Avoid unnecessary migration complexity.** Add columns/enums additively; do not restructure
  Phase 5 tables. Design migrations before writing them and dry-run locally before deploy.
- **Share links must stay behind a feature flag** (`ENABLE_PHASE6_SHARE_LINKS=false`) until the
  privacy review passes. Store only a token hash; redact raw CV/JD/private evidence by default.
- **Usage shell must not enforce real billing/payment.** It is read-only visibility of usage
  counters and static plan descriptions — no checkout, no transactions, no fake paid tiers.
- **Learning and Interview reuse Phase 5 shells.** Build on the existing learning roadmap and
  interview practice structures rather than parallel new ones where practical.

---

## 6. Related Documents

- [phase6_api_contract.md](phase6_api_contract.md) — endpoint and payload contracts.
- [phase6_acceptance_criteria.md](phase6_acceptance_criteria.md) — gates per module.
