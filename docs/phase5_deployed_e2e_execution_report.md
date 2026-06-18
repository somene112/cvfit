# Phase 5 Deployed E2E Execution Report

## Metadata

- **Date/time:** 2026-06-17
- **Frontend URL:** https://cvfit-frontend.onrender.com
- **Backend URL:** https://cvfit.onrender.com
- **Main commit under test:** `ff71964` (feat(frontend): polish Phase 5 demo journey (#64))
- **Executor:** Authenticated API-level E2E (Claude Code) using a dedicated demo account.
- **Data rule:** Synthetic only. No real CV/JD/user data used.
- **Privacy note:** No credentials, tokens, cookies, JWTs, emails, secrets, S3 keys, database
  URLs, or raw API response bodies recorded. Object IDs redacted to first 6 chars + `...`.

---

## Summary

- **Overall status:** `PASS`
- **Route smoke:** Passed — all 8 frontend routes and backend `/health` return 200.
- **API-level E2E:** Passed — the full authenticated, data-mutating flow ran end-to-end against
  the deployed backend with synthetic data (login → attach analysis → interview Q&A → cover
  letter generate/save → package generate → report download → logout).
- **Browser GA4 verification:** Done — a manual browser walkthrough on the production frontend
  using the demo account and synthetic data was completed, and all 17 happy-path custom events
  were observed in GA4 Realtime. `cv_analysis_error` is a negative-path event and is **not
  required** for happy-path Phase 5 closeout.
- **Sign-off:** Done — Phúc / Quân / Đạt have all signed off.
- **Phase 5 completion:** Ready for closeout — route smoke, authenticated API-level E2E, and
  browser GA4 Realtime happy-path verification are all complete.

---

## Route smoke

| Route | Status | Result |
|---|---|---|
| `/` | 200 | PASS |
| `/dashboard` | 200 | PASS |
| `/applications` | 200 | PASS |
| `/applications/new` | 200 | PASS |
| `/profile` | 200 | PASS |
| `/profile/evidence` | 200 | PASS |
| `/learning` | 200 | PASS (new in #64) |
| `/help` | 200 | PASS (new in #64) |
| `GET /health` | 200 | PASS `{"status":"ok"}` |

Control: unknown route `/nonexistent-xyz-123` → 404 (confirms the 200s above are real routes).

---

## API/E2E steps

All calls authenticated as the demo account via Bearer token (token never printed). IDs redacted.

| Step | Result | Sanitized evidence | Notes |
|---|---|---|---|
| Backend health | PASS | `GET /health` → 200 `{"status":"ok"}` | |
| Frontend route smoke | PASS | 8 routes → 200; unknown → 404 | See Route smoke table |
| Login | PASS | `POST /v1/auth/login` → 200 | Token acquired, not shown |
| Auth/me | PASS | `GET /v1/auth/me` → 200 | Session valid |
| List job history | PASS | `GET /v1/jobs/history` → 200 | 11 jobs, 11 succeeded |
| Find completed analysis | PASS | succeeded job `302de3...` selected | No fresh analysis needed |
| Create synthetic application | PASS | `POST /v1/applications` → 201; app `e95011...` | Demo Company / Demo Frontend Developer |
| Load application detail | PASS | `GET /v1/applications/{id}` → 200 | |
| Attach analysis | PASS | `POST /v1/applications/{id}/attach-analysis/{job}` → 200 | Existing completed analysis attached |
| Create synthetic profile/evidence item | PASS | `POST /v1/profile/items` → 201; item `0c69a1...` | project: Demo React Portfolio |
| Load interview questions | PASS | `GET …/interview/questions` → 200 | count = 2 |
| Submit synthetic interview answer | PASS | `POST …/interview/answers` → 201 | Synthetic answer; rubric returned |
| Generate cover letter | PASS | `POST …/cover-letter/generate` → 201 | |
| Save/update cover letter | PASS | `PATCH …/cover-letter` → 200 | Edited closing section |
| Generate package/readiness | PASS | `POST …/package/generate` → 201 | Readiness produced |
| Download DOCX report | PASS | `GET /v1/jobs/{job}/report/download` → 200 | DOCX served (Bearer auth) |
| Logout | PASS | `POST /v1/auth/logout` → 200 | |

> Sanitized-evidence policy honoured: no tokens, cookies, emails, full IDs, or raw API response
> bodies recorded. IDs redacted to first 6 chars + `...`.

---

## Analysis-dependent steps

A completed analysis **was available**: the demo account's job history contained 11 succeeded
analyses. An existing succeeded analysis (`302de3...`) was attached to the synthetic application,
so **no fresh CV upload / `create-score` run was required**. All analysis-dependent steps —
attach analysis, interview questions + answer, cover letter generate/save, package generate, and
DOCX report download — executed and **passed**.

---

## GA4 event verification

> **Note:** The custom analytics events fire only in the **browser** via
> `window.dataLayer.push(...)`. The API-level E2E confirmed the backend capability behind each
> event; the events below were then confirmed in **GA4 Realtime** during a manual browser
> walkthrough on the production frontend using the demo account and synthetic data.

| Event | Status | Evidence/notes |
|---|---|---|
| landing_cta_click | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| login_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| language_switch | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| cv_analysis_submit | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| cv_analysis_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| cv_analysis_error | NOT_REQUIRED_FOR_HAPPY_PATH_CLOSEOUT | Negative-path event; not required for happy-path closeout. |
| result_view | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| download_report_click | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| application_create_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| application_detail_view | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| attach_analysis_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| profile_item_create_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| interview_start | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| interview_answer_submit_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| package_generate_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| cover_letter_generate_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| cover_letter_save_success | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |
| logout_click | VERIFIED_IN_GA4_REALTIME | Observed in GA4 Realtime during manual browser walkthrough. |

---

## Sign-off

| Owner | Area | Status | Notes |
|---|---|---|---|
| Phúc | Backend/deploy/docs | Done | API E2E passed; report finalized. |
| Quân | Frontend/UI + browser GA4 walkthrough | Done | Browser walkthrough completed; GA4 Realtime happy-path events verified. |
| Đạt | QA/evaluation/guardrails | Done | Synthetic E2E and analytics evidence reviewed. |

---

## Final verdict

**Phase 5 is ready for closeout.**

All closeout criteria are met:

1. Route smoke passed and all routes are healthy.
2. The authenticated, data-mutating API-level E2E passed end-to-end on the deployed backend.
3. Browser GA4 Realtime verification is complete — all 17 happy-path custom events were observed
   during a manual browser walkthrough on the demo account with synthetic data.
   (`cv_analysis_error` is a negative-path event and is not required for happy-path closeout.)
4. Owner sign-off (Phúc / Quân / Đạt) is Done.

Current status: `PASS`. **Phase 5 can be declared complete after PR #65 is reviewed and merged.**
Phase 6 planning can start after the PR #65 merge.

> Note: the synthetic application (`e95011...`), evidence item (`0c69a1...`), generated cover
> letter, and package created by this run were **left in place** on the demo account — they
> double as pre-seeded demo data per `docs/phase5_demo_seed_data.md`. No production data was deleted.
