# Phase 6 Privacy Review

**Date:** 2026-06-22
**Owner:** Đạt
**Status:** IN_PROGRESS
**Gates:** Must pass before flipping `ENABLE_PHASE6_SHARE_LINKS=true`

---

## Purpose

This document reviews the privacy posture of Phase 6 features: Share Links, Help Assistant, Learning Roadmap, Interview Practice v2, Target Jobs, and Usage Shell. It identifies privacy risks and defines the conditions required to flip `ENABLE_PHASE6_SHARE_LINKS` to `true`.

---

## Privacy Risk Matrix

| Feature | Risk | Severity | Status | Notes |
|---------|------|----------|--------|-------|
| Share Links — token storage | Raw token persisted | 🔴 Critical | ✅ Mitigated | SHA-256 hash only; raw token returned once |
| Share Links — public view | Raw CV/JD exposed | 🔴 Critical | ✅ Mitigated | Redacted by default; visibility settings available |
| Share Links — token logging | Token printed in logs | 🔴 Critical | ✅ Mitigated | `smoke_phase6_e2e.py` never prints raw tokens |
| Share Links — analytics | Token in event payload | 🔴 Critical | ✅ Mitigated | Event table forbids share token as property |
| Help Assistant | Private CV/JD in answer | 🟠 High | ✅ Mitigated | Answer uses labels/counts, not raw text |
| Help Assistant | Private IDs exposed | 🟠 High | ✅ Mitigated | Uses product routes, not raw IDs |
| Learning Roadmap | Skills revealed in tasks | 🟡 Medium | ✅ Mitigated | Task titles use skill names from analysis only |
| Interview Practice v2 | Answer text in analytics | 🟠 High | ✅ Mitigated | `interview_answer_submitted` forbids answer text |
| Target Jobs | JD text in analytics | 🟡 Medium | ✅ Mitigated | Events forbid raw JD text as property |
| Usage Shell | Usage patterns revealed | 🟢 Low | ✅ Informational | Count-only; no sensitive content |
| All features | JWT in logs | 🔴 Critical | ✅ Mitigated | Never logged in any smoke/doc/smoke script |
| All features | Cross-user data leak | 🔴 Critical | ✅ Mitigated | 404 on all cross-user access |

---

## Share Links — Privacy Gate Checklist

`ENABLE_PHASE6_SHARE_LINKS` may only be flipped to `true` when all items below are confirmed.

### Token Security

- [ ] Raw share token is never stored in the database. Only SHA-256 hash is stored.
- [ ] `token_hash` field does not appear in any API response (only in backend DB).
- [ ] Raw token is returned only once in the `POST /v1/share-links` response.
- [ ] Subsequent reads (`GET /v1/share-links`) return only metadata, no raw token.
- [ ] `smoke_phase6_e2e.py` does not print the raw token (confirms `redact_token` used).
- [ ] No log line anywhere in the codebase prints a share token value.

**Verification commands:**
```bash
# Must return no results
rg "share_token|share_token_raw|print.*token" backend/app/services/share/
rg "share_token" scripts/smoke_phase6_e2e.py
```

### Public View Redaction

- [ ] `GET /v1/public/share/{token}` does not return raw CV text.
- [ ] `GET /v1/public/share/{token}` does not return raw JD text.
- [ ] `GET /v1/public/share/{token}` does not return interview answer text.
- [ ] `GET /v1/public/share/{token}` does not return profile evidence details.
- [ ] Candidate name is optional and may be omitted.
- [ ] Fit score is shown as a bucket (e.g., `75-84`), not exact score.
- [ ] Redaction function is tested and returns empty strings or omits fields for redacted content.
- [ ] Visibility settings are respected: `hide_raw_cv`, `hide_raw_jd`, `include_score_breakdown`.

**Verification commands:**
```bash
# Check share service redacts sensitive fields
rg "raw_cv|cv_text|jd_text|answer_text" backend/app/services/share/
# Should only find redaction logic, not inclusion in response
```

### Analytics Privacy

- [ ] `share_link_created` event does not include `token_hash` or share link ID.
- [ ] `share_link_opened` event does not include token value.
- [ ] `share_link_revoked` event does not include token value.
- [ ] All share link events use `target_type` label only, not link ID.

**Verification:** Review GA4 event payloads in browser Network tab during smoke test.

### Revoke and Expiry

- [ ] Revoking a share link makes it return 404 (not 410) to avoid existence disclosure.
- [ ] Expired links return 404.
- [ ] Revoke and expiry are tested in `smoke_phase6_e2e.py` or a dedicated test.

### Ownership

- [ ] Only the link owner can list, update, or delete their own links.
- [ ] Cross-user access to another user's share links returns 404.

---

## Help Assistant — Privacy Review

### Data Grounding

- [ ] Help assistant answers use only data from the caller's account.
- [ ] `based_on` in the response uses labels/counts, not raw CV/JD text.
- [ ] `recommended_actions` uses product routes, not external URLs.
- [ ] `answer` field never contains raw CV text, raw JD text, or interview answer text.
- [ ] `limitations` field is non-empty and describes what the assistant did not consider.

