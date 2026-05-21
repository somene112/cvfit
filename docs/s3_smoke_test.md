# S3 Smoke Test

This smoke test proves that the existing app can use S3-compatible object storage for uploaded CV files and generated DOCX reports. It does not deploy the app and does not add new product behavior.

## Purpose

Run the normal app flow with `STORAGE_BACKEND=s3`:

1. Upload a temporary DOCX CV.
2. Confirm the API writes the CV object to S3-compatible storage.
3. Create a scoring job.
4. Confirm the worker reads the CV object from storage.
5. Confirm the worker writes the DOCX report object to storage.
6. Confirm the API downloads the report object and streams non-empty DOCX bytes.

## Required Environment Variables

Set these in the shell or root `.env` before starting Docker Compose:

```env
STORAGE_BACKEND=s3
S3_BUCKET=
S3_REGION=
S3_PREFIX=cvfit/smoke
S3_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_USE_IAM_ROLE=false
```

`S3_ENDPOINT_URL` is optional for AWS S3. It is usually required for S3-compatible providers.

Never commit real credentials. Keep bucket policies private and use a disposable prefix such as `cvfit/smoke/<date>` for test runs.

API and worker must share the same `DATABASE_URL`, `REDIS_URL`, `STORAGE_BACKEND`, and S3 environment variables.

## AWS S3

For AWS S3:

```env
STORAGE_BACKEND=s3
S3_BUCKET=your-private-bucket
S3_REGION=us-east-1
S3_PREFIX=cvfit/smoke
S3_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_USE_IAM_ROLE=false
```

The IAM user or role needs permission for `s3:PutObject`, `s3:GetObject`, and preferably `s3:DeleteObject` for cleanup under the selected prefix.

## S3-Compatible Providers

For providers such as Cloudflare R2, MinIO, Wasabi, or Backblaze B2, set the provider endpoint:

```env
STORAGE_BACKEND=s3
S3_BUCKET=your-private-bucket
S3_REGION=auto
S3_ENDPOINT_URL=https://your-provider-endpoint.example
S3_PREFIX=cvfit/smoke
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_USE_IAM_ROLE=false
```

Use the region value required by the provider. Cloudflare R2 commonly uses `auto`.

## Docker Compose S3 Smoke Test

From the repository root:

```bash
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.s3.yml up --build -d
python scripts/smoke_test_s3.py
docker compose -f docker-compose.yml -f docker-compose.s3.yml down
```

The override keeps Postgres and Redis local, but forces both API and worker to use S3-compatible storage.

## Render S3 Smoke Test

After manually deploying the API and worker on Render with the same S3 settings, run:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_s3.py
```

This validates the deployed API, deployed worker, Render Redis/Postgres, and private S3-compatible bucket together.

## Expected Output

Successful output includes:

```text
s3 smoke target prefix=<bucket>/<prefix>
health ok
uploaded cv_file_id=<uuid>
created job_id=<uuid>
job status=succeeded progress=100
fit_score=<number>
report metadata ok: {'format': 'docx', 'download_url': '/v1/jobs/<job_id>/report/download'}
downloaded report bytes=<non-zero>
smoke test passed
s3 smoke test passed
```

## Failure Notes

If startup fails, inspect:

```bash
docker compose -f docker-compose.yml -f docker-compose.s3.yml logs api --tail=200
docker compose -f docker-compose.yml -f docker-compose.s3.yml logs worker --tail=200
```

Common causes:

- Missing `S3_BUCKET`.
- Missing `S3_REGION`.
- Missing credentials while `AWS_USE_IAM_ROLE=false`.
- Incorrect `S3_ENDPOINT_URL` for the provider.
- Bucket policy denies object reads or writes.
- API and worker have different storage environment variables.
- S3 lifecycle cleanup has not been configured yet; old smoke-test objects may accumulate until cleanup is added.
