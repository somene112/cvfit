# Guardrails v3 — AI CV Fit Phase 5

**Version:** 3.0
**Date:** 2026-06-10
**Owner:** Đạt (evaluation), Phúc (backend enforcement)
**Status:** Active — Phase 5
**Extends:** Guardrails v2 (Phase 4)

---

## Purpose

This document extends Guardrails v2 with Phase 5-specific rules covering the Application Workspace, Career Profile / Evidence Vault, Application Package, Cover Letter Draft, Interview Practice, and Readiness Summary. All v2 guardrails remain in force. This document adds Phase 5 rules only.

---

## Guardrail Philosophy

> The system must **never fabricate** a skill, experience, company, metric, certification, or achievement — in any output type, at any phase. Every claim in system-generated content must be traceable to evidence in the user's CV, analysis result, or career profile. Missing evidence must be disclosed honestly, not silently omitted or replaced with invented content.

---

## 1. Evidence-First Principle (Phase 5 Extension)

All Phase 5 features that generate user-facing text (cover letter draft, interview feedback, readiness summary, application package) must follow the evidence-first principle:

- Generate only from: JD text, parsed CV evidence, analysis result (matched/missing skills), and career profile items the user has explicitly provided.
- If evidence is missing for a claim, either omit the claim or flag it in `review_notes` / `missing_evidence`.
- Never infer missing evidence from JD requirements alone.
- Never present a skill as acquired because it appears in the JD.

---

## 2. Cover Letter Guardrails

See `cover_letter_guardrails.md` for the full cover letter contract. Summary of hard rules:

- No fabricated skills, companies, projects, metrics, or experience.
- No conversion of JD-only skills into claimed competencies.
- No hiring/outcome guarantees.
- `company_name` null → use neutral role-focused wording.
- Weak evidence → flagged in `review_notes`, not presented as strong.
- `disclaimer` field always present with standard wording.
- `review_notes` always non-empty; must describe assumptions.
- `missing_evidence` list always present (may be empty if all requirements are covered).

---

## 3. Interview Feedback Guardrails

See `interview_practice_contract.md` for the full contract. Summary of hard rules:

- Feedback must reference the user's answer and available CV/profile evidence.
- `sample_outline` must not fabricate project names, companies, or metrics.
- `suggested_improvements` must be actionable and evidence-grounded.
- Weak answer → non-empty `missing_evidence` and `suggested_improvements` (not just generic advice).
- Strong answer → still includes at least one polish suggestion.
- `disclaimer` field always present with standard wording.
- `gap_probe` questions must state the skill was not found in the CV; must not imply the user has the skill.
- Answer scoring must be deterministic (rule-based) for v1; no floating LLM-scored rubric without evaluation coverage.

---

## 4. Career Profile Evidence Guardrails

Career profile items are user-provided. The system's obligation is:

- Accept only structured user input; do not generate or embellish profile item content.
- When profile items are used as inputs (for cover letter, interview feedback, package), include only items provided by the user — do not invent additional items.
- Do not merge or synthesize two profile items into a new claim not stated in either.
- Evidence text is stored as-is; the system never upgrades weak evidence into strong evidence automatically.
- Skills listed in a profile item are not validated by the system — if the user enters "Kubernetes" as a skill, the system accepts it. The guardrail is that the system never generates this claim itself.

---

## 5. Application Package Guardrails

- `payload_json` contains only structured output derived from the user's CV evidence, analysis result, and career profile items.
- No raw CV text in `payload_json`.
- No JWT, access token, storage key, or internal paths in `payload_json` or the download response.
- If the package generation uses a cover letter draft, the cover letter's own guardrails apply in full.
- `disclaimer` from the cover letter draft must be preserved in the package payload.
- Download endpoint returns structured JSON only for v1; no raw file paths.

---

## 6. Readiness Score Guardrails

- Readiness summary is **derived** from the existing analysis result (fit score, matched/missing skills). It is not a new scoring model.
- `readiness_level` is a human-readable label derived from `fit_score` ranges — it is not a hiring prediction.
- Suggested ranges (implementation guidance, not a hard contract):
  - `fit_score` ≥ 75 → `high`
  - `fit_score` 50–74 → `moderate`
  - `fit_score` < 50 → `low`
