# Render Deployment Guide

This guide prepares the app for an MVP/demo deployment on Render. It does not deploy anything and does not include secrets.

For the step-by-step service setup handoff, use the [Render manual setup checklist](render_manual_setup_checklist.md). For the real Phase 1 deployment trial runbook, use [Phase 1 Render execution](phase1_render_execution.md).

## MVP Architecture

- Render Web Service: FastAPI API and current Jinja/vanilla JS frontend.
- Render Background Worker: Celery worker for CV parsing, JD parsing, scoring, and DOCX report generation.
- Render Redis/Key Value: Celery broker and result backend.
- Render Postgres: application database. Use a PostgreSQL option that supports the `vector` extension.
- S3-compatible object storage: private storage for uploaded CV files and generated DOCX reports.

S3-compatible storage must be accessed through the app storage service and SDK. Do not mount S3 as a filesystem.

## Required Environment Variables

API and worker:

```env
DATABASE_URL=
REDIS_URL=
STORAGE_BACKEND=s3
STORAGE_ROOT=./data
S3_BUCKET=
S3_REGION=
S3_ENDPOINT_URL=
S3_PREFIX=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_USE_IAM_ROLE=false
CV_MAX_UPLOAD_MB=10
```

Notes:

- `STORAGE_BACKEND=local` is only for local development.
- `S3_BUCKET` and `S3_REGION` are required when `STORAGE_BACKEND=s3`.
- `S3_ENDPOINT_URL` is optional for AWS S3 and required by some S3-compatible providers such as MinIO, Cloudflare R2, or Wasabi. Set it only when the provider requires a custom endpoint.
- On Render, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as secret environment variables unless using an object-storage provider with another supported credential mechanism.
- Set the same storage, database, Redis, and upload-limit environment variables on both the Render API service and the Render worker service.
- API and worker must share the same `DATABASE_URL`, `REDIS_URL`, `STORAGE_BACKEND`, and S3 environment variables.
- For future AWS deployments, prefer IAM roles and set `AWS_USE_IAM_ROLE=true`.
- Keep `STORAGE_ROOT` defined even when using S3; it remains useful for temporary/local development paths.
- Do not commit secrets to git, docs, tickets, or smoke-test logs.

## Suggested Render Commands

API Web Service:

```bash
cd backend && pip install -r requirements.txt
```

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Background Worker:

```bash
cd backend && pip install -r requirements.txt
```

```bash
cd backend && celery -A app.workers.celery_app:celery_app worker --loglevel=INFO -Q cvfit
```

The API and worker do not run migrations at startup. Before starting or
restarting services against a database after a PR with new Alembic migrations,
apply the reviewed migrations from a trusted operator environment. For Render,
prefer `scripts/run_alembic.py` through the deployed Python interpreter instead
of relying on an `alembic` executable on `PATH`. For an existing Render
database, take a backup and run the schema/adoption checks described in
[database_migrations.md](database_migrations.md) before upgrading or stamping.

## Render Database Migration Commands

Run these from the Render Shell for the API service after deployment has built
the new code and before starting or restarting API/worker against the new
schema. Render service shells already have the service environment variables,
including `DATABASE_URL`.

```bash
cd /opt/render/project/src
/opt/render/project/src/.venv/bin/python scripts/run_alembic.py current
/opt/render/project/src/.venv/bin/python scripts/run_alembic.py heads
/opt/render/project/src/.venv/bin/python scripts/run_alembic.py upgrade head
/opt/render/project/src/.venv/bin/python scripts/run_alembic.py current
/opt/render/project/src/.venv/bin/python scripts/check_db_schema.py
```

If you must run the same migration from local Windows, use the Render External
Database URL, not the Render Internal Database URL:

```bat
set "DATABASE_URL=<external-render-postgres-url>"
python scripts\run_alembic.py current
python scripts\run_alembic.py heads
python scripts\run_alembic.py upgrade head
python scripts\run_alembic.py current
python scripts\check_db_schema.py
set "DATABASE_URL="
```

Do not use a Render Internal Database URL from local; it is only reachable from
Render's private network. Do not paste `DATABASE_URL` into logs, docs, PRs,
screenshots, or chat. Rotate the database password if the URL was exposed.

