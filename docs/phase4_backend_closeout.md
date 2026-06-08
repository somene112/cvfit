# Phase 4 Backend Closeout

## Status

Phase 4 backend scope owned by Phúc is production-smoke-passed. The deployed
backend supports Result JSON v3, linked reanalysis, comparison, DOCX report v3
sections, and the Phase 4 production smoke flow.

This note contains sanitized handoff evidence only. It does not include access
tokens, database URLs, storage paths, S3 keys, or other secrets.

## Completed Backend Scope

- Result JSON v3 additive enrichment while preserving v2 score aliases and
  response compatibility.
- Improvement Action Plan.
- Safe Rewrite Suggestions.
- Interview Prep Pack.
- Learning Roadmap.
- Reanalysis endpoint for linked revised-CV jobs.
- Comparison endpoint for before/after analysis.
- Keyword stuffing warnings for unsupported keyword-only improvements.
- DOCX Report v3 sections.
- Render Alembic runner for safer production migrations.
- Phase 4 production smoke script.

## Production Smoke Evidence

Sanitized Phase 4 deployed smoke summary:

```text
API base URL: https://cvfit.onrender.com
initial job id: a1331715-fe7b-4d00-ac09-88e34be54a66
child job id: 2f97d8b8-1437-4fba-8309-46fdea4412fe
schema_version: 3.0
docx_v3_sections_found: True
revision_number: 2
comparison_score_delta: 3.8
phase4 smoke test passed
```

Additional smoke observations:

- Read-only smoke returned `health ok`.
- Initial synthetic analysis completed with Result JSON v3.
- DOCX report downloaded successfully and included v3 sections.
- Reanalysis created a child job with revision metadata.
- Child Result JSON v3 returned successfully.
- Comparison endpoint returned the expected shape and safety checks passed.

## Operational Commands

Read-only Phase 4 deployed smoke:

```bat
cmd.exe /c "set API_BASE_URL=https://cvfit.onrender.com&& python scripts\smoke_test_phase4.py"
```

Mutating Phase 4 deployed smoke:

```bat
cmd.exe /c "set API_BASE_URL=https://cvfit.onrender.com&& set SMOKE_ALLOW_MUTATING=1&& python scripts\smoke_test_phase4.py --mutating"
```

Operational notes:

- Do not set `REQUIRE_RESULT_V2=1` for Phase 4 smoke.
- Mutating smoke creates synthetic jobs, uploads, and reports in production
  because the API has no cleanup endpoint.
- Run migrations before deploy when a PR includes Alembic migrations.
- Use `scripts/run_alembic.py` for Render migrations as documented in
  [render_deployment.md](render_deployment.md).
- Do not paste access tokens, token-bearing URLs, `DATABASE_URL`, storage
  paths, S3 keys, or screenshots containing secrets into docs, issues, PRs, or
  chat.
- Rotate/reset the database password if `DATABASE_URL` was exposed.

## API Handoff For Quân

Frontend can build against the current backend contracts:

- `GET /v1/jobs/{job_id}/result` now returns Result JSON v3 sections
  additively. Existing v2-compatible fields and score aliases remain present.
- `POST /v1/jobs/{job_id}/reanalyze` creates a linked revised-CV analysis job.
  Guest flow uses the parent `access_token`; logged-in flow uses owner auth.
- `GET /v1/jobs/{base_job_id}/comparison/{new_job_id}` returns score delta,
  evidence changes, resolved/still-missing gaps, keyword stuffing warnings, and
  next actions.
- DOCX report download now includes v3 sections when the result payload is v3.
- History includes revision metadata: `parent_job_id`, `analysis_group_id`, and
  `revision_number`.

Frontend reminders:

- Treat v3 fields as optional and render v2-compatible sections first.
- Do not log guest tokens or token-bearing URLs.
- Use comparison output as evidence quality guidance, not only as a score delta.
- Keep reanalysis jobs immutable; do not overwrite prior results in the UI.

## Evaluation And QA Handoff For Ð?t

Recommended Phase 4 QA/evaluation focus:

- Result JSON v3 fields exist and are list-shaped:
  `improvement_actions`, `safe_rewrite_suggestions`, `interview_prep`,
  `learning_roadmap`, and `limitations`.
- No fabricated skill, experience, employer, date, certification, ownership, or
  metric wording.
- No hiring guarantee wording.
- Missing evidence uses "not found in the parsed CV" semantics rather than
  claiming the user lacks a skill.
- Keyword stuffing warnings appear when revised CV text adds unsupported
  keyword-only matches.
- Comparison resolves gaps only when revised CV evidence supports the skill.
- Guest and owner auth cases for result, report, reanalysis, and comparison.
- DOCX v3 privacy redaction: no access tokens, token hashes, raw CV text,
  storage paths, local paths, S3 keys, report paths, bucket names, or secrets.

## Known Follow-Ups

- Frontend UI for action plan, safe rewrite, interview prep, learning roadmap,
  reanalysis, and comparison.
- Evaluation expansion for Phase 4 outputs.
- Cleanup endpoint or synthetic smoke artifact cleanup strategy.
- Rotate/reset database password because `DATABASE_URL` was exposed earlier.
- Optional future: add reanalysis/comparison frontend E2E smoke after UI exists.
