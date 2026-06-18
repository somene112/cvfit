# Phase 6 API Contract — Draft Only

> **Version:** 1.0 (draft)
> **Date:** 2026-06-18
> **Status:** Active — Phase 6 (planning)
> **Companion to:** [phase6_kickoff_plan.md](phase6_kickoff_plan.md)

> ⚠️ **Draft contract only.** Endpoint paths, fields, and shapes below are the *planned* surface.
> All endpoints are authenticated and scoped by the authenticated `user_id` unless explicitly marked
> public. No examples here contain real user data, tokens, JWTs, secrets, or raw CV/JD text.
>
> **Implementation status:** Target Jobs (§1) shipped — see
> [phase6_target_jobs_backend_notes.md](phase6_target_jobs_backend_notes.md). Learning Roadmap (§2)
> and Interview Practice v2 (§3) shipped in the Week 2 bundle — see
> [phase6_learning_interview_backend_notes.md](phase6_learning_interview_backend_notes.md).
> Help Assistant (§4) and Share Links (§5, flag-off by default) shipped in the Week 3 bundle — see
> [phase6_help_share_backend_notes.md](phase6_help_share_backend_notes.md) for as-built intents,
> token-hash/redaction rules, and feature flags. See
> [phase6_pr_tracking.md](phase6_pr_tracking.md) for logical-vs-actual PR numbers.

---

## 1. Target Jobs

A target job is a saved JD + status pipeline, optionally linked to an analysis.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/target-jobs` | Create a target job (title, company, JD text, source). |
| GET | `/v1/target-jobs` | List the caller's target jobs (filter by status). |
| GET | `/v1/target-jobs/{job_id}` | Get one target job. |
| PATCH | `/v1/target-jobs/{job_id}` | Update fields or status. |
| DELETE | `/v1/target-jobs/{job_id}` | Delete a target job. |
| POST | `/v1/target-jobs/{job_id}/attach-analysis/{analysis_job_id}` | Attach an existing analysis to the target job. |
| GET | `/v1/target-jobs/{job_id}/readiness` | Readiness summary derived from the attached analysis. |
| GET | `/v1/target-jobs/{job_id}/package` | Application package for the target job. |

### Statuses

```
saved
analyzing
ready_to_apply
interviewing
applied
rejected
offer
archived
```

---

## 2. Learning Roadmap

Generate and track learning tasks from analysis gaps, optionally scoped to a target job.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/learning/roadmaps/generate` | Generate roadmap tasks from an analysis/gap input. |
| GET | `/v1/learning/tasks` | List the caller's learning tasks (filter by status/target job). |
| GET | `/v1/learning/tasks/{task_id}` | Get one task. |
| PATCH | `/v1/learning/tasks/{task_id}` | Update a task (status/progress). |
| POST | `/v1/target-jobs/{job_id}/learning/generate` | Generate roadmap tasks scoped to a target job. |

### Task fields

| Field | Notes |
|-------|-------|
| `id` | Task id. |
| `user_id` | Owner. |
| `target_job_id` | Nullable. |
| `application_id` | Nullable. |
| `analysis_job_id` | Nullable. |
| `skill` | Skill the task addresses. |
| `category` | Skill category. |
| `priority` | Task priority. |
| `task_type` | e.g. course / project / certification / practice. |
| `title` | Short task title. |
| `description` | Task detail. |
| `evidence_to_add` | What evidence completing this should add to the CV. |
| `status` | e.g. not_started / in_progress / completed. |
| `created_at` | Timestamp. |
| `updated_at` | Timestamp. |

---

## 3. Interview Practice v2

Structured practice sessions with question generation, answers, rubric feedback, and history.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/interview/sessions` | Create a practice session. |
| GET | `/v1/interview/sessions` | List the caller's sessions. |
| GET | `/v1/interview/sessions/{session_id}` | Get one session. |
| POST | `/v1/interview/sessions/{session_id}/questions/generate` | Generate questions for the session. |
| POST | `/v1/interview/sessions/{session_id}/answers` | Submit (or retry) an answer. |
| GET | `/v1/interview/sessions/{session_id}/answers` | List answers in the session. |
| GET | `/v1/interview/sessions/{session_id}/summary` | Session summary across answers. |

### Rubric

```
relevance
evidence
clarity
structure
confidence
risk
```

---

## 4. Help Assistant

A guided, scoped career-coach assistant over a fixed intent set — **not** a free-form chatbot.

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/help/assistant` | Answer a scoped intent grounded in the caller's data. |
| GET | `/v1/help/suggestions` | Context-aware suggested next actions. |