## Pre-Deploy Checklist

Before creating Render services:

1. Confirm `cd backend && pip install -r requirements-dev.txt && python -m pytest` passes locally.
2. Confirm `docker compose config` renders successfully.
3. Run the local Docker smoke test below.
4. Choose the S3-compatible provider and confirm whether it needs `S3_ENDPOINT_URL`.
5. Create a private object-storage bucket and prefix for the MVP.
6. Run the S3-backed smoke test in [s3_smoke_test.md](s3_smoke_test.md).
7. Set the required environment variables on both Render services.
8. Confirm the Render database is initialized or safely adopted to Alembic head before starting API/worker runtime.
9. Confirm uploaded CVs and reports are not committed to git.

## Local Docker Smoke Test

Start the full local stack:

```bash
docker compose down -v
docker compose up --build -d postgres redis
DATABASE_URL=postgresql+psycopg2://cvfit:cvfit@localhost:5432/cvfit \
python scripts/run_alembic.py upgrade head
docker compose up --build -d
```

Run the smoke test:

```bash
python scripts/smoke_test_local.py
```

Expected success criteria:

- `/health` is reachable.
- CV upload returns `cv_file_id`.
- Score job reaches `succeeded`.
- Result JSON contains `scores.fit_score`.
- Report metadata does not contain `local_path`.
- DOCX report download returns non-empty bytes.

Shut the stack down after testing:

```bash
docker compose down
```

## Local Docker E2E Smoke Test Passed

Pre-Render local Docker verification was run successfully with:

```bash
python -m compileall backend/app
cd backend && python -m pytest
docker compose config
docker compose down -v
docker compose up --build -d
docker compose ps
python scripts/smoke_test_local.py
docker compose down
```

Expected successful smoke output includes:

```text
health ok
uploaded cv_file_id=<uuid>
created job_id=<uuid>
job status=succeeded progress=100
fit_score=<number>
report metadata ok: {'format': 'docx', 'download_url': '/v1/jobs/<job_id>/report/download'}
downloaded report bytes=<non-zero>
smoke test passed
```

This is the required pre-Render verification step for the current MVP architecture.

## S3-Backed Smoke Test

Before deploying to Render, run the S3-backed smoke test with a private bucket or S3-compatible provider:

```bash
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.s3.yml up --build -d
python scripts/smoke_test_s3.py
docker compose -f docker-compose.yml -f docker-compose.s3.yml down
```

See [s3_smoke_test.md](s3_smoke_test.md) for required environment variables, provider notes, and expected output.

