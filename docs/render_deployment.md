# Render Deployment Guide

This guide prepares the app for an MVP/demo deployment on Render. It does not deploy anything and does not include secrets.

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
CV_MAX_UPLOAD_MB=5
```

Notes:

- `STORAGE_BACKEND=local` is only for local development.
- `S3_BUCKET` and `S3_REGION` are required when `STORAGE_BACKEND=s3`.
- `S3_ENDPOINT_URL` is optional for AWS S3 and required by some S3-compatible providers such as MinIO, Cloudflare R2, or Wasabi. Set it only when the provider requires a custom endpoint.
- On Render, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as secret environment variables unless using an object-storage provider with another supported credential mechanism.
- Set the same storage, database, Redis, and upload-limit environment variables on both the Render API service and the Render worker service.
- For future AWS deployments, prefer IAM roles and set `AWS_USE_IAM_ROLE=true`.
- Keep `STORAGE_ROOT` defined even when using S3; it remains useful for temporary/local development paths.

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

## Pre-Deploy Checklist

Before creating Render services:

1. Confirm `cd backend && pip install -r requirements-dev.txt && python -m pytest` passes locally.
2. Confirm `docker compose config` renders successfully.
3. Run the local Docker smoke test below.
4. Choose the S3-compatible provider and confirm whether it needs `S3_ENDPOINT_URL`.
5. Create a private object-storage bucket and prefix for the MVP.
6. Run the S3-backed smoke test in [s3_smoke_test.md](s3_smoke_test.md).
7. Set the required environment variables on both Render services.
8. Confirm uploaded CVs and reports are not committed to git.

## Local Docker Smoke Test

Start the full local stack:

```bash
docker compose down -v
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

## Health Check

Use:

```text
GET /health
```

Expected response:

```json
{"status":"ok"}
```

## Known Limitations

- No authentication yet.
- CV, result, and report access is UUID-based only.
- Render environment variables must be set for both the API and worker services.
- S3 integration must be smoke-tested with a real private bucket before demo use.
- Render free tier is suitable only for demo/testing, not production.
- The first scoring run may be slower if the embedding model has to download at runtime.
- Database migrations are not yet implemented; the app currently creates tables at startup.

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