- `next_action` must be actionable and evidence-based (e.g., "Address top 3 missing skills"), not motivational fluff.
- `disclaimer` must be included: "Readiness level is derived from CV-to-JD analysis and does not guarantee any hiring outcome."
- Do not combine readiness levels across multiple applications into a "career readiness score" in Phase 5.

---

## 7. No Fabricated Claims (Universal Rule)

This rule applies to every Phase 5 output type:

| Prohibited | Example |
|---|---|
| Fabricated skill claim | "I have 3 years of Kubernetes experience" when not in CV |
| Fabricated company | "I worked at Google on the payments team" when not in CV |
| Fabricated metric | "Improved performance by 40%" without evidence |
| Fabricated education | "I hold a master's in computer science" when not in CV |
| Fabricated certification | "I am AWS certified" when not in CV |
| JD-only skill conversion | Writing "I am proficient in X" when X is only in the JD |
| Experience invention | "I led a team of 10 engineers" without CV evidence |

System-generated output that contains any of the above is a **blocker violation** that must prevent the feature from merging.

---

## 8. No Hiring Guarantee (Universal Rule)

No Phase 5 output — cover letter, readiness summary, interview feedback, application package — may contain language that:

- Guarantees the user will be hired.
- Promises an interview will result from the application.
- Claims the user "will definitely get the job."
- States a score or readiness level means the user is "ready to get hired."

Every output type that involves a hiring context must include a `disclaimer` field with appropriate wording.

---

## 9. User Review Required

All draft outputs (cover letter draft, application package, interview feedback) must explicitly communicate that user review is required before use:

- Cover letter: `review_notes` non-empty + `disclaimer` field.
- Interview feedback: `disclaimer` field in every feedback response.
- Application package: preserves cover letter disclaimer + includes top-level disclaimer.
- Readiness summary: `disclaimer` field always present.

---

## 10. Token and Privacy Logging

The following must **never** appear in any API response, log output, error message, or generated document:

```
JWT / Authorization header value
access_token (per-job guest token)
storage_key / s3_key / object_key / file_path / local_path / report_docx_path
raw_cv_text / cv_text (except in explicitly allowed analysis input flow)
password / password_hash
```

### Logging Rules for Phase 5

- **Do not log JWT** in request logs, error traces, or debug output.
- **Do not log raw CV text** unless the existing policy for the analysis worker explicitly permits it and it is already happening in Phase 1–4.
- **Do not log private storage keys** — `storage_key` in `application_artifacts` must not appear in application logs.
- **Redact sensitive fields in error responses**: if an exception exposes a storage key, CV path, or auth token in its message, the error handler must redact before returning.
- **Do not log `payload_json`** from `application_artifacts` at INFO level. Debug-level logging of payload is acceptable only in local/dev environments and must be gated by a dev flag.

---

## 11. Demo Data Privacy

For Phase 5 demo fixtures and smoke scripts:

- Use only synthetic, obviously fictional data: fake names, fake companies, fake job titles.
- Do not use real user CVs, real JD text from real companies, or real personal data in demo fixtures.
- Smoke scripts must not commit real access tokens, real job IDs, or real user credentials.
- Đạt must verify demo fixture data in the Phase 5 QA checklist (PR7).

---

## 12. Output Wording Standards

### DO SAY

```
"Based on your CV evidence, I can highlight..."
"My background includes experience with FastAPI, as shown in my e-commerce project."
"This is a draft cover letter that needs your review before submission."
"Kubernetes evidence was not found in your CV. The JD lists it as a requirement."
"Readiness level is derived from your CV-to-JD fit score and does not guarantee any hiring outcome."
"This feedback is generated from your answer and available CV/JD evidence. Review before a real interview."
"If you have Docker experience not reflected in your CV, consider adding a project bullet."
```

### NEVER SAY

```
"I am an expert in Kubernetes." (if not in CV)
"You are guaranteed to be hired."
"This cover letter will get you an interview."
"I led the [fabricated project] at [fabricated company]."
"I increased revenue by 40%." (without evidence)
"Since you already know FastAPI..." (in a gap context)
"You have strong machine learning skills." (if not in CV)
"This score means you will be selected."
```

