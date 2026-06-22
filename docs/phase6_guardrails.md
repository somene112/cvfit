# Guardrails v4 — AI CV Fit Phase 6

**Version:** 4.0
**Date:** 2026-06-22
**Owner:** Đạt (evaluation / QA)
**Status:** Active — Phase 6
**Extends:** Guardrails v3 (Phase 5)

---

## Purpose

This document extends Guardrails v3 with Phase 6-specific rules covering Target Jobs / Saved JD Workspace, Learning Roadmap Expansion, Interview Practice v2, Help Assistant, Shareable Readiness, and Usage / Plan Shell. All v3 guardrails remain in force. This document adds Phase 6 rules only.

---

## Guardrail Philosophy

> The system must **never fabricate** a skill, experience, company, metric, certification, or achievement — in any output type, at any phase. Every claim in system-generated content must be traceable to evidence in the user's CV, analysis result, or career profile. Missing evidence must be disclosed honestly, not silently omitted or replaced with invented content.

---

## 1. Target Jobs Guardrails

Target jobs are user-provided saved job descriptions. The system's obligation is:

- Accept only structured user input for job title, company, JD text, and source URL.
- Never generate, rewrite, or infer JD content — the JD is the user's own input.
- When generating readiness from an attached analysis, derive it from the existing analysis result only.
- Readiness is not a new scoring model; it is a derived summary from `fit_score`, `matched_skills`, and `missing_skills`.
- Never claim the user is "ready to apply" based on status alone — derive readiness from analysis result.
- Source URL is optional; if provided, never fetch or scrape it.
- `target_role` is a label, not a claim of qualification.
- Status transitions are user-driven; the system does not auto-transition status.
- Never expose another user's target jobs, even if the ID is known (ownership enforced).
- Cross-user access returns 404 (not 403) to avoid existence disclosure.

---

## 2. Learning Roadmap Guardrails

Learning tasks are generated from analysis gaps. Rules:

- Tasks must be derived from `missing_skills` or weak evidence from the analysis result.
- Never claim a missing skill as "already known" — use "was not found" or "no evidence was found" wording.
- All tasks must have `do_not_claim_until_completed: true` — user cannot claim the skill on their CV until the task is done.
- `why` fields must use evidence-not-found semantics, not capability claims.
- Priority mapping: `high` only for must-have gaps; `medium` for nice-to-have gaps; no roadmap item for already-matched skills.
- Mini-project suggestions must be concrete and achievable, not course recommendations.
- `evidence_to_add` must describe what to add to the CV after completing the task, not before.
- Estimated effort must be realistic; do not understate time required.
- Do not suggest tasks that require skills not mentioned in the attached analysis JD.
- If no analysis is attached, return a scoped fallback with `fallback_used: true` and explain limitations.
- Learning tasks must be scoped to the caller's `user_id`; cross-user access returns 404.

---

## 3. Interview Practice v2 Guardrails

Structured practice sessions with question generation, answers, rubric feedback, and history.

### Question Generation

- Questions must be grounded in the attached analysis (JD requirements + CV evidence).
- `gap_probe` questions must state the skill was not found in the CV; must not imply the user has the skill.
- Questions must not ask about skills not mentioned in the JD.
- Difficulty level must match the evidence depth in the CV (junior CV → junior questions).
- `why_this_question` must reference a real JD requirement or CV evidence line.
- Never fabricate question answer outlines — provide structured guidance only ("Problem → Architecture → Tools → Outcome"), not model-generated sample answers.
- `risk_if_user_cannot_answer` must describe the evidence gap, not a hiring outcome.

### Answer Feedback

- Feedback must reference the user's answer text and available CV/profile evidence.
- Feedback scoring must be rule-based (deterministic); no floating LLM scoring without evaluation coverage.
- `sample_outline` must not fabricate project names, companies, or metrics.
- `suggested_improvements` must be actionable and evidence-grounded.
- Weak answer → non-empty `missing_evidence` and `suggested_improvements`.
- Strong answer → still includes at least one polish suggestion.
- `disclaimer` field always present in every feedback response.
- Retry answer feature: allow re-submission; do not average scores across attempts in a way that hides improvement.
- Session summary must aggregate scores across answers without revealing raw answer text in analytics.

