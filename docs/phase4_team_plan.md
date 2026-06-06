# Expanded Phase 4 Team Plan

## Purpose

Expanded Phase 4 turns AI CV Fit from a one-time CV-to-JD scorer into a Career Readiness Operating System. The product should help a user improve the CV, compare progress across revisions, prepare for interview questions, and plan learning without fabricating skills or experience.

This phase should preserve the Phase 1 to Phase 3 foundations:

- Guest access through per-job `access_token`.
- Logged-in ownership through JWT Bearer auth.
- `GET /v1/jobs/{job_id}/result` compatibility.
- History and DOCX report download behavior.
- Result JSON v2 fields and score aliases.
- Evidence-first wording and no hiring guarantee.

## Must-Have Scope

- Improvement Action Plan v1: prioritized actions tied to JD requirements, CV evidence, and missing evidence.
- Safe Rewrite Suggestions v1: rewrite guidance that only uses facts already present in the CV or explicitly asks the user to confirm missing context.
- Interview Prep Pack v1: role/JD-specific interview questions with answer outlines, evidence links, and caveats.
- Learning Roadmap v1: prioritized learning gaps with topics, mini-project suggestions, and rules for when the user can add evidence to the CV.
- Re-analysis flow: upload a revised CV for the same JD or an updated JD and create a linked analysis job.
- Before/After Comparison: compare two analysis jobs in the same analysis group and show score, evidence, and gap changes.
- Keyword stuffing detection basic: warn when improvement appears to be repeated keywords without meaningful evidence.
- DOCX report v3 support: include action plan, safe rewrite, interview prep, learning roadmap, and comparison summary when available.
- History/revision integration: show revision groups, revision numbers, and before/after access from history.
- Guardrails v2: stricter no-fabrication, safe rewrite, interview prep, learning, comparison, keyword stuffing, and privacy rules.

## Team Split

### Phúc: Backend, Product, And API Contracts

Owns:

- Result JSON v3 contract and backend result expansion.
- Re-analysis and comparison API contracts.
- Linked job/revision behavior and analysis group rules.
- Report v3 backend support.
- Smoke commands and deployment validation.
- Backward compatibility with Result JSON v2, history, result, report, owner JWT, and guest access token flows.

Deliverables:

- Contract docs and implementation PRs for result v3, comparison, re-analysis, and report v3.
- Focused backend tests for compatibility, auth, comparison, and report safety when implementation starts.
- Smoke run evidence for local or deployed API when Phase 4 closes.

### Quân: Frontend Result And Comparison Experience

Owns:

- Expanded result UI for action plan, rewrite suggestions, interview prep, and learning roadmap.
- Re-analysis upload flow.
- Revision history UI.
- Before/after comparison dashboard.
- Empty, loading, error, and guest-token-safe states.

Deliverables:

- Result page sections that render v2 and v3 payloads safely.
- Re-analysis UI that keeps original jobs immutable and clearly marks revision numbers.
- Comparison UI that explains evidence quality, not just score delta.

### Đạt: Evaluation, Guardrails, And QA

Owns:

- Guardrails v2 evaluation cases.
- Keyword stuffing detection test cases.
- Safe/unsafe rewrite wording cases.
- Interview prep and learning roadmap QA cases.
- Regression checks for no fabricated skills, no fabricated experience, no hiring guarantee, and token/privacy safety.

Deliverables:

- Evaluation skeleton before backend implementation.
- Guardrail cases that can fail implementation PRs when wording or evidence behavior is unsafe.
- Manual QA checklist for Phase 4 closeout.

## PR Sequence

1. Contract docs only.
   - Add Phase 4 plan, Result JSON v3 contract, comparison/re-analysis API contract, and Guardrails v2 draft.
   - No backend, frontend, model, migration, report, or test implementation.
2. Evaluation skeleton.
   - Add Phase 4 evaluation case structure and guardrail fixtures.
   - Keep expected outputs contract-based until backend exists.
3. Backend result expansion.
   - Add Result JSON v3 builder/enricher while preserving v2 aliases and response compatibility.
   - Add focused tests for result shape, guardrails, and no internal field leakage.
4. Frontend expanded UI.
   - Render v3 sections with v2 fallback.
   - Add user-facing empty/error states for unavailable v3 sections.
5. Reanalysis and comparison.
   - Implement linked job creation and comparison endpoint.
   - Integrate history/revision UI and comparison dashboard.
6. Report v3 and closeout.
   - Add DOCX report v3 sections.
   - Run backend, frontend, evaluation, smoke, and manual QA closeout.

## Definition Of Done

Phase 4 is done when:

- Result JSON v3 is returned as an additive extension of v2.
- Existing result, history, report, and smoke consumers still work.
- Improvement actions, rewrite suggestions, interview prep, and learning roadmap are evidence-first and guarded.
- Re-analysis creates linked immutable jobs with revision metadata.
- Comparison explains score delta, resolved gaps, remaining gaps, new evidence, and keyword stuffing warnings.
- DOCX report v3 includes expanded readiness sections when available.
- Evaluation covers safe wording, fabricated claim prevention, keyword stuffing, and comparison behavior.
- Frontend renders v3 and v2 states without breaking guest or logged-in flows.
- No tokens, raw CV text, storage paths, or internal report paths leak in API responses, reports, logs, or docs.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Result v3 breaks existing dashboard, history, report, or smoke scripts. | Keep v3 additive, preserve v2 fields and aliases, and test v2 consumers against v3 payloads. |
| Rewrite suggestions encourage fabricated claims. | Require source evidence, missing context prompts, `do_not_fabricate`, and guardrail evaluation cases. |
| Score delta becomes the only progress signal. | Comparison must show evidence quality, resolved gaps, still-missing gaps, and keyword stuffing warnings. |
| Re-analysis mutates the original result. | Original jobs remain immutable; revised uploads create linked child jobs with revision metadata. |
| Guest tokens leak through URLs or logs. | Preserve current guest behavior but redact URLs and avoid logging full query strings or token form fields. |
| Keyword stuffing detection produces false positives. | Start with basic warnings only; do not penalize score heavily until evaluation evidence supports it. |
| DOCX report becomes too large or hard to scan. | Keep report v3 section summaries concise and include detailed evidence only when useful. |
