# Phase 6 Acceptance Criteria — Gates

> **Version:** 1.0
> **Date:** 2026-06-18
> **Status:** Active — Phase 6 (planning)
> **Companion to:** [phase6_kickoff_plan.md](phase6_kickoff_plan.md)

Phase 6 is accepted only when every gate below is met or explicitly deferred behind a documented
feature flag.

---

## 1. Product Gates

- [ ] Target job workspace works end to end.
- [ ] User can create / edit / filter target jobs.
- [ ] User can attach an analysis to a target job.
- [ ] Learning roadmap generates tasks from gaps.
- [ ] User can update learning progress.
- [ ] Interview session history works.
- [ ] User can submit / retry an answer and see the rubric.
- [ ] Help assistant works with guarded, scoped intents (no free-form chatbot behavior).
- [ ] Shareable readiness works **or** is explicitly deferred behind `ENABLE_PHASE6_SHARE_LINKS`.
- [ ] Usage shell is visible **or** explicitly deferred.

---

## 2. Technical Gates

- [ ] Backend tests pass.
- [ ] Frontend build / lint pass (if available).
- [ ] Old Phase 5 flows still work (no regressions).
- [ ] Migrations tested before deploy once code PRs begin.
- [ ] Local smoke passes.
- [ ] Render smoke passes.
- [ ] Feature flags documented (see [phase6_technical_scope.md](phase6_technical_scope.md)).

---

## 3. Privacy Gates

- [ ] No secrets / tokens / JWTs in docs or logs.
- [ ] No raw CV / JD / answer text in analytics.
- [ ] Share token stored hashed when implemented.
- [ ] Share view redacted by default when implemented.
- [ ] Cross-user access tests pass once code starts.

---

## 4. Analytics Gates

- [ ] GA4 critical events listed (see [phase6_api_contract.md](phase6_api_contract.md#7-analytics-events)).
- [ ] Event coverage table exists.
- [ ] Happy-path events verified.
- [ ] Negative / error-path events documented.
- [ ] No private text sent to analytics.

---

## 5. Demo Gates

- [ ] Demo data uses synthetic / non-sensitive content only.
- [ ] Demo health check exists by closeout.
- [ ] Deployed E2E report is PASS by closeout.
- [ ] Phúc / Quân / Đạt sign-off: Done.

---

## 6. Event Coverage Table (to be completed during closeout)

| Event | Happy path verified | Negative/error path | Notes |
|-------|---------------------|---------------------|-------|
| `target_job_created` | ☐ | ☐ | |
| `target_job_updated` | ☐ | ☐ | |
| `target_job_status_changed` | ☐ | ☐ | |
| `target_job_analysis_attached` | ☐ | ☐ | |
| `target_job_readiness_viewed` | ☐ | ☐ | |
| `target_job_package_opened` | ☐ | ☐ | |
| `learning_roadmap_generated` | ☐ | ☐ | |
| `learning_task_started` | ☐ | ☐ | |
| `learning_task_completed` | ☐ | ☐ | |
| `interview_session_created` | ☐ | ☐ | |
| `interview_question_generated` | ☐ | ☐ | |
| `interview_answer_submitted` | ☐ | ☐ | |
| `interview_feedback_viewed` | ☐ | ☐ | |
| `help_assistant_opened` | ☐ | ☐ | |
| `help_assistant_response_generated` | ☐ | ☐ | |
| `help_assistant_fallback_shown` | ☐ | ☐ | |
| `share_link_created` | ☐ | ☐ | |
| `share_link_opened` | ☐ | ☐ | |
| `share_link_revoked` | ☐ | ☐ | |
| `usage_page_viewed` | ☐ | ☐ | |

---

## 7. Related Documents

- [phase6_team_plan.md](phase6_team_plan.md) — ownership and weekly plan.
- [phase6_api_contract.md](phase6_api_contract.md) — endpoints, fields, and analytics events.