---

## 13. Ownership and Access Control

All Phase 5 resources (`applications`, `career_profile_items`, `application_artifacts`, `interview_answers`) are scoped by `user_id`. Enforced rules:

- Every read/write operation must validate `user_id` from JWT against the resource owner.
- No cross-user data access is permitted, even for internal service calls.
- `attach-analysis` must validate both the application and the job belong to the same user.
- Package and readiness endpoints must not leak data from another user's analysis job.
- 403 is returned when the resource exists but belongs to a different user. 404 is acceptable as an alternative when revealing existence is itself a security concern.

---

## 14. Guardrail Violation Severity

Carries forward Phase 4 severity levels, extended to Phase 5 output types:

### Blocker (Must Fix Before Merge)

- Fabricated skill, company, metric, education, or experience in any generated output.
- Hiring guarantee language in any output.
- JWT, access token, or storage key in any API response.
- User can access another user's application, profile item, or artifact.
- Cover letter with empty `review_notes` or missing `disclaimer`.
- Interview feedback with fabricated `sample_outline` details.

### High Severity (Must Fix Before Merge)

- Readiness summary missing `disclaimer`.
- Interview `gap_probe` question implies user has the missing skill.
- Weak evidence presented as strong without flagging in `review_notes`.
- Package download returning `storage_key`.

### Medium Severity (Fix in Next Sprint)

- `review_notes` present but vague (no specific assumption or missing evidence listed).
- Interview `strengths` empty for a clearly strong answer.
- Readiness `next_action` is generic motivation instead of specific action.

### Low Severity (Fix When Convenient)

- Minor wording issues in disclaimers.
- Polish suggestion missing for a strong interview answer.

---

## 15. Phase 5 Closeout Checklist (Đạt)

Before Phase 5 is declared done, Đạt must confirm:

- [x] Guardrail evaluation cases for cover letter (good/weak/missing/hallucination-risk/irrelevant) pass. — 16/16 PASS (2026-06-16, `evaluate_cover_letter_cases.py`)
- [ ] Interview feedback evaluation cases (weak/strong/missing evidence/unrelated/cross-user/empty profile/no analysis) pass. — BLOCKED: `sentence_transformers` not installed locally; CI evidence required.
- [x] Readiness summary does not invent scores or claims. — Confirmed by `evaluate_application_package.py` 16/16 PASS.
- [x] Application package payload contains no raw CV, no JWT, no storage key. — Confirmed by code review: `build_package_payload` only uses analysis result JSON and profile items.
- [x] Cross-user access test returns 404 for all Phase 5 resource types. — Confirmed in `_get_owned_application` and `_get_owned_item` (404, not 403, per non-leak convention).
- [ ] Demo fixtures contain no real PII. — PENDING: demo account setup required.
- [x] Smoke script produces no token or path leaks in output. — Backend smoke 19/20 steps pass; analysis-backed paths pending (see `phase5_backend_closeout.md`).
- [ ] All Phase 1–4 smoke endpoints still pass (backward compatibility confirmed). — PENDING: requires manual run.
- [x] `disclaimer` field present and correct in cover letter, interview feedback, readiness summary, and package. — Confirmed: all four paths enforce disclaimer in service layer.
- [ ] Manual QA checklist signed off. — PENDING: `docs/phase5_demo_checklist.md` not yet executed.

**Analytics note:** GA4/GTM analytics is not implemented in Phase 5 and is explicitly deferred to a separate future PR. This does not block Phase 5 closeout because analytics was not part of the mandatory Phase 5 exit gates.

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-05 | Initial guardrails (Phase 1/2) |
| 1.5 | 2026-06-05 | Phase 3: missing skill wording, improvement actions, low-fit cap, evidence IDs, rewrite constraints |
| 2.0 | 2026-06-09 | Phase 4: safe rewrite, interview prep pack, learning roadmap, comparison, keyword stuffing |
| 3.0 | 2026-06-10 | Phase 5: application workspace, career profile, cover letter draft, interview practice v2, readiness summary, application package, logging rules, demo data privacy |

---

*This document is the source of truth for AI CV Fit Phase 5 guardrails. Update before merging any Phase 5 feature that affects generated output wording.*