### Data Handling

- Interview answers are user-provided; never use them as evidence in other contexts without explicit user consent.
- Session history must be scoped by `user_id`; cross-user access returns 404.
- Never log raw interview answer text in analytics, logs, or error messages.

---

## 4. Help Assistant Guardrails

A guided, scoped career-coach assistant over a fixed intent set — **not a free-form chatbot**.

### Supported Intents

```
next_best_action        — What should I do next based on my current data?
explain_score           — Why did I get this fit score?
explain_gap             — Why is my score low / what is the top gap?
suggest_learning        — What should I learn first?
suggest_interview_practice — What should I practice for this job?
explain_application_status — What is the status of my application?
help_product_usage      — How do I use [feature]?
```

### Core Rules

- The assistant **only** answers within the supported intent set.
- All answers must be grounded in the caller's own data: current application, analysis result, interview feedback, cover letter, learning tasks, or product FAQ.
- Never fabricate data not present in the user's account.
- Never answer questions outside the intent set — respond with a guarded fallback.
- Fallback response must include `fallback_used: true` and a clear message that the question cannot be answered.
- Never infer missing data from JD requirements alone.

### Intent-Specific Rules

| Intent | Must be grounded in | Must not claim |
|--------|--------------------|----------------|
| `next_best_action` | readiness level, learning tasks, interview sessions | fabricated next steps |
| `explain_score` | analysis fit_score + breakdown | "you will be hired" |
| `explain_gap` | missing_skills from analysis | "you don't know X" |
| `suggest_learning` | learning tasks + missing skills | "you already know X" |
| `suggest_interview_practice` | interview sessions + missing skills | fabricated questions |
| `explain_application_status` | target job status + readiness | hiring guarantee |
| `help_product_usage` | product FAQ / feature descriptions | speculative behavior |

### Response Shape

```json
{
  "answer": "Scoped, grounded answer text.",
  "based_on": ["analysis_result", "learning_tasks"],
  "recommended_actions": [
    {
      "label": "Generate learning roadmap",
      "action_type": "navigate",
      "route": "/jobs/{id}/learning"
    }
  ],
  "limitations": [
    "This answer is based only on your current analysis data."
  ]
}
```

### Privacy

- Never expose raw CV text, raw JD text, interview answer text, or private IDs in the answer.
- `based_on` must use labels/counts, not raw content.
- `recommended_actions` must use product routes, not external URLs.
- Help assistant scoped by `user_id`; cross-user access returns 404.

---

## 5. Shareable Readiness Guardrails

Recruiter-lite share links to a redacted readiness summary. **Gated behind `ENABLE_PHASE6_SHARE_LINKS=false` until privacy review passes.**

### Token Security

- **Store only the SHA-256 hash of the token** — never persist the raw token.
- **Never log the raw token.**
- The raw token is returned **once** on creation to the owner only.
- Token hash must not be derivable from any other field in the response.
- Revoke support: a revoked link returns 404 (not 410) to avoid existence disclosure.
- Expiry: expired links return 404.

### Data Redaction (Public View)

By default, the public share view must redact:
- Raw CV text.
- Raw JD text.
- Interview answer text.
- Full matched/missing skills list (use count or buckets instead).
- Profile evidence details.
- Any field that could identify the candidate beyond name + readiness summary.

The public view **may** include:
- Candidate name (if provided).
- Overall readiness level label (e.g., `high` / `moderate` / `low`).
- Score bucket (e.g., `75-84`).
- High-level matched skill categories (not individual skill names if sensitive).
- Top improvement suggestions (generic, not evidence-specific).
- Share link metadata (creation date, expiry).

### Visibility Settings

The owner may choose what to include/exclude. If a setting is not chosen, redact by default.

| Setting | Default | Note |
|---------|---------|------|
| `include_score_breakdown` | `false` | Only fit level label |
| `include_package` | `false` | Application package summary |
| `include_cover_letter` | `false` | Cover letter draft |
| `include_learning_roadmap` | `false` | Learning roadmap summary |
| `hide_raw_cv` | `true` | Always redact CV text |
| `hide_raw_jd` | `true` | Always redact JD text |

