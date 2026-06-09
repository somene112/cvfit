# Render Manual Setup Checklist

This checklist prepares a manual Render deployment for the Phase 1 MVP baseline. It does not deploy anything, does not include secrets, and does not add product features.

## Architecture

- Render Web Service: FastAPI API plus the existing Jinja/vanilla JS frontend.
- Render Background Worker: Celery worker on the `cvfit` queue.
- Render Redis/Key Value: Celery broker and result backend.
- Render Postgres: application database. Choose an option that supports the `vector` extension.
- S3-compatible object storage: private bucket for uploaded CV files and generated DOCX reports.

API and worker must share the same `DATABASE_URL`, `REDIS_URL`, `STORAGE_BACKEND`, and S3 environment variables. Do not commit secrets to the repo or to docs.

## Render Web Service

Create a Render Web Service from this repository branch.

- Environment: Python or Docker-compatible Render service.
- Root directory: repository root.
- Build command:

```bash
cd backend && pip install -r requirements.txt
```

- Start command:

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Health check path:

```text
/health
```

Expected health response:

```json
{"status":"ok"}
```

## Render Background Worker

Create a Render Background Worker from the same repository branch.

- Environment: Python or Docker-compatible Render service.
- Root directory: repository root.
- Build command:

```bash
cd backend && pip install -r requirements.txt
```

- Start command:

```bash
cd backend && celery -A app.workers.celery_app:celery_app worker --loglevel=INFO -Q cvfit
```

The worker must use the same database, Redis, storage backend, bucket, prefix, region, endpoint, and S3 credentials as the API service.

## Redis / Key Value

Create a Render Redis or Key Value instance for Celery.

- Copy the internal Redis URL into `REDIS_URL`.
- Set the same `REDIS_URL` on the API and worker.
- Do not use a local Redis URL in Render.

## Postgres

Create a Render Postgres database.

- Use a PostgreSQL plan/provider that supports the `vector` extension.
- Copy the internal database URL into `DATABASE_URL`.
- Set the same `DATABASE_URL` on the API and worker.
- App startup verifies schema state but does not create tables or patch columns.
- Initialize an empty database with Alembic, or safely adopt an existing database after backup and schema checks.

## S3 Environment Setup

Create or choose a private S3-compatible bucket before the first Render smoke test.

Set these values on both API and worker:

```env
STORAGE_BACKEND=s3
STORAGE_ROOT=./data
S3_BUCKET=<private-bucket-name>
S3_REGION=<provider-region>
S3_ENDPOINT_URL=<provider-endpoint-if-required>
S3_PREFIX=<render/test/prefix>
AWS_ACCESS_KEY_ID=<secret>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_USE_IAM_ROLE=false
CV_MAX_UPLOAD_MB=10
```

Notes:

- `S3_ENDPOINT_URL` is optional for AWS S3 and often required for S3-compatible providers such as Cloudflare R2, MinIO, Wasabi, or Backblaze B2.
- Keep the bucket private.
- Use a disposable prefix for smoke tests, such as `cvfit/render-smoke/<date>`.
- S3 lifecycle cleanup is still needed so old uploads and generated reports do not accumulate.

## Required API Environment Variables

```env
DATABASE_URL=<render-postgres-internal-url>
REDIS_URL=<render-redis-internal-url>
STORAGE_BACKEND=s3
STORAGE_ROOT=./data
S3_BUCKET=<private-bucket-name>
S3_REGION=<provider-region>
S3_ENDPOINT_URL=<provider-endpoint-if-required>
S3_PREFIX=<render/test/prefix>
AWS_ACCESS_KEY_ID=<secret>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_USE_IAM_ROLE=false
CV_MAX_UPLOAD_MB=10
```

Render provides `PORT` for the Web Service start command.

## Required Worker Environment Variables

```env
DATABASE_URL=<same-as-api>
REDIS_URL=<same-as-api>
STORAGE_BACKEND=s3
STORAGE_ROOT=./data
S3_BUCKET=<same-as-api>
S3_REGION=<same-as-api>
S3_ENDPOINT_URL=<same-as-api-if-used>
S3_PREFIX=<same-as-api>
AWS_ACCESS_KEY_ID=<secret>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_USE_IAM_ROLE=false
CV_MAX_UPLOAD_MB=10
```

The worker does not need `PORT`.

## Optional Local Env Contract Check

The helper script checks the current shell or a local env file without printing secret values:

```bash
python scripts/check_env_contract.py --mode render --env-file .env
```

Run it for local development or S3 smoke setup as needed:

```bash
python scripts/check_env_contract.py --mode local --env-file .env
python scripts/check_env_contract.py --mode s3 --env-file .env
```

This script is advisory only and is not part of normal app startup.

## Render Smoke Test

After both Render services are running, run the production-like smoke test from your local machine:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_s3.py
```

On Windows PowerShell:

```powershell
$env:API_BASE_URL="https://<render-api-url>"; python scripts/smoke_test_s3.py
```

Expected success criteria:

- `/health` returns `{"status":"ok"}`.
- CV upload returns `cv_file_id`.
- Score job reaches `succeeded`.
- Result JSON includes `scores.fit_score`.
- Report metadata does not expose `local_path`.
- DOCX report download returns non-empty bytes.
- The private bucket contains upload/report objects under `S3_PREFIX`.

## Current Limitations

- Current app still has no full auth.
- Job status polling remains UUID-based; result, report metadata, and report download use MVP access-token protection.
- S3 lifecycle cleanup is still needed.
- API and worker startup require the database schema to be at Alembic head.
- First scoring run may be slower if the embedding model has to download at runtime.

## Troubleshooting

- Health check fails: confirm the Web Service start command uses `$PORT`, inspect Render API logs, and verify `DATABASE_URL` is reachable.
- Jobs stay queued: confirm the worker is running, uses the `cvfit` queue, and shares the same `REDIS_URL` as the API.
- Jobs fail during storage reads/writes: compare API and worker `STORAGE_BACKEND`, `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, `S3_PREFIX`, and S3 credentials.
- S3 credentials fail: confirm `AWS_USE_IAM_ROLE=false` when using access keys, and verify the keys have object read/write permissions for the selected prefix.
- S3 endpoint errors: set `S3_ENDPOINT_URL` only when the provider requires it, and use the provider's required region value.
- Database errors mention vector support: confirm the database supports the `vector` extension or choose a compatible Postgres provider/plan.
- Database errors mention missing schema or Alembic head: run the documented migration/adoption workflow after backup and schema checks; do not rely on app startup to create tables.
- Smoke test cannot reach the API: confirm `API_BASE_URL` has the public Render Web Service URL and no trailing path.
- Unexpected auth assumptions: this MVP does not include full auth yet; do not expose it as a production application.
