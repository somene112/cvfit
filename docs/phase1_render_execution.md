# Phase 1 Render Execution

## Purpose

This runbook guides the real Render deployment trial for the existing MVP. It keeps Phase 1 focused on deployment readiness, environment verification, and post-deploy smoke testing. It does not add product features, auth, LLM behavior, frontend redesign, or scoring changes.

Do not commit secrets. Do not paste secrets into docs, tickets, screenshots, or smoke-test logs.

## Architecture For Render Phase 1

- Render Web Service runs the FastAPI API and current Jinja/vanilla JavaScript frontend.
- Render Background Worker runs the Celery worker on the `cvfit` queue.
- Render Redis or Key Value is the Celery broker and result backend.
- Render PostgreSQL stores CV metadata, JD text, job state, results, and report metadata.
- Private S3-compatible object storage stores uploaded CV files and generated DOCX reports.

API and worker must share the same `DATABASE_URL`, `REDIS_URL`, `STORAGE_BACKEND`, `CV_MAX_UPLOAD_MB`, and S3 environment variables.

## Services To Create

| Service | Render type | Purpose |
| --- | --- | --- |
| `cvfit-api` | Web Service | FastAPI API and current frontend |
| `cvfit-worker` | Background Worker | Celery processing for parsing, scoring, and reports |
| `cvfit-postgres` | PostgreSQL | Application database with pgvector support |
| `cvfit-redis` | Redis / Key Value | Celery broker and result backend |
| S3 bucket | External S3-compatible storage | Private uploads and DOCX reports |

Service names are placeholders. Use your Render naming convention, but keep API and worker env vars aligned.

## Render Web Service

- Service type: Web Service.
- Branch: `phase1/render-deploy-s3`.
- Root directory: repository root.
- Runtime expectation: Render runs commands from the repository root, then commands enter `backend`.
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

- Expected health response:

```json
{"status":"ok"}
```

## Render Background Worker

- Service type: Background Worker.
- Branch: `phase1/render-deploy-s3`.
- Root directory: repository root.
- Runtime expectation: Render runs commands from the repository root, then commands enter `backend`.
- Build command:

```bash
cd backend && pip install -r requirements.txt
```

- Start command:

```bash
cd backend && celery -A app.workers.celery_app:celery_app worker --loglevel=INFO -Q cvfit
```

The worker does not expose HTTP and does not need `PORT`.

## Shared Env Var Table

Set these on both the API service and worker service.

| Variable | Example / placeholder | Required | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | `<render-postgres-internal-url>` | Yes | Use the same value on API and worker. |
| `REDIS_URL` | `<render-redis-internal-url>` | Yes | Use the same value on API and worker. |
| `STORAGE_BACKEND` | `s3` | Yes | Render trial should use S3-compatible storage. |
| `STORAGE_ROOT` | `./data` | Yes | Kept for config compatibility and local paths. |
| `CV_MAX_UPLOAD_MB` | `10` | Yes | Keep aligned across API and worker. |

## API-Only Env Vars

No required API-only app env vars are currently needed. Render provides `PORT` automatically for the Web Service start command.

## Worker-Only Env Vars

No required worker-only app env vars are currently needed. The worker must share the API's database, Redis, storage, and S3 configuration.

## S3 Env Var Table

Set these on both the API service and worker service.

| Variable | Example / placeholder | Required | Notes |
| --- | --- | --- | --- |
| `S3_BUCKET` | `<private-bucket-name>` | Yes | Bucket must be private. |
| `S3_REGION` | `us-east-1` or `auto` | Yes | Use the value required by the provider. |
| `S3_ENDPOINT_URL` | `<provider-endpoint-if-required>` | Provider-specific | Leave empty for normal AWS S3 unless needed. Usually required for Cloudflare R2, MinIO, Wasabi, or Backblaze B2. |
| `S3_PREFIX` | `cvfit/render-smoke/<date>` | Recommended | Use a dedicated prefix for the deployment trial. |
| `AWS_ACCESS_KEY_ID` | `<secret>` | Yes when `AWS_USE_IAM_ROLE=false` | Store as a Render secret env var. |
| `AWS_SECRET_ACCESS_KEY` | `<secret>` | Yes when `AWS_USE_IAM_ROLE=false` | Store as a Render secret env var. |
| `AWS_USE_IAM_ROLE` | `false` | Yes | Keep `false` for access-key based S3-compatible providers. |

## Render PostgreSQL

- Create a Render PostgreSQL database or compatible Postgres service that supports the `vector` extension.
- Copy the internal database URL into `DATABASE_URL`.
- Set the same `DATABASE_URL` on the API and worker.
- API and worker startup verify that the database schema is at Alembic head; they do not create tables or patch columns.
- For an empty database, run the reviewed Alembic migration. For an existing database, take a backup and use the schema/adoption workflow before upgrading or stamping.

## Render Redis / Key Value

- Create a Render Redis or Key Value instance.
- Copy the internal Redis URL into `REDIS_URL`.
- Set the same `REDIS_URL` on the API and worker.
- If jobs remain queued, compare the API and worker `REDIS_URL` values first.

## S3 / S3-Compatible Storage

- Use a private bucket.
- Use a dedicated deployment-trial prefix, for example `cvfit/render-smoke/2026-05-21`.
- Set `S3_ENDPOINT_URL` only when the provider requires a custom endpoint.
- Confirm credentials can put and get objects under the selected prefix.
- Add a provider lifecycle rule later; S3 lifecycle cleanup is still needed.

## Optional Env Contract Checks

The local checker does not print secret values:

```bash
python scripts/check_env_contract.py --mode local --env-file .env.example
```

For a real Render/S3 env file kept outside git, use:

```bash
python scripts/check_env_contract.py --mode render --env-file <local-render-env-file>
```

