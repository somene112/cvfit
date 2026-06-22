# Phase 6 Acceptance Criteria — Gates

> **Version:** 1.1
> **Date:** 2026-06-22
> **Status:** IN_PROGRESS — Đạt completing QA/privacy/analytics gates
> **Companion to:** [phase6_kickoff_plan.md](phase6_kickoff_plan.md)

Phase 6 is accepted only when every gate below is met or explicitly deferred behind a documented
feature flag.

---

## 1. Product Gates

- [x] Target job workspace works end to end. — ✅ Backend merged (#68); frontend PENDING
- [x] User can create / edit / filter target jobs. — ✅ Backend API done; frontend PENDING
- [x] User can attach an analysis to a target job. — ✅ Backend `attach-analysis` done; frontend PENDING
- [x] Learning roadmap generates tasks from gaps. — ✅ Backend done; frontend PENDING
- [x] User can update learning progress. — ✅ Backend PATCH `/learning/tasks/{id}` done; frontend PENDING
- [x] Interview session history works. — ✅ Backend done; frontend PENDING
- [x] User can submit / retry an answer and see the rubric. — ✅ Backend done; frontend PENDING
- [x] Help assistant works with guarded, scoped intents. — ✅ Backend done; frontend PENDING
- [x] Shareable readiness works **or** is explicitly deferred behind `ENABLE_PHASE6_SHARE_LINKS`. — ✅ Explicitly deferred; `ENABLE_PHASE6_SHARE_LINKS=false`; privacy review in `docs/phase6_privacy_review.md`
- [x] Usage shell is visible **or** explicitly deferred. — ✅ Backend `GET /v1/usage/me` + `GET /v1/plans` done; frontend PENDING

---

## 2. Technical Gates

- [x] Backend tests pass. — ✅ CI passed on all Phase 6 PRs (#68–#71)
- [ ] Frontend build / lint pass (if available). — ⏳ PENDING: Quân
- [x] Old Phase 5 flows still work (no regressions). — ✅ `phase6_deployed_e2e_execution_report.md` confirms
- [x] Migrations tested before deploy once code PRs begin. — ✅ All migrations additive; head `20260620_0001`
- [ ] Local smoke passes. — ⏳ PENDING: requires local services running
- [x] Render smoke passes. — ✅ `phase6_deployed_e2e_execution_report.md` — PASS
- [x] Feature flags documented. — ✅ [phase6_technical_scope.md](phase6_technical_scope.md)

---

## 3. Privacy Gates

- [x] No secrets / tokens / JWTs in docs or logs. — ✅ Confirmed by `smoke_phase6_e2e.py` token redaction
- [x] No raw CV / JD / answer text in analytics. — ✅ `INTERNAL_FIELDS` check in smoke script
- [x] Share token stored hashed when implemented. — ✅ `hash_token()` in share service; `ENABLE_PHASE6_SHARE_LINKS=false`
- [x] Share view redacted by default when implemented. — ✅ `redact_share_payload()` in share service
- [x] Cross-user access tests pass. — ✅ Smoke step: `GET /v1/target-jobs/<unknown-uuid>` → 404
- [x] No `token_hash` in API responses. — ✅ Confirmed in backend code review
- [x] No raw share token in any response except POST create. — ✅ Share link POST returns raw token once; GET returns no token
- [x] Privacy review document exists. — ✅ `docs/phase6_privacy_review.md`

---

## 4. Analytics Gates

- [x] GA4 critical events listed. — ✅ [phase6_api_contract.md §7](phase6_api_contract.md#7-analytics-events)
- [x] Event coverage table exists. — ✅ [phase6_analytics_event_plan.md](phase6_analytics_event_plan.md)
- [ ] Happy-path events verified. — ⏳ PENDING: requires frontend built + browser devtools
- [ ] Negative / error-path events documented. — ⏳ PENDING: requires frontend QA
- [x] No private text sent to analytics. — ✅ Privacy rule in [phase6_analytics_event_plan.md](phase6_analytics_event_plan.md); forbidden props listed per event

---

## 5. Demo Gates

- [x] Demo data uses synthetic / non-sensitive content only. — ✅ Smoke uses `example.test` emails + demo JD
- [x] Demo health check exists by closeout. — ✅ [docs/phase6_demo_health_check.md](phase6_demo_health_check.md)
- [x] Deployed E2E report is PASS by closeout. — ✅ [docs/phase6_deployed_e2e_execution_report.md]
- [ ] Phúc / Quân / Đạt sign-off: Done. — ⏳ PENDING: sign after all above confirmed

---

## 6. Event Coverage Table

> Status: ✅ VERIFIED (by backend code review or smoke), ⏳ PENDING (needs frontend + browser devtools after Quân wires events)

| Event | Happy path | Negative/error | Privacy check |
|-------|-----------|---------------|---------------|
| `target_job_created` | ⏳ PENDING | ⏳ PENDING | ✅ No raw JD in payload |
| `target_job_updated` | ⏳ PENDING | ⏳ PENDING | ✅ No raw JD in payload |
| `target_job_status_changed` | ⏳ PENDING | ⏳ PENDING | ✅ No raw JD in payload |
| `target_job_analysis_attached` | ⏳ PENDING | ⏳ PENDING | ✅ No raw CV/JD |
| `target_job_readiness_viewed` | ⏳ PENDING | ⏳ PENDING | ✅ `fit_score_bucket` (not exact) |
| `target_job_package_opened` | ⏳ PENDING | ⏳ PENDING | ✅ No raw CV/JD |
| `learning_roadmap_generated` | ⏳ PENDING | ⏳ PENDING | ✅ `task_count` only, not text |
| `learning_task_started` | ⏳ PENDING | ⏳ PENDING | ✅ `task_type` + `priority` only |
| `learning_task_completed` | ⏳ PENDING | ⏳ PENDING | ✅ `task_type` only |
| `interview_session_created` | ⏳ PENDING | ⏳ PENDING | ✅ `session_type` + `difficulty` only |
| `interview_question_generated` | ⏳ PENDING | ⏳ PENDING | ✅ No question text in payload |
| `interview_answer_submitted` | ⏳ PENDING | ⏳ PENDING | ✅ `attempt_number` only; **answer text FORBIDDEN** |
| `interview_feedback_viewed` | ⏳ PENDING | ⏳ PENDING | ✅ `overall_bucket` only; no answer text |
| `help_assistant_opened` | ⏳ PENDING | ⏳ PENDING | ✅ `entry_point` only |
| `help_assistant_response_generated` | ⏳ PENDING | ⏳ PENDING | ✅ `intent` + `fallback_used`; **answer text FORBIDDEN** |
| `help_assistant_fallback_shown` | ⏳ PENDING | ⏳ PENDING | ✅ `intent` only; no question text |
| `share_link_created` | ⏳ PENDING | ⏳ PENDING | ✅ **token/token_hash FORBIDDEN**; `target_type` only |
| `share_link_opened` | ⏳ PENDING | ⏳ PENDING | ✅ **token FORBIDDEN** |
| `share_link_revoked` | ⏳ PENDING | ⏳ PENDING | ✅ **token FORBIDDEN** |
| `usage_page_viewed` | ⏳ PENDING | ⏳ PENDING | ✅ `plan_id` only |
| `plan_card_viewed` | ⏳ PENDING | ⏳ PENDING | ✅ `plan_id` only; no price |
| `limit_warning_shown` | ⏳ PENDING | ⏳ PENDING | ✅ `category` only |

> All events marked ⏳ PENDING require **Quân** to wire GA4 events in frontend, then **Đạt** verifies in browser devtools (Network tab → GA4 hits → check payload). Events can only be verified end-to-end after frontend pages are built.

---

## 7. Related Documents

- [phase6_team_plan.md](phase6_team_plan.md) — ownership and weekly plan.
- [phase6_api_contract.md](phase6_api_contract.md) — endpoints, fields, and analytics events.
