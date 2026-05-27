# Phase 1 Closeout PR Summary

## What changed

- Added guest-mode access-token protection for result, report metadata, and report download endpoints.
- Preserved backend compatibility for both documented frontend fields and existing fallback UI fields.
- Added a repeatable deployed-backend smoke script at `scripts/smoke_phase1_backend.py`.
- Added and validated Alembic baseline migration readiness on disposable PostgreSQL/pgvector.
- Added and applied S3 lifecycle cleanup policy for temporary uploads, raw uploads, generated reports, and incomplete multipart uploads.
- Updated closeout documentation, API contract, runbooks, and Phase 2 product scope.

## Evidence

- `python -m pytest -q`: 60 passed.
- Render backend smoke passed against `https://cvfit.onrender.com`.
- Live smoke verified health, CV upload, create-score, worker completion, missing/wrong access-token rejection, correct-token result/report/download, and DOCX download.
- Alembic single head `20260522_0001` validated with `alembic upgrade head` on disposable PostgreSQL/pgvector; production DB was not touched.
- S3 lifecycle policy applied to bucket `2026-fpt-exe-app` in region `ap-southeast-2`; rules were read back and verified.

## How to test

```cmd
python -m pytest -q
python -m json.tool infra/s3-lifecycle.json
python -m py_compile scripts/smoke_phase1_backend.py
git diff --check
```

For deployed backend smoke with a dummy CV only:

```cmd
set API_BASE_URL=https://cvfit.onrender.com
set TEST_CV_PATH=backend\pytest-tmp\dummy_cv.docx
set SMOKE_TIMEOUT_SECONDS=300
python scripts\smoke_phase1_backend.py
```

Do not use a real personal CV for smoke testing.

## Known non-goals

- No full login, user accounts, OAuth, password reset, or user history.
- No frontend rewrite and no new product feature work.
- No manual S3 object deletion.
- No production database migration or stamp was performed as part of this closeout audit.

## Remaining Phase 2 items

- Quân should separately validate the Next frontend if/when the Next app is present.
- Decide whether the demo uses the current FastAPI-served Jinja/vanilla JS fallback or a separately deployed Next frontend.
- Use `docs/phase1_demo_script.md` for the 3-5 minute Phase 1 demo and fallback path.
- Implement Phase 2 product polish: richer result dashboard, evidence-based feedback, rewrite assistant guardrails, interview readiness, roadmap/history strategy, and login/history ADR.