### Analytics

- Analytics must not include raw share tokens, token hashes, or share link IDs.
- Share link events may include `target_type` (label only), not link IDs.

### Ownership

- Only the link owner can create, list, update, revoke, or delete their own share links.
- Cross-user access returns 404.
- The public view requires only the token — no JWT required.

---

## 6. Usage / Plan Shell Guardrails

Read-only usage and plan visibility. **No real payment, no checkout, no fake paid plan.**

### Hard Rules

- **No real payment.** Do not implement any payment processing.
- **No checkout.** Do not link to a checkout URL or accept payment input.
- **No fake paid plan.** `GET /v1/plans` returns only informational plan descriptions. Do not create a paid plan that pretends to be purchasable.
- **No usage enforcement.** `GET /v1/usage/me` returns `enforcement_enabled: false`. Do not block users based on usage counts.
- **No pricing in analytics.** Analytics events must not include plan prices or checkout attempt metadata.

### What is Allowed

- Display current plan (e.g., `free_demo`).
- Display usage counts for informational purposes.
- Show feature limits with informational copy.
- Display an "upgrade teaser" that is disabled (no checkout link).
- Count metrics: analyses, interview answers, cover letters, packages, share links.

### Warning Copy

When usage approaches a limit, show a soft warning only:

```
You have used 4 of 5 free analyses this month.
Upgrade to [Plan Name] for more.
```

Do not say:
- "You have reached your limit. Upgrade now to continue." (implies enforcement)
- Any price or checkout URL in UI copy.

### Privacy

- Usage counts must not include raw CV/JD/answer text, tokens, or PII.
- Usage page views may be tracked as events (`usage_page_viewed`) without including sensitive metadata.

---

## 7. Universal Rules (Carried Forward from v3)

### No Fabricated Claims

Applies to all Phase 6 output types:

| Prohibited | Example |
|------------|---------|
| Fabricated skill claim | "You have FastAPI experience" when not in CV |
| Fabricated company | "You worked at Google" when not in CV |
| Fabricated metric | "Improved performance by 40%" without evidence |
| Fabricated years of experience | Inferring experience not in CV |
| Fabricated JD content | Generating JD text the user did not provide |
| "You already know X" in learning | Claiming user has a missing skill |

### No Hiring Guarantee

No Phase 6 output may contain language that guarantees hiring, promises an interview, or claims a readiness level means the user will be selected.

### Token and Privacy Logging

The following must **never** appear in any API response, log output, error message, or analytics event:

```
JWT / Authorization header value
access_token (per-job guest token)
share_token (raw)
token_hash
storage_key / s3_key / file_path / report_docx_path
raw_cv_text / cv_text
raw_jd_text
interview_answer_text
password / password_hash
email address (unless hashed)
```

### Ownership and Access Control

All Phase 6 resources are scoped by `user_id`. Cross-user access returns 404 (not 403) to avoid existence disclosure.

---

## 8. Guardrail Violation Severity

### Blocker (Must Fix Before Merge)

- Fabricated skill, company, metric, experience, or JD content in any generated output.
- Hiring guarantee language in any output.
- JWT, access token, share token, or storage key in any API response or analytics event.
- User can access another user's target job, learning task, interview session, share link, or usage data.
- Share link stores raw token (not hash only).
- Public share view exposes raw CV or JD text.
- Help assistant returns non-fallback answer for unsupported intent.
- Learning roadmap claims user has a missing skill.
- Interview question implies user has a skill not found in CV.

### High Severity (Must Fix Before Merge)

- Readiness summary missing `disclaimer`.
- Interview `gap_probe` question implies user has the missing skill.
- Help assistant answer references raw CV/JD/answer text.
- Share link metadata leaks token hash in analytics.
- Usage shell displays a fake checkout URL or price.

### Medium Severity (Fix in Next Sprint)

- Help assistant `limitations` field is empty.
- Learning task has no `estimated_effort` or `mini_project`.
- Interview feedback `suggested_improvements` is generic motivation instead of specific action.
- Usage warning copy implies enforcement (instead of informational only).

### Low Severity (Fix When Convenient)

- Minor wording issues in disclaimer copy.
- Share link expiry display format inconsistencies.
- Usage page missing a category count.

