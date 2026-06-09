# Deployment Design

## Current Architecture

The app is a FastAPI service with a small Jinja/vanilla JavaScript frontend. It accepts a CV upload, stores the file, accepts pasted job description text, creates an analysis job in PostgreSQL, and queues the work through Celery with Redis. A worker parses the CV, parses the JD, scores the match with deterministic heuristics plus local SentenceTransformers embeddings, writes JSON results to PostgreSQL, and generates a DOCX report.

Current persistence is split across PostgreSQL and file storage:

- PostgreSQL stores CV metadata, JD text, analysis job state, result JSON, and report storage locations.
- Local development stores uploaded CVs under `STORAGE_ROOT/uploads`.
- Local development stores generated DOCX reports under `STORAGE_ROOT/reports`.

## MVP Deployment: Render + Object Storage

Recommended MVP/demo architecture:

- Render Web Service: runs FastAPI and serves the current UI.
- Render Background Worker: runs the Celery worker.
- Render Redis/Key Value: Celery broker and result backend.
- Render Postgres with pgvector: application database and vector extension support.
- S3-compatible object storage: uploaded CVs and generated DOCX reports.

S3-compatible storage should be accessed through the storage service/SDK abstraction. It should not be mounted as a filesystem. The API and worker should treat stored CVs/reports as object locations, not host-local paths.

## Future AWS Production Architecture

Future production architecture:

- API: AWS App Runner or ECS service running FastAPI.
- Worker: ECS/Fargate service running the Celery worker.
- Database: RDS PostgreSQL with pgvector enabled.
- Object storage: S3 bucket for CV uploads and DOCX reports.
- Redis: ElastiCache Redis for Celery broker/result backend.
- Observability: CloudWatch logs, metrics, alarms, and dashboarding.
- CI/CD: GitHub Actions to run tests, build images, and deploy to AWS.

For AWS, prefer IAM roles for runtime credentials instead of long-lived access keys. Use separate S3 prefixes or buckets for development, staging, and production.

## Render vs AWS Tradeoffs

| Area | Render MVP | AWS Production |
| --- | --- | --- |
| Setup speed | Faster, fewer moving parts | Slower, more infrastructure choices |
| Operational burden | Low | Medium to high |
| Cost predictability | Good for demos/MVP | Better control at scale, more services to manage |
| Scaling | Simple vertical/horizontal options | More granular API/worker/database scaling |
| Security controls | Adequate for MVP | Stronger IAM, networking, audit, and compliance options |
| Observability | Basic platform logs/metrics | CloudWatch and broader AWS tooling |
| Portability | Good if app stays twelve-factor | Good, but infrastructure becomes AWS-specific |

## Recommendation

Use Render plus S3-compatible object storage for the MVP/demo. It is the fastest path to a deployable app while keeping the app architecture close to production shape.

Move to AWS later when the product needs stronger security boundaries, more predictable production operations, private networking, IAM-based access, and mature monitoring.

## Environment Variables

Common:

```env
DATABASE_URL=postgresql+psycopg2://...
REDIS_URL=redis://...
STORAGE_BACKEND=local|s3
STORAGE_ROOT=./data
CV_MAX_UPLOAD_MB=10
FRONTEND_TEMPLATES_DIR=../frontend/templates
FRONTEND_STATIC_DIR=../frontend/static
```

Local storage:

```env
STORAGE_BACKEND=local
STORAGE_ROOT=./data
```

S3-compatible storage:

```env
STORAGE_BACKEND=s3
S3_BUCKET=
S3_REGION=
S3_ENDPOINT_URL=
S3_PREFIX=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_USE_IAM_ROLE=false
```

Render should provide `DATABASE_URL` and `REDIS_URL` from managed services. Object storage credentials should be configured as secret environment variables.

Future AWS should use RDS for `DATABASE_URL`, ElastiCache for `REDIS_URL`, `STORAGE_BACKEND=s3`, an S3 bucket/prefix, and IAM roles where possible.

## Data Retention and Privacy Notes

CVs contain personal data. Treat uploaded files and generated reports as private user data:

- Do not expose raw storage paths or bucket keys in public API responses.
- Use private buckets and short-lived presigned URLs only when needed.
- Define retention rules for uploaded CVs and generated reports.
- Avoid committing uploads, reports, model caches, local databases, or generated files.
- Log job IDs and statuses, not CV contents or full JD/CV text.
- Add authentication and ownership checks before production use.
