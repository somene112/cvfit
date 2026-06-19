# Phase 6 Analytics Event Plan

> **Date:** 2026-06-19
> **Status:** Demo-ready. GA4-oriented; events are fired from the frontend unless noted.

## Privacy rule (applies to every event)

**Never** include these as event properties: raw CV text, raw JD text, interview
answer text, share tokens, `token_hash`, JWTs, secrets/API keys, or email addresses
(unless explicitly required and hashed). Prefer IDs/labels/counts/enums over content.
Private object IDs should be omitted when a non-identifying label suffices.

## Event coverage

| Event | Trigger | Owner | Source | Required props | Forbidden props |
|-------|---------|-------|--------|----------------|-----------------|
| `landing_view` | Landing page load | Quân | FE | `page` | any PII |
| `signup` / `login` | Auth success | Quân | FE | `method` | password, JWT, raw email |
| `target_job_created` | Target job created | Quân | FE | `status` | raw JD text |
| `target_job_updated` | Target job edited | Quân | FE | `field_changed`, `status` | raw JD text |
| `target_job_analysis_attached` | Analysis attached | Quân | FE | `readiness_level` | raw CV/JD |
| `target_job_readiness_viewed` | Readiness opened | Quân | FE | `readiness_level`, `fit_score_bucket` | raw CV/JD |
| `learning_roadmap_generated` | Roadmap generated | Quân | FE | `task_count` | raw CV/JD |
| `learning_task_started` | Task → in_progress | Quân | FE | `task_type`, `priority` | task free text |
| `learning_task_completed` | Task → done | Quân | FE | `task_type` | task free text |
| `interview_session_created` | Session created | Quân | FE | `session_type`, `difficulty` | — |
| `interview_question_generated` | Questions generated | Quân | FE | `question_count`, `question_type` | question text |
| `interview_answer_submitted` | Answer submitted | Quân | FE | `attempt_number` | **answer text** |
| `interview_feedback_viewed` | Rubric viewed | Quân | FE | `overall_bucket` | answer text |
| `help_assistant_opened` | Assistant opened | Quân | FE | `entry_point` | — |
| `help_assistant_response_generated` | Scoped answer returned | Quân | FE | `intent`, `fallback_used` | answer/CV/JD text |
| `help_assistant_fallback_shown` | Guarded fallback shown | Quân | FE | `intent` | — |
| `share_link_created` | Share link created | Quân | FE | `target_type` | **share token, token_hash** |
| `share_link_opened` | Public view opened | Quân | FE | `target_type` | **share token** |
| `share_link_revoked` | Link revoked | Quân | FE | — | **share token** |
| `usage_page_viewed` | Usage page opened | Quân | FE | `plan_id` | — |
| `plan_card_viewed` | Plan card opened | Quân | FE | `plan_id` | price/checkout |
| `limit_warning_shown` | Soft usage warning shown | Quân | FE | `category` | raw counts of others |

## Notes

- Phase 6 backend is the source of truth for the data these events summarize; the
  backend itself does not emit analytics (no PII leaves the API in logs).
- `fit_score_bucket`/`overall_bucket` are coarse ranges (e.g. `0-54`, `55-74`, `75-100`)
  rather than exact scores, to avoid fingerprinting.
- See [phase6_funnel_dashboard_spec.md](phase6_funnel_dashboard_spec.md) and
  [phase6_product_metrics_template.md](phase6_product_metrics_template.md).