### Unsupported Intent Handling

- [ ] Intents outside the supported set return `fallback_used: true`.
- [ ] Fallback message is safe: does not fabricate advice or claim knowledge the system does not have.
- [ ] Fallback does not suggest external URLs or non-product actions.

### Analytics

- [ ] `help_assistant_response_generated` does not include answer text.
- [ ] `help_assistant_fallback_shown` does not include the user's question text.
- [ ] Only `intent` and `fallback_used` are included as event properties.

### Cross-User Isolation

- [ ] User A cannot access User B's data through the help assistant.
- [ ] Cross-user access returns 404.

---

## Learning Roadmap — Privacy Review

### Data Grounding

- [ ] Learning tasks are generated only from the analysis result (missing skills, weak evidence).
- [ ] Tasks do not include raw CV text or raw JD text.
- [ ] `evidence_to_add` describes what to add to CV after completing the task, not content from the original CV.
- [ ] Task titles use skill names derived from analysis, not fabricated skills.

### Priority and Scope

- [ ] Priority (high/medium/low) is derived from JD requirements, not from guessing the user's level.
- [ ] Tasks scoped to `user_id`; cross-user access returns 404.

### Analytics

- [ ] `learning_roadmap_generated` includes `task_count` only, not skill names.
- [ ] `learning_task_started` and `learning_task_completed` include `task_type` and `priority` only, not task free text.

---

## Interview Practice v2 — Privacy Review

### Answer Handling

- [ ] Interview answers are stored as user-provided text, never used as evidence in other contexts without consent.
- [ ] Session history scoped by `user_id`; cross-user access returns 404.
- [ ] `GET /v1/interview/sessions/{id}/summary` does not return raw answer text.

### Analytics

- [ ] `interview_answer_submitted` includes `attempt_number` only, not answer text.
- [ ] `interview_feedback_viewed` includes `overall_bucket` only, not answer text or exact score.
- [ ] Session summary does not include raw answers in any response field.

### Question Generation

- [ ] Questions reference JD requirements by label, not by embedding raw JD text.
- [ ] Questions reference CV evidence by skill name, not by embedding raw CV text.

---

## Target Jobs — Privacy Review

### JD Handling

- [ ] JD text is stored as user-provided content, not fetched or scraped from any URL.
- [ ] `source_url` is optional; if provided, it is never fetched or displayed to third parties.
- [ ] Cross-user access returns 404; ownership enforced on all endpoints.

### Analytics

- [ ] `target_job_created` and `target_job_updated` include no raw JD text.
- [ ] `target_job_readiness_viewed` includes `fit_score_bucket`, not exact score.
- [ ] `target_job_package_opened` does not include raw CV or JD.

---

## Usage Shell — Privacy Review

### Data Scope

- [ ] Usage counts are computed from database aggregates, not raw record content.
- [ ] No raw CV/JD/answer text is included in usage response.
- [ ] Usage page is scoped to the authenticated user.

### Analytics

- [ ] `usage_page_viewed` includes `plan_id` only, not usage counts of other users.
- [ ] No pricing or checkout data in analytics.

---

## Privacy Review Sign-off

| Checkpoint | Owner | Status | Date |
|------------|-------|--------|------|
| Share links token security | Đạt | PENDING | — |
| Share links public view redaction | Đạt | PENDING | — |
| Share links analytics privacy | Đạt | PENDING | — |
| Help assistant data grounding | Đạt | PENDING | — |
| Learning roadmap data grounding | Đạt | PENDING | — |
| Interview v2 answer handling | Đạt | PENDING | — |
| Target jobs JD handling | Đạt | PENDING | — |
| Usage shell data scope | Đạt | PENDING | — |
| Grep scan: no raw tokens in logs | Đạt | PENDING | — |
| Final gate: flip `ENABLE_PHASE6_SHARE_LINKS=true` | Đạt + Phúc | PENDING | — |

---

## Privacy Review Commands

Run these commands to verify privacy posture:

```bash
# Token logging — must return no results (except in test asserts or redaction helpers)
rg -i "share_token|jwt|token_hash|raw_cv|raw_jd" \
  --type py \
  backend/app/api/routes/share_links.py \
  backend/app/services/share/ \
  scripts/smoke_phase6_e2e.py

# CV/JD in share response — must return no results
rg "cv_text|jd_text|raw_cv|raw_jd" \
  --type py \
  backend/app/services/share/

# Interview answer in analytics — must return no results
rg "answer_text|interview_answer" \
  --type ts \
  frontend/src/lib/analytics.ts \
  frontend/src/services/

# Share token in analytics — must return no results
rg "share_token|token_hash" \
  --type ts \
  frontend/src/lib/analytics.ts \
  frontend/src/services/
```

---

*This document must pass all checkpoints before `ENABLE_PHASE6_SHARE_LINKS` is flipped to `true`.*
