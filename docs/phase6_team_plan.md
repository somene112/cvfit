# Phase 6 Team Plan — Product Expansion & JobReady Parity

> **Version:** 1.0
> **Date:** 2026-06-18
> **Status:** Active — Phase 6 (planning)
> **Companion to:** [phase6_kickoff_plan.md](phase6_kickoff_plan.md)

---

## 1. Roles and Ownership

Same three-person team and ownership model as Phases 4–5.

### Phúc — Backend, Architecture, Product Lead

Owns:

- Backend architecture for all Phase 6 modules.
- API contracts (see [phase6_api_contract.md](phase6_api_contract.md)).
- DB / migrations planning (design first; reuse existing tables where possible).
- **Target Jobs backend** — CRUD, status pipeline, attach-analysis, readiness, package.
- **Learning backend** — roadmap generation from gaps, task CRUD/progress.
- **Interview Session backend** — sessions, question generation, answer submission, rubric, summary.
- **Help Assistant backend** — scoped-intent handler, suggestions, guarded fallback.
- **Share Links backend** — token hashing, revoke, expiry, redaction (behind feature flag).
- **Usage backend** — usage counters and plan visibility (no billing).
- **Feature flags** — definition, defaults, and documentation.
- **Render smoke / E2E closeout** — deployed smoke and sign-off.

### Quân — Frontend

Owns:

- `/jobs` UI — list, filter, new, detail, compare, per-job learning/interview.
- `/learning` UI — roadmap list and task detail/progress.
- `/interview/sessions` UI — session history, new session, session detail with rubric.
- `/help/assistant` UI — guided assistant drawer over scoped intents.
- `/share/[token]` UI — public redacted readiness view.
- `/usage` UI — usage and plan shell.
- Responsive demo polish across all new pages (loading/empty/error states).
- GA4 UI event walkthrough — fire and verify critical events from the UI.

### Đạt — QA, Guardrails, Privacy

Owns:

- QA plan for Phase 6 modules.
- Guardrails coverage for new output types (learning tasks, interview feedback, assistant answers).
- Privacy / security review (especially share links before flag is enabled).
- Ownership / access-control tests (no cross-user reads/writes).
- Share link privacy tests (hashed token, redaction, revoke, expiry).
- Help assistant fallback tests (out-of-scope → guarded fallback, no hallucination).
- Analytics verification (events fire, no private text leaks).
- Deployed E2E closeout report.

---

## 2. Weekly Plan

| Week | Focus | Primary owners |
|------|-------|----------------|
| **Week 1** | Planning + Target Jobs foundation | Phúc (contracts, Target Jobs backend), Quân (`/jobs` scaffolding), Đạt (QA plan, access-control tests) |
| **Week 2** | Learning + Interview v2 | Phúc (learning + interview backends), Quân (`/learning`, `/interview/sessions` UI), Đạt (guardrails, rubric/fallback tests) |
| **Week 3** | Help Assistant + Shareable Readiness | Phúc (help + share backends), Quân (`/help/assistant`, `/share/[token]` UI), Đạt (privacy review, share link tests) |
| **Week 4** | Usage + Analytics + E2E Closeout | Phúc (usage backend, Render smoke), Quân (`/usage` UI, GA4 walkthrough), Đạt (analytics verification, deployed E2E report) |

---

## 3. Coordination Notes

- **Contracts before code.** Phúc freezes each module's contract section in
  [phase6_api_contract.md](phase6_api_contract.md) before Quân builds against it.
- **Flags first.** Each module lands behind its feature flag (see
  [phase6_technical_scope.md](phase6_technical_scope.md)) so Phase 5 stays green.
- **Share links gated.** `ENABLE_PHASE6_SHARE_LINKS` stays `false` until Đạt's privacy review passes.
- **Sign-off.** Phase 6 closeout requires Phúc / Quân / Đạt sign-off per
  [phase6_acceptance_criteria.md](phase6_acceptance_criteria.md).