### Supported intents

```
next_best_action
explain_score
explain_gap
suggest_learning
suggest_interview_practice
explain_application_status
help_product_usage
```

Requests outside these intents return a guarded fallback (no free-form generation,
no hallucinated advice).

### Response shape

| Field | Notes |
|-------|-------|
| `answer` | Scoped, grounded answer text. |
| `based_on` | What data the answer was grounded in (ids/labels, no raw private text). |
| `recommended_actions` | List of concrete in-product next actions. |
| `limitations` | Honest statement of what the assistant cannot do / did not consider. |

---

## 5. Share Links

Recruiter-lite share links to a redacted readiness summary. **Gated behind
`ENABLE_PHASE6_SHARE_LINKS=false` until privacy review passes.**

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/share-links` | Create a share link (returns raw token once, to the owner only). |
| GET | `/v1/share-links` | List the caller's share links (no raw tokens). |
| GET | `/v1/share-links/{id}` | Get one share link's metadata. |
| PATCH | `/v1/share-links/{id}` | Update (e.g. expiry, redaction settings). |
| DELETE | `/v1/share-links/{id}` | Revoke a share link. |
| GET | `/v1/public/share/{token}` | Public, redacted readiness view resolved by token. |

### Security notes

- **Store only the token hash** — never persist the raw token.
- **Never log the raw token.**
- **Support revoke** — a revoked link returns not-found/gone.
- **Support optional expiry** — expired links stop resolving.
- **Redact raw CV/JD/private evidence by default** on the public view.

---

## 6. Usage Shell

Read-only usage and plan visibility. **No real payment, no checkout, no fake paid plan.**

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/usage/me` | The caller's usage counters. |
| GET | `/v1/plans` | Static plan descriptions / limits (informational). |

### Usage categories

```
analyses
interview answers
cover letters
application packages
share links
```

### Clarifications

- **No real payment.**
- **No checkout.**
- **No fake paid plan** — plans are informational descriptions of limits only.

---

## 7. Analytics Events

Critical GA4 events fired by Phase 6 surfaces.

| Event | Fired when |
|-------|-----------|
| `target_job_created` | A target job is created. |
| `target_job_updated` | A target job's fields are updated. |
| `target_job_status_changed` | A target job's status changes. |
| `target_job_analysis_attached` | An analysis is attached to a target job. |
| `target_job_readiness_viewed` | The readiness summary is viewed. |
| `target_job_package_opened` | The application package is opened. |
| `learning_roadmap_generated` | A learning roadmap is generated. |
| `learning_task_started` | A learning task moves to in_progress. |
| `learning_task_completed` | A learning task is completed. |
| `interview_session_created` | A practice session is created. |
| `interview_question_generated` | Questions are generated for a session. |
| `interview_answer_submitted` | An answer is submitted. |
| `interview_feedback_viewed` | Rubric feedback is viewed. |
| `help_assistant_opened` | The help assistant is opened. |
| `help_assistant_response_generated` | The assistant returns a scoped answer. |
| `help_assistant_fallback_shown` | The guarded fallback is shown. |
| `share_link_created` | A share link is created. |
| `share_link_opened` | A public share link is opened. |
| `share_link_revoked` | A share link is revoked. |
| `usage_page_viewed` | The usage page is viewed. |

### Analytics privacy rule

> **Never send raw CV text, raw JD text, interview answer text, share tokens, JWTs, private IDs,
> or secrets to analytics.** Send event names and non-sensitive metadata (counts, statuses,
> category labels) only.

---

## 8. Related Documents

- [phase6_technical_scope.md](phase6_technical_scope.md) — route/service layout and feature flags.
- [phase6_acceptance_criteria.md](phase6_acceptance_criteria.md) — gates per module.
