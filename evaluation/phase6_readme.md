# AI CV Fit — Phase 6 Evaluation Cases

**Date:** 2026-06-22
**Owner:** Đạt
**Status:** IN_PROGRESS

---

## Overview

Phase 6 evaluation covers the 6 new backend modules:
- Target Jobs
- Learning Roadmap v2
- Interview Practice v2
- Help Assistant
- Share Links
- Usage Shell

Unlike Phase 1–5 (which test LLM-generated output quality), Phase 6 evaluation focuses on:
1. API correctness and contract compliance
2. Ownership and access control
3. Privacy: no sensitive data in responses or logs
4. Guardrail enforcement in generated outputs

---

## Case Naming Convention

Each case has a `case_ph6_XX_expected.md` file describing expected behavior and guardrail checks.
Feature-specific cases use subdirectories.

---

## Target Jobs Cases

### `case_ph6_tj_01/` — Create target job, happy path

**case_ph6_tj_01_request.json:**
```json
{
  "job_title": "Backend Developer",
  "company_name": "TechCo",
  "jd_text": "We need Python, FastAPI, PostgreSQL.",
  "target_role": "Backend"
}
```

**case_ph6_tj_01_expected.md:**
- POST returns 201 with `id`
- `job_title`, `company_name`, `jd_text`, `target_role` echoed in response
- No `storage_key`, `access_token`, `token_hash` in response
- No raw CV text

---

### `case_ph6_tj_02/` — List target jobs, filtered by status

**case_ph6_tj_02_expected.md:**
- GET `/v1/target-jobs?status=saved` returns only jobs with `status=saved`
- Response includes `total` count
- Empty list returns 200 with `total: 0`, not 404

---

### `case_ph6_tj_03/` — Cross-user access returns 404

**case_ph6_tj_03_expected.md:**
- User A creates target job
- User B calls `GET /v1/target-jobs/{job_a_id}` with User B's token
- Returns 404 (not 403, to avoid existence disclosure)
- No sensitive data from User A's job in response

---

### `case_ph6_tj_04/` — Attach analysis updates readiness

**case_ph6_tj_04_request.json:**
```json
{
  "analysis_job_id": "<uuid of succeeded job>"
}
```

**case_ph6_tj_04_expected.md:**
- POST `/v1/target-jobs/{id}/attach-analysis/{job_id}` returns 200
- `GET /v1/target-jobs/{id}/readiness` returns `readiness_level` derived from analysis
- `readiness_level` is one of: `not_started`, `almost_ready`, `ready`, `needs_work`
- No raw CV or JD text in readiness response

---

## Learning Roadmap v2 Cases

### `case_ph6_lr_01/` — Generate learning from analysis gaps

**case_ph6_lr_01_expected.md:**
- Generate roadmap with analysis attached
- Response includes `limitations` field (non-empty)
- All tasks have `do_not_claim_until_completed: true`
- No task claims user "already knows" a missing skill
- `priority` is `high` for must-have gaps, `medium` for nice-to-have

---

### `case_ph6_lr_02/` — Learning without analysis returns scoped fallback

**case_ph6_lr_02_expected.md:**
- Generate roadmap without analysis attached
- Response includes `fallback_used: true`
- `limitations` field is non-empty
- No fabricated learning tasks without evidence

---

### `case_ph6_lr_03/` — Task progress update

**case_ph6_lr_03_request.json:**
```json
{
  "status": "in_progress"
}
```

**case_ph6_lr_03_expected.md:**
- PATCH `/v1/learning/tasks/{id}` returns 200 with updated `status`
- Cross-user task update returns 404

---

## Interview Practice v2 Cases

### `case_ph6_ip_01/` — Interview session happy path

**case_ph6_ip_01_expected.md:**
- Create session with `session_type`, `difficulty`
- Generate questions → questions have `type`, `why_this_question`, `suggested_answer_outline`, `risk_if_user_cannot_answer`
- No `gap_probe` question implies user has the missing skill
- Submit answer → rubric returned with `disclaimer`
- Session summary → aggregated scores without raw answer text

---

### `case_ph6_ip_02/` — Answer retry updates score

**case_ph6_ip_02_expected.md:**
- Submit same question with different answer twice
- Both answers stored with `attempt_number`
- Summary shows both attempts
- Newer attempt score does NOT average with older attempt in a way that hides improvement

---

### `case_ph6_ip_03/` — Cross-user session access returns 404

**case_ph6_ip_03_expected.md:**
- User A creates session
- User B calls `GET /v1/interview/sessions/{session_a_id}` with User B's token
- Returns 404
- User B cannot see User A's questions or answers

---

## Help Assistant Cases

### `case_ph6_ha_01/` — `next_best_action` returns scoped answer

