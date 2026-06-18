# Phase 6 Kickoff Plan — Product Expansion & JobReady Parity

> **Theme:** Product Expansion & JobReady Parity — Lightweight Career Operating System
> **Version:** 1.0
> **Date:** 2026-06-18
> **Status:** Active — Phase 6 (planning)
> **Document type:** Docs-only kickoff. No backend, frontend, migration, or runtime changes in this PR.

---

## 1. Baseline

- **Phase 5 is completed, audited, deployed, and closed out.** Phase 6 builds directly on the
  Application Readiness Suite delivered in Phase 5 (application workspace, evidence vault,
  application package, cover letter draft, interview practice v2 shell, readiness dashboard).
- Phase 6 starts **from** the Application Readiness Suite, not from scratch. We reuse existing
  applications, analysis jobs/results, learning roadmap shell, and the `/help` shell wherever
  possible.
- This plan refines and supersedes the parking-lot framing in
  [phase6_product_scope.md](phase6_product_scope.md) with a concrete, sequenced delivery plan.

---

## 2. Product Goal

Move AI CV Fit from a single-application readiness workspace toward a **lightweight career
operating system**: a place where a student or fresh graduate can manage multiple target jobs,
follow a learning roadmap toward each one, practice interviews, get guided help, share a
readiness summary, and see their usage — all grounded in real CV evidence and without overbuilding
high-risk surfaces (payment, recruiter portal, marketplace scraping, free-form chatbot).

---

## 3. In-Scope Modules

| # | Module | One-line definition |
|---|--------|---------------------|
| 1 | **Target Jobs** | Saved JD workspace; track multiple target jobs through a status pipeline; attach an analysis to each. |
| 2 | **Learning Roadmap** | Generate and track learning tasks from analysis gaps, per target job. |
| 3 | **Interview Practice v2** | Structured practice sessions with question generation, answer submission, rubric feedback, and history. |
| 4 | **Help Assistant** | Guided, scoped career-coach assistant over a fixed set of intents (not a free-form chatbot). |
| 5 | **Shareable Readiness** | Recruiter-lite, privacy-reviewed share links to a redacted readiness summary. |
| 6 | **Usage Shell** | Read-only usage/plan/credits visibility. No real billing or checkout. |
| 7 | **Analytics & Product Ops** | GA4 critical-event coverage, privacy rules, and deployed E2E closeout. |

---

## 4. Out of Scope (Phase 6)

These are explicitly **not** built in Phase 6:

- **Real payment checkout** (PayOS/Stripe, wallet/ledger, refunds, webhooks).
- **Full recruiter portal** (separate role model, ATS-like surface).
- **Job marketplace scraping** (external job ingestion, search/index, data licensing).
- **Course marketplace** (catalog, content licensing, course payments).
- **Video / WebRTC interview** (camera, recording, media storage).
- **Automated apply-to-job** (auto-submission to external systems).
- **Public share without privacy review** (share links stay behind a feature flag until privacy
  review passes).

---

## 5. Recommended PR Sequence

| PR | Type | Title |
|----|------|-------|
| PR 66 | docs | add Phase 6 kickoff plan |
| PR 67 | feat | add target jobs workspace |
| PR 68 | feat | expand learning roadmap |
| PR 69 | feat | add interview practice sessions v2 |
| PR 70 | feat | add guided help assistant |
| PR 71 | feat | add shareable readiness package |
| PR 72 | feat | add usage and plan shell |
| PR 73 | docs/test | add Phase 6 analytics and E2E closeout |

Each `feat` PR is expected to ship its backend, frontend, and tests together (or in a tightly
coupled pair of PRs) behind a feature flag, following the contract in
[phase6_api_contract.md](phase6_api_contract.md).

---

## 6. Recommended Order

1. **Target Jobs first** — it is the spine of the career OS; other modules attach to a target job.
2. **Learning + Interview second** — both hang off a target job and reuse existing analysis/roadmap
   and interview shells.
3. **Help Assistant third** — scoped intents that read from the data the first modules produce.
4. **Shareable Readiness fourth** — depends on a complete readiness package and a passed privacy
   review.
5. **Usage + Analytics closeout last** — usage shell plus GA4 coverage, privacy verification, and
   deployed E2E report.

---

## 7. Guiding Principles

- **Reuse before rebuild.** Prefer extending existing tables/models (applications, analysis jobs,
  learning roadmap) over new migrations. See [phase6_technical_scope.md](phase6_technical_scope.md).
- **Flag everything new.** Every module ships behind a feature flag so Phase 5 flows stay safe.
- **Evidence-first, always.** No fabricated skills, no hiring guarantees, no invented scores.
- **Privacy by default.** Share links are redacted and flag-gated until privacy review passes; no
  raw CV/JD/answer text, tokens, JWTs, or secrets in analytics, docs, or logs.
- **No demo PII.** All demo data is synthetic.

---

## 8. Related Documents

- [phase6_team_plan.md](phase6_team_plan.md) — work split (Phúc / Quân / Đạt) and weekly plan.
- [phase6_technical_scope.md](phase6_technical_scope.md) — route/service areas and feature flags.
- [phase6_api_contract.md](phase6_api_contract.md) — planned API contract (draft only).
- [phase6_acceptance_criteria.md](phase6_acceptance_criteria.md) — product/technical/privacy/analytics/demo gates.
- [phase6_product_scope.md](phase6_product_scope.md) — original parking-lot framing.
