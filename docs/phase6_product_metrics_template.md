# Phase 6 Product Metrics Template

> **Date:** 2026-06-19
> Fill in per reporting window (demo: synthetic data only). Source = GA4 events
> ([phase6_analytics_event_plan.md](phase6_analytics_event_plan.md)) and/or backend
> `GET /v1/usage/me` aggregates.

| Metric | Definition | Event / source | Value |
|--------|------------|----------------|-------|
| Target jobs created | Count of `target_job_created` | GA4 / usage.applications | |
| Analyses per user | analyses ÷ active users | usage.analyses | |
| Learning tasks generated | Count of `learning_roadmap_generated` tasks | GA4 / usage.learning_tasks | |
| Learning tasks completed | Count of `learning_task_completed` | GA4 | |
| Interview sessions created | Count of `interview_session_created` | usage.interview_sessions | |
| Interview answers submitted | Count of `interview_answer_submitted` | usage.interview_answers | |
| Share links created | Count of `share_link_created` | usage.share_links | |
| Packages generated | Count of application packages | usage.application_packages | |
| Conversion to ready_to_apply | target jobs reaching `ready_to_apply` ÷ created | target job status | |
| Error rate / failed jobs | failed analyses ÷ total analyses | backend job status | |
| Usage page views | Count of `usage_page_viewed` | GA4 | |
| Plan card views | Count of `plan_card_viewed` | GA4 | |

## Guardrails

- No metric should require raw CV/JD/answer text, tokens, or PII.
- Score-based metrics use buckets, not exact values.
- All demo figures are labeled synthetic.