**case_ph6_ha_01_request.json:**
```json
{
  "intent": "next_best_action",
  "target_job_id": "<uuid>"
}
```

**case_ph6_ha_01_expected.md:**
- Response has `answer`, `based_on` (labels only, no raw CV text), `recommended_actions`, `limitations`
- `recommended_actions` uses product routes, not external URLs
- No raw CV text, raw JD text, or interview answer text in `answer`

---

### `case_ph6_ha_02/` — Unsupported intent returns fallback

**case_ph6_ha_02_request.json:**
```json
{
  "intent": "salary_negotiation"
}
```

**case_ph6_ha_02_expected.md:**
- Response has `fallback_used: true`
- `answer` does not fabricate salary advice
- `limitations` field is non-empty

---

### `case_ph6_ha_03/` — Cross-user access returns 404

**case_ph6_ha_03_expected.md:**
- User A calls help assistant with User A's token
- User B cannot access User A's data through help assistant
- Response scoped to User B's own data only

---

## Share Links Cases

### `case_ph6_sl_01/` — Create share link returns token once

**case_ph6_sl_01_expected.md:**
- POST creates share link, returns raw `token` ONCE
- GET share link (owner) → no `token` in response, only metadata
- `token_hash` is NOT in any response
- `share_token` is NOT in any GET response

---

### `case_ph6_sl_02/` — Public view redacts CV and JD

**case_ph6_sl_02_expected.md:**
- GET `/v1/public/share/{token}` (valid token)
- Response does NOT contain `raw_cv_text`, `cv_text`, `jd_text`, `raw_jd`
- Score shown as bucket (e.g., `75-84`), not exact value
- Candidate name may be present but raw JD/CV is redacted

---

### `case_ph6_sl_03/` — Revoke makes link return 404

**case_ph6_sl_03_expected.md:**
- Owner revokes share link → DELETE returns 200
- GET `/v1/public/share/{token}` after revoke → 404 (not 410)
- GET `/v1/share-links` (owner) → revoked link not listed

---

### `case_ph6_sl_04/` — Cross-user access to share links returns 404

**case_ph6_sl_04_expected.md:**
- User A creates share link
- User B calls `GET /v1/share-links` with User B's token
- Returns 200 with User B's links only (not User A's)
- User B cannot PATCH/DELETE User A's share link

---

## Usage Shell Cases

### `case_ph6_us_01/` — Usage returns counts, no enforcement

**case_ph6_us_01_expected.md:**
- `GET /v1/usage/me` returns `enforcement_enabled: false`
- Response includes counts for: `analyses`, `interview_answers`, `cover_letters`, `application_packages`
- No raw CV/JD/answer text in response

---

### `case_ph6_us_02/` — Plans endpoint returns free_demo only

**case_ph6_us_02_expected.md:**
- `GET /v1/plans` returns at least one plan with `id: free_demo`
- No `checkout_url` in response
- No price or payment data
- No plan pretends to be purchasable

---

## Privacy Guardrail Cases

### `case_ph6_priv_01/` — No JWT in logs or responses

All cases must verify:
- `access_token` not in any response
- `password_hash` not in any response
- `storage_key` not in any response
- `token_hash` not in any response
- JWT not printed in logs

**Verification:** `rg` scan of all response payloads

---

### `case_ph6_priv_02/` — No raw CV/JD in share public view

**case_ph6_priv_02_expected.md:**
- Share public view redacts raw CV and JD by default
- No `cv_text`, `jd_text`, `raw_cv`, `raw_jd` fields present
- Only buckets/labels for scores

---

## Guardrail Violation Checklist

For all Phase 6 output-generating features, verify:

| Check | Target | Learning | Interview | Help | Share |
|-------|--------|---------|----------|------|-------|
| No "you already know X" in gap context | — | ✅ | — | — | — |
| No "you don't know X" phrasing | — | ✅ | ✅ | ✅ | — |
| No hiring guarantee | ✅ | ✅ | ✅ | ✅ | — |
| `disclaimer` always present | — | — | ✅ | ✅ | — |
| `token_hash` never in response | — | — | — | — | ✅ |
| Raw CV/JD redacted in public view | — | — | — | — | ✅ |
| Ownership 404 on cross-user access | ✅ | ✅ | ✅ | ✅ | ✅ |
| `do_not_claim_until_completed: true` | — | ✅ | — | — | — |
| Answer text never in analytics | — | — | ✅ | — | — |

---

## Run All Phase 6 Evaluations

```bash
# Backend API / ownership / privacy evaluation
python scripts/evaluate_phase6_cases.py

# With verbose output
python scripts/evaluate_phase6_cases.py --verbose

# Run specific case
python scripts/evaluate_phase6_cases.py --case ph6_tj_03
```