Do not commit the real env file.

## Post-Deploy Smoke Test

After the API and worker are deployed and healthy, start with the read-only MVP
smoke check from your local machine:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_mvp.py
```

PowerShell equivalent:

```powershell
$env:API_BASE_URL="https://<render-api-url>"; python scripts/smoke_test_mvp.py
```

Run the full synthetic upload-to-report flow only with explicit opt-in:

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

Expected success signs:

- Read-only mode returns `health ok`.
- Mutating mode uploads only a tiny synthetic DOCX CV.
- Mutating mode creates one score job and reaches `succeeded`.
- Mutating mode result JSON includes `scores.fit_score`.
- Mutating mode report metadata does not expose `local_path`.
- Mutating mode DOCX report download returns non-empty bytes.

Do not set `DATABASE_URL` for smoke tests. Do not use real CVs or private
personal data. Mutating smoke leaves one synthetic job/report because the API
does not currently expose a cleanup endpoint.

## Render MVP Smoke Test Passed

Date: May 22, 2026

API URL domain: `cvfit.onrender.com`

Smoke command:

```bash
API_BASE_URL=https://cvfit.onrender.com python scripts/smoke_test_s3.py
```

Success summary:

- `/health` returned ok.
- CV upload succeeded.
- Score job was created.
- Job moved from queued to running to succeeded.
- Result JSON was returned with `fit_score`.
- Report metadata returned `download_url` and did not expose `local_path`.
- DOCX report downloaded successfully.
- Smoke script ended with `smoke test passed` and `s3 smoke test passed`.

Remaining risks at Phase 1A closeout:

- No full auth yet.
- UUID-only access existed before the Phase 1B access-token patch.
- Alembic baseline exists; existing production-like databases need backup and schema/adoption checks before migration changes.
- S3 lifecycle cleanup still needed.
- Docker image still large.
- First model load can be slow.

## Phase 1B Render Token Smoke Test Passed

Date: May 22, 2026

API URL domain: `cvfit.onrender.com`

Smoke command:

```bash
API_BASE_URL=https://cvfit.onrender.com python scripts/smoke_test_s3.py
```

Success summary:

- `/health` returned ok.
- CV upload succeeded.
- Score job was created.
- The smoke script captured `access_token` internally and did not print the raw token.
- Missing/wrong token checks returned 403.
- Job reached `succeeded`.
- Result JSON worked with the correct token and returned `fit_score`.
- Report metadata worked with the correct token, returned `download_url`, and did not expose `local_path`.
- Token-bearing report URL output was redacted.
- DOCX report download worked with the correct token.
- Smoke script ended with `smoke test passed` and `s3 smoke test passed`.

Phase 1B adds MVP access-token protection for result, report metadata, and report download endpoints. Full auth, user accounts, and per-user history remain future work.

## Troubleshooting

### API Build Failure

- Confirm the build command is exactly `cd backend && pip install -r requirements.txt`.
- Confirm Render is using Python 3.11 or a compatible Python version.
- Inspect whether the failure occurs in `requirements-ml.txt`; the runtime dependency path intentionally uses CPU-only Torch.
- If the build times out while downloading dependencies, retry once and capture the failing package line.

### Worker Cannot Connect To Redis

- Confirm `REDIS_URL` is set on the worker.
- Confirm API and worker use the same internal Render Redis URL.
- Confirm the worker start command includes `-Q cvfit`.
- Restart the worker after env var changes.

### API Cannot Connect To Postgres

- Confirm `DATABASE_URL` is set on the API.
- Confirm API and worker use the same internal Render Postgres URL.
- Confirm the database is available before restarting the API.
- Confirm the selected Postgres service supports the `vector` extension.
- If logs mention missing schema or Alembic head, run the documented migration/adoption workflow instead of relying on app startup side effects.

### S3 AccessDenied

- Confirm bucket name, region, endpoint, prefix, and credentials match on API and worker.
- Confirm `AWS_USE_IAM_ROLE=false` when using access keys.
- Confirm the key can `PutObject` and `GetObject` under `S3_PREFIX`.
- Confirm the bucket is private but not blocking the selected credential.

### Worker Job Stuck In Queued/Running

- Confirm the worker service is running and has recent logs.
- Confirm API and worker share `REDIS_URL`.
- Confirm API and worker share `DATABASE_URL`.
- Confirm API and worker share `STORAGE_BACKEND=s3` and the same S3 env vars.
- Check worker logs for model download, parser, database, or S3 errors.

### Model Download Is Slow

- The first scoring run may download the embedding model at runtime.
- Wait for the first worker run before judging steady-state latency.
- If Render memory or disk limits are hit, capture worker logs and consider a paid plan or prebuilt image strategy later.

### Report Download Returns 404

- Confirm the job reached `succeeded`.
- Confirm the worker wrote report metadata to the database.
- Confirm API and worker share `DATABASE_URL`.
- Confirm API and worker share the same S3 bucket and prefix.
- Inspect API logs for missing S3 object or storage-key errors.

## Rollback Notes

- Do not delete the working local branch after a failed deployment trial.
- If a Render deploy fails, roll the affected Render service back to the previous deploy in the Render dashboard.
- If smoke-test objects were created in S3, remove only objects under the dedicated smoke-test prefix.
- If a bad env var was entered, update the value in both API and worker, then restart both services.
- Keep the failed logs for diagnosis, but redact secrets before sharing.

## Current Limitations

- No full auth yet.
- MVP access-token protection is not full account auth.
- Job status polling remains public by UUID for the current UI flow.
- API and worker startup require the database schema to be initialized and tracked by Alembic.
- S3 lifecycle cleanup still needed.
- Docker image remains large.
- The deployment is for MVP/demo validation, not production exposure.
