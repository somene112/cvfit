# Phase 6 Learning Roadmap & Interview v2 — Backend Notes

> **PR:** Week 2 bundle (`feat: add learning roadmap and interview v2 backend`)
> **Date:** 2026-06-19
> **Scope:** Backend foundation only. No frontend UI; no Help Assistant / Share Links / Usage.

## Architecture / table decisions

- **Learning Roadmap:** new `learning_tasks` table. Generation **reuses** the existing
  `app/services/roadmap/learning_roadmap.py` deriver (`build_learning_roadmap`) and normalizes its
  output into persistable task rows.
- **Interview Practice v2:** three new tables — `interview_sessions`, `interview_session_questions`,
  `interview_session_answers`. The Phase 5 `interview_answers` table is **left untouched**. Question
  generation reuses `app/services/interview/interview_prep.py` (`build_interview_prep`); scoring is a
  new deterministic six-dimension rubric.
- **Constrained fields** (priority/task_type/status/difficulty/question_type) are stored as plain
  **strings** and validated at the Pydantic layer with `Literal`s — no native enum types, keeping the
  migration a plain additive `CREATE TABLE`.

## Migration

- `20260619_0001_add_learning_and_interview_sessions` — additive, `down_revision = 20260618_0001`.
- `EXPECTED_ALEMBIC_HEAD` updated to `20260619_0001` (single linear head).
- Fully backward compatible: no existing table/column/enum altered.

## Endpoints

All require auth and are scoped by `user_id`; cross-user access → **404**.

**Learning** (flag `ENABLE_PHASE6_LEARNING`, default true):
`POST /v1/learning/roadmaps/generate`, `GET /v1/learning/tasks`, `GET /v1/learning/tasks/{id}`,
`PATCH /v1/learning/tasks/{id}`, `POST /v1/target-jobs/{job_id}/learning/generate`.

**Interview v2** (flag `ENABLE_PHASE6_INTERVIEW_V2`, default true):
`POST /v1/interview/sessions`, `GET /v1/interview/sessions`, `GET /v1/interview/sessions/{id}`,
`POST .../questions/generate`, `POST .../answers`, `GET .../answers`, `GET .../summary`.

## Generation & scoring behavior

- Learning tasks derive **only** from the user's own analysis result (missing skills, matched
  evidence). No external/course-marketplace data, no scraping, no paid APIs. When no analysis context
  exists, a safe fallback set of profile-evidence tasks is returned with a clear `limitations` note.
- Interview scoring is deterministic across six dimensions: **relevance, evidence, clarity,
  structure, confidence, risk** (`risk` is inverse — higher = more interview risk). Answers claiming
  a flagged-missing skill, overclaiming, or being too vague raise `risk` and a `risk_flags` note.
- No "you will pass" guarantees anywhere; every summary/feedback carries an honest disclaimer.

## Ownership / privacy

- Questions/answers inherit ownership from their parent session.
- Generation never stores raw CV/JD text — only derived skills, titles, and descriptions.
- Interview answer text is stored as product data for the owner only.

## Analytics privacy note

Analytics/event payloads for these modules must **never** include:

- raw CV text
- raw JD text
- interview answer text
- JWTs, tokens, share tokens, secrets
- private IDs beyond non-sensitive event metadata (counts, statuses, dimension labels)

## Known limitations / deferred

- Frontend UI (`/learning`, `/interview/sessions`) is deferred to Quân.
- Scoring is rule-based/deterministic (no LLM) by design.
- Help Assistant, Share Links, and Usage remain out of scope.