After the app is manually deployed on Render, start with the read-only MVP smoke
check from your local machine:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_mvp.py
```

Expected read-only success output includes:

```text
health ok
read-only smoke completed
mutating smoke is skipped by default
```

Run the full deployed upload-to-report smoke only when you intentionally want
to create one synthetic job/report in the deployed app:

```bash
API_BASE_URL=https://<render-api-url> SMOKE_ALLOW_MUTATING=1 python scripts/smoke_test_mvp.py --mutating
```

PowerShell equivalent:

```powershell
$env:API_BASE_URL="https://<render-api-url>"
$env:SMOKE_ALLOW_MUTATING="1"
python scripts/smoke_test_mvp.py --mutating
Remove-Item Env:SMOKE_ALLOW_MUTATING
```

Do not set `DATABASE_URL` for smoke testing. Do not use real CVs or private
personal data. The mutating smoke script creates a tiny synthetic DOCX upload,
score job, result, and report. The current API has no cleanup endpoint, so the
synthetic smoke job/report remains in app storage and database records.

## Phase 4 Production Smoke Test

Use `scripts/smoke_test_phase4.py` after the API and worker are deployed. If a
PR includes migrations, run the documented Render migration commands first.
Do not set `REQUIRE_RESULT_V2=1` for this smoke; Phase 4 expects Result JSON
v3.

Read-only mode checks deployed health only and explains the mutating flow:

```bat
cmd.exe /c "set API_BASE_URL=https://cvfit.onrender.com&& python scripts\smoke_test_phase4.py"
```

Mutating mode runs the full Phase 4 deployed flow:

```bat
cmd.exe /c "set API_BASE_URL=https://cvfit.onrender.com&& set SMOKE_ALLOW_MUTATING=1&& python scripts\smoke_test_phase4.py --mutating"
```

The mutating Phase 4 smoke:

- Uploads an initial synthetic DOCX CV.
- Creates an initial analysis job and waits for completion.
- Verifies Result JSON v3 fields.
- Downloads the DOCX report and verifies v3 report sections when DOCX text can
  be parsed.
- Reanalyzes the initial job with a revised synthetic CV.
- Waits for the child job, fetches child Result JSON v3, and calls the
  comparison endpoint.
- Verifies comparison response shape and checks for sensitive internal fields.

Tokens and token-bearing URLs are redacted from script output. Do not paste
access tokens, `DATABASE_URL`, storage paths, or screenshots containing secrets
into docs, tickets, PRs, or chat.

The mutating smoke creates real test jobs, uploaded CV objects, and generated
report objects in the deployed environment. The current API has no cleanup
endpoint, so use synthetic content only.

## Health Check

Use:

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

## Production-Safe MVP Smoke Test

Use `scripts/smoke_test_mvp.py` for deployed MVP checks.

Read-only mode:

- Requires `API_BASE_URL`.
- Calls only `GET /health`.
- Prints the mutating flow that would be tested.
- Does not require or read `DATABASE_URL`.

Mutating mode:

- Requires `API_BASE_URL`.
- Requires `SMOKE_ALLOW_MUTATING=1`.
- Requires `--mutating`.
- Uses only tiny synthetic CV/JD content.
- Uploads one DOCX, creates one score job, polls to a terminal state, fetches
  result JSON, and downloads the DOCX report.
- Uses bounded polling; override with `SMOKE_TIMEOUT_SECONDS=<seconds>`.
- Does not print access tokens.
- Leaves one synthetic job/report because there is no cleanup endpoint.

Troubleshooting:

- Wrong `API_BASE_URL`: confirm it includes `https://` and has no path suffix.
- Render cold start: rerun read-only smoke after the service wakes up.
- Worker not running: mutating smoke may remain queued or time out; inspect the
  worker service and shared `REDIS_URL` configuration.
- Storage/S3 error: mutating smoke may fail during upload or report download;
  confirm API and worker share bucket, prefix, region, endpoint, and credentials.
- Job timeout: increase `SMOKE_TIMEOUT_SECONDS` only after checking worker logs.
- Report download failure: confirm the job reached `succeeded` and API/worker
  share the same database and storage configuration.

## Known Limitations

- Current app still has no full auth.
- Job status polling remains UUID-based; result, report metadata, and report download use MVP access-token protection.
- Render environment variables must be set for both the API and worker services.
- S3 integration must be smoke-tested with a real private bucket before demo use.
- S3 lifecycle cleanup is still needed for uploaded CVs and generated reports.
- Render free tier is suitable only for demo/testing, not production.
- The first scoring run may be slower if the embedding model has to download at runtime.
- API and worker startup verify schema state but do not silently create or patch database schema. Missing or outdated schema must be fixed through Alembic.

## Manual Smoke Test Checklist

After deployment:

1. Open the Web Service URL.
2. Confirm `GET /health` returns `{"status":"ok"}`.
3. Upload a small PDF CV under `CV_MAX_UPLOAD_MB`.
4. Paste a JD longer than 30 characters.
5. Submit the score request and confirm the UI moves through queued/running/succeeded.
6. Confirm the result card shows a fit score and score breakdown.
7. Download the DOCX report.
8. Confirm the object-storage bucket contains one upload object and one report object under `S3_PREFIX`.
9. Try uploading `.doc` or `.txt` and confirm the API rejects it cleanly.
10. Review Render logs for uncaught exceptions or S3 credential errors.

## render.yaml

This repo does not include a `render.yaml` blueprint yet. Service names, plans, regions, object-storage provider, and secret management choices are still project-specific, so a blueprint would be easy to make misleading. Add one after those choices are confirmed.
