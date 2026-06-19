# Phase 6 Funnel Dashboard Spec

> **Date:** 2026-06-19
> **Demo caveat:** All funnel data in the demo is from **synthetic/demo accounts only**.
> No real user data is present.

## Funnel stages

| # | Stage (event) | Definition |
|---|---------------|------------|
| 1 | `landing_view` | Visitor loads the landing page. |
| 2 | `auth_success` | User signs up or logs in successfully. |
| 3 | `target_job_created` | User saves a first target job. |
| 4 | `analysis_started` | User starts a CV/JD analysis. |
| 5 | `analysis_succeeded` | Analysis completes successfully. |
| 6 | `target_job_analysis_attached` | Analysis attached to a target job. |
| 7 | `learning_roadmap_generated` | A learning roadmap is generated. |
| 8 | `interview_session_created` | An interview practice session is created. |
| 9 | `help_assistant_response_generated` | The assistant returns a scoped answer. |
| 10 | `share_link_created` | A share link is created (only when flag on). |
| 11 | `usage_page_viewed` | User opens the usage page. |

## Drop-off interpretation

- **1→2 (landing→auth):** acquisition/onboarding friction.
- **2→3 (auth→target job):** activation — did the user grasp the core workflow?
- **3→6 (target job→analysis attached):** core value moment (readiness unlocked).
- **6→7/8 (attach→learning/interview):** depth of engagement with prep tools.
- **8→9 (interview→assistant):** guidance usage; high fallback rate signals data gaps.
- **10 (share):** advocacy — expected low in demo since share links are flag-off by default.
- **11 (usage):** awareness of limits; informational only (no paywall).

## Demo notes

- Share-link stages will be near-zero unless `ENABLE_PHASE6_SHARE_LINKS` is enabled for
  the demo environment after privacy review.
- Treat absolute counts as illustrative; focus on stage-to-stage conversion shape.
