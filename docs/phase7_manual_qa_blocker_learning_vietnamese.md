# Pre-Phase-7 Manual QA — Learning + Vietnamese Blocker

Records the manual production QA progress and the fix for the Section 3 (Learning)
blocker plus the most-visible Vietnamese result-page copy. Payment remains paused
(`ENABLE_BILLING=false`, `ENABLE_CREDIT_GATING=false`).

## Manual QA progress

| Section | Result |
| --- | --- |
| 1. Admin | **PASS** — admin dashboard + Analytics v2 (funnel, 7/30-day, depth, billing readiness) render; billing "Chưa bật"; no private content. |
| 2. Pricing/Billing | **PASS** — VI plan names ("Gói khởi đầu", "Gói demo Pro"), prices 20.000đ / 49.000đ; `/billing` safe, not implying live payment. |
| 3. Learning | **BLOCKED before this PR** → fixed here (retest required after deploy). |
| 4–8 | Not yet reached (resume after retest). |

## Root cause (Section 3 — Learning)

- CV analysis writes a `learning_roadmap` array **inside** `result_json` (via the
  result_v3 assembly) but does **not** persist `LearningTask` rows.
- `LearningTask` rows are created **only** by a generate endpoint
  (`POST /v1/learning/roadmaps/generate` or the target-job variant).
- `/learning` lists `LearningTask` rows, so after a fresh analysis it was empty —
  and its empty state told the user to "Chạy phân tích CV" (analyze again), which
  is wrong when the user just analyzed.
- Additionally, several analysis-result strings are generated deterministically in
  English (`result_v2`/`result_v3` + interview-prep/roadmap generators), so they
  showed in English even in VI mode (score labels, explanations, interview-prep
  questions, roadmap text).

## Fix summary (this PR)

**Learning (the blocker):**
- `/learning` empty state now checks for the user's latest **succeeded** analysis
  (via the existing `GET /v1/jobs/history` — safe metadata only). If one exists, it
  shows a Vietnamese CTA **"Tạo lộ trình học tập từ phân tích gần nhất"** that calls
  `POST /v1/learning/roadmaps/generate` with that `analysis_job_id` and
  `language=vi`, then reloads the task list. If there is genuinely no analysis, the
  original "Chạy phân tích CV" CTA remains. No raw "Not Found" is ever shown.
- The learning-task generator (`generate_learning_tasks`) gained an optional
  `language` param (default `en`); with `vi` the task title/description/evidence
  prose is Vietnamese (skill/tech names preserved). Threaded through the generate
  endpoint via `RoadmapGenerateRequest.language`.

**Vietnamese result copy (fixed deterministic strings):**
- A frontend map (`utils/resultI18n.js`) localizes the **score-breakdown labels**
  (Mức độ khớp kỹ năng / Mức độ khớp trách nhiệm / Mức kinh nghiệm / Mức độ liên
  quan dự án / Chất lượng CV), their **explanations**, and the **limitation
  disclaimers**, applied in `ResultCardV2.jsx`. Backend response contract unchanged.

**Backend language threading (follow-up applied in-place on this PR):**
- `run_job.delay` and the worker now accept a `language` parameter (default `en`).
- `result_v2` and `result_v3` thread `language` through to the deterministic
  result prose: **summary**, **score labels/explanations**, **limitations**,
  **missing-skill reasons/suggestions**, **improvement actions**, **safe-rewrite
  suggestions**, **interview-prep questions/hints**, and **learning-roadmap task
  titles/descriptions/evidence**.
- Vietnamese variants live in a per-service i18n helper; skill/tech/JD tokens
  stay untranslated.
- New `backend/tests/test_vietnamese_analysis_pipeline.py` pins the language
  threading end-to-end (job → worker → result_v2/v3 → service prose).
- Existing phase-3 result tests were updated to pass `language="en"` to
  `run_job.delay` (signature change, no behavior change for EN).
- Dashboard default language was switched to `vi` so new users see Vietnamese
  on first load.

## Out of scope (documented)

- **Historical analyses** stored before this deploy remain partly English
  unless regenerated, because the localized prose is only written by the
  updated pipeline. Fresh analyses after deploy are fully Vietnamese (VI mode).
- No payment rollout, credit-gating live, fake data, or admin mutations.

## Retest required after deploy

Redeploy latest `main` (backend + frontend), keep flags false, then:
1. Run a **fresh** CV analysis (so the new pipeline writes localized prose).
2. Open `/learning` → confirm the **"Tạo lộ trình học tập từ phân tích gần nhất"**
   CTA (not "analyze again"); click it → Vietnamese tasks appear.
3. Open the analysis result → confirm **summary**, **score labels/explanations**,
   **limitations**, **missing-skill reasons/suggestions**, **improvement
   actions**, **safe-rewrite suggestions**, **interview-prep questions**, and
   **learning-roadmap text** are Vietnamese (skill/tech names preserved).
4. Resume manual QA Sections 4–8 (Help, Interview, Cover letter, Package, Flags).