---

## 9. Phase 6 Closeout Checklist (Đạt)

Before Phase 6 is declared done, Đạt must confirm:

### Privacy Gates

- [ ] No raw CV/JD/answer text, JWT, share token, or `token_hash` in any API response. — CONFIRMED by `INTERNAL_FIELDS` check in `smoke_phase6_e2e.py`
- [ ] Share links store only SHA-256 token hash. — CONFIRMED: `hash_token()` in `backend/app/services/share/`
- [ ] Public share view redacts by default. — CONFIRMED: `redact_share_payload()` in share service
- [ ] Cross-user access returns 404 for all Phase 6 resources. — CONFIRMED in `smoke_phase6_e2e.py` ownership check
- [ ] Share token returned once on create only to owner. — CONFIRMED in share link POST response
- [ ] No sensitive data in GA4 event payloads. — PENDING: verify Quân's event wiring
- [ ] Demo data is synthetic only. — CONFIRMED: `smoke_phase6_e2e.py` uses `example.test` emails + demo JD

### Guardrail Gates

- [ ] Help assistant answers scoped intents only; unsupported intent returns `fallback_used: true`. — PENDING: verify in smoke
- [ ] Learning tasks use "not found" semantics, not "you don't know". — PENDING: verify in evaluation
- [ ] Interview gap_probe questions state skill was not found in CV. — PENDING: verify in evaluation
- [ ] Share link public view redacts raw CV/JD by default. — CONFIRMED in share service
- [ ] Usage shell has no checkout URL or fake payment. — CONFIRMED: `free_demo` plan only, `enforcement_enabled: false`

### Analytics Gates

- [ ] Event coverage table filled (19 events). — PENDING: fill in `phase6_acceptance_criteria.md` §6
- [ ] GA4 critical events verified (manual check in browser devtools). — PENDING: Quân wires events, Đạt verifies
- [ ] No raw CV/JD/answer text in any event property. — PENDING: verify in browser network tab
- [ ] `fit_score_bucket` / `overall_bucket` used (coarse ranges, not exact scores). — PENDING: verify in analytics code

### Technical Gates

- [ ] Backend tests pass (ownership, privacy). — CONFIRMED: per-module tests in CI
- [ ] `smoke_phase6_e2e.py` PASS on deployed backend. — CONFIRMED: `phase6_deployed_e2e_execution_report.md`
- [ ] Share links correctly return 404 when flag is off. — CONFIRMED: smoke step
- [ ] No old Phase 5 flow broken. — PENDING: verify Phase 5 smoke scripts still pass
- [ ] Render smoke PASS. — CONFIRMED: `phase6_deployed_e2e_execution_report.md`

### Demo Gates

- [ ] Demo data uses synthetic / non-sensitive content only. — CONFIRMED
- [ ] Demo health check document exists. — CONFIRMED: `docs/phase6_demo_health_check.md`
- [ ] Deployed E2E report PASS. — CONFIRMED: `docs/phase6_deployed_e2e_execution_report.md`
- [ ] Team sign-off: Phúc ☐ / Quân ☐ / Đạt ☐. — PENDING: sign after all above confirmed

---

## 10. Deferred Items

| Item | Reason | Owner |
|------|--------|-------|
| GA4 analytics wiring | Frontend not built yet | Quân |
| Share links privacy review | Feature flag off by default | Đạt (after frontend) |
| Frontend E2E smoke | Frontend not built yet | Quân + Đạt |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05 | Initial guardrails (Phase 1/2) |
| 1.5 | 2026-06-05 | Phase 3: missing skill wording, improvement actions, evidence |
| 2.0 | 2026-06-09 | Phase 4: safe rewrite, interview prep, learning roadmap, comparison, keyword stuffing |
| 3.0 | 2026-06-10 | Phase 5: application workspace, career profile, cover letter, interview practice v2, readiness |
| 4.0 | 2026-06-22 | Phase 6: target jobs, learning roadmap expansion, interview v2, help assistant, share links, usage shell |

---

*This document is the source of truth for AI CV Fit Phase 6 guardrails. Update before merging any Phase 6 feature that affects generated output wording.*
