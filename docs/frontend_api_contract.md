# Frontend API Contract

Owner backend auth/API contract: Phuc
Owner Next/React frontend: Quan

This document is the Phase 2 Full Auth/Login MVP contract draft. It records the
backend state that exists now and the planned JWT Bearer auth contract. It does
not mean the auth endpoints are implemented yet.

## Auth Status Audit

Original audit classification before the DB foundation:
Frontend-only login placeholder exists

Current foundation status after revision `20260531_0001`:
Partial backend auth foundation exists. This means the user table and nullable
job ownership column exist in the model/migration contract, but login/register
behavior is still not implemented.

Current repository state:

- No implemented backend auth endpoints.
- `users` model/table foundation exists after applying Alembic revision
  `20260531_0001`.
- No password hashing utility or dependency.
- No JWT/session utility or dependency.
- No `Authorization: Bearer` parsing in backend routes.
- No history endpoint.
- `frontend/templates/login.html` is a static login form placeholder, but it is
  not wired to a backend auth route and is not included by `backend/app/main.py`.
- Guest mode is implemented with per-job `access_token` protection for result,
  report metadata, and report download.

## Base URL Guidance

Local backend:

```text
http://localhost:8000
```

Current deployed backend example:

```text
https://cvfit.onrender.com
```

The existing Jinja fallback UI is served by FastAPI and uses same-origin
relative API paths. A separate Next frontend should use an explicit public API
base URL.

Backend scripts and smoke tests:

```env
API_BASE_URL=https://cvfit.onrender.com
```

Next frontend:

```env
NEXT_PUBLIC_API_BASE_URL=https://cvfit.onrender.com
```

Contract gap: backend CORS is not currently configured in `backend/app/main.py`.
Before a separate Next/Vercel frontend calls the API, add explicit allowed
origins for local Next and the deployed frontend domain.

## Current Implemented Endpoints

### Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Jinja Fallback UI

```http
GET /
```

Serves `frontend/templates/index.html`. Do not remove this fallback while adding
auth.

### Upload CV

```http
POST /v1/cv/upload
Content-Type: multipart/form-data
```

Form fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | PDF or DOCX | Yes | Extension must be `.pdf` or `.docx`; max size follows `CV_MAX_UPLOAD_MB`. |

Current response example:

```json
{
  "cv_file_id": "4a95a6fc-97cc-4c2f-8f5d-5f07409e4068",
  "cv_id": "4a95a6fc-97cc-4c2f-8f5d-5f07409e4068",
  "filename": "candidate_cv.pdf",
  "content_type": "application/pdf",
  "size_bytes": 123456
}
```

Current errors:

- `400` when filename is missing.
- `400` for unsupported extensions.
- `400` for empty or oversized uploads from storage validation.

### Create Score Job

```http
POST /v1/jobs/create-score
Content-Type: application/json
```

Current request shape accepted by backend:

```json
{
  "cv_file_id": "4a95a6fc-97cc-4c2f-8f5d-5f07409e4068",
  "jd_text": "Backend Engineer role requiring Python, FastAPI, PostgreSQL, Redis, Docker, and SQL.",
  "options": {
    "target_role": "Backend Engineer",
    "language": "en",
    "strictness": "balanced",
    "output_formats": ["json", "docx"]
  }
}
```

Compatibility request shape also accepted:

```json
{
  "cv_id": "4a95a6fc-97cc-4c2f-8f5d-5f07409e4068",
  "job_description": "Backend Engineer role requiring Python, FastAPI, PostgreSQL, Redis, Docker, and SQL."
}
```

Current response:

```json
{
  "job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "access_token": "guest-job-secret",
  "status": "queued"
}
```

Current behavior:

- Creates a `jd_docs` row.
- Creates an `analysis_jobs` row with status `queued`, progress `0`, and
  `access_token_hash`.
- Returns the plaintext `access_token` only once in the create response.
- Queues `app.workers.tasks.run_job`.
- Does not attach a `user_id` yet because auth routes/current-user dependency
  are not implemented in this foundation step.

### Poll Job Status

```http
GET /v1/jobs/{job_id}
```

Current response:

```json
{
  "job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "status": "queued",
  "progress": 0,
  "error_message": null,
  "error": null
}
```

Current behavior:

- Does not require `access_token`.
- Returns `404` if the job is not found.
- Returns `400` if `job_id` is not a UUID.

### Get Result

```http
GET /v1/jobs/{job_id}/result?access_token=<guest-job-secret>
```

Current response shape:

```json
{
  "job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "result": {
    "scores": {
      "fit_score": 88,
      "skill_match": 90
    },
    "skill_gap": {
      "missing_must_have": [],
      "missing_nice_to_have": ["Kubernetes"]
    },
    "evidence": []
  },
  "overall_fit_score": 88,
  "summary": "Analysis complete.",
  "strengths": [],
  "missing_skills": ["Kubernetes"],
  "recommendations": [],
  "evidence": []
}
```

Current behavior:

- Requires a valid query-string `access_token`.
- Returns `403` for missing or wrong token.
- Returns `409` when the job is not succeeded or result JSON is not ready.
- Scrubs internal fields such as token hashes, storage paths, local paths, S3
  keys, raw CV text, and report paths from the result payload.

### Get Report Metadata

```http
GET /v1/jobs/{job_id}/report?access_token=<guest-job-secret>
```

Current response:

```json
{
  "job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "report_status": "ready",
  "sections": [],
  "format": "docx",
  "download_url": "/v1/jobs/7f7ee6ba-15f3-4771-9a10-5124c77a5c2b/report/download?access_token=guest-job-secret"
}
```

Current behavior:

- Requires a valid query-string `access_token`.
- Returns `403` for missing or wrong token.
- Returns `409` when the report is not ready.
- Does not expose local report path.

### Download Report

```http
GET /v1/jobs/{job_id}/report/download?access_token=<guest-job-secret>
```

Current response:

```http
200 OK
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="cvfit_report_{job_id}.docx"
```

Current behavior:

- Requires a valid query-string `access_token`.
- Returns `403` for missing or wrong token.
- Returns `409` when the report is not ready.
- Returns `404` when the stored report object cannot be found.

## Current Guest Access Token Flow

Guest mode must remain backward compatible:

```text
Upload CV
-> Create score job
-> Backend returns job_id + access_token
-> Frontend polls GET /v1/jobs/{job_id}
-> Frontend calls result/report/download with ?access_token=<token>
```

The database stores only `analysis_jobs.access_token_hash`, not the plaintext
token. The plaintext token is currently carried in result/report/download URLs,
so frontend and logs must redact those URLs.

## Planned Full Auth MVP Contract

Auth strategy: JWT Bearer Token.

DB foundation added in revision `20260531_0001`:

- `users.id`, `users.email`, `users.password_hash`, `users.full_name`,
  `users.is_active`, `users.created_at`, and `users.updated_at`.
- Unique email index: `ix_users_email`.
- Nullable job owner field: `analysis_jobs.user_id`.
- Job owner index: `ix_analysis_jobs_user_id`.
- Foreign key: `analysis_jobs.user_id -> users.id`.

The nullable `analysis_jobs.user_id` is intentional so guest jobs continue to
work.

Request format:

```http
Authorization: Bearer <jwt>
```

Initial MVP can use a single access token response without refresh tokens.
Logout can be stateless from the backend perspective unless token revocation is
added later.

### Register

```http
POST /v1/auth/register
Content-Type: application/json
```

Request:

```json
{
  "email": "student@example.com",
  "password": "correct-horse-battery-staple",
  "full_name": "Example Student"
}
```

Planned response:

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "user": {
    "id": "2c81c4b6-b716-43c6-b9d3-3d7d00c6fd15",
    "email": "student@example.com",
    "full_name": "Example Student"
  }
}
```

Planned errors:

- `400` or `409` if email already exists.
- `422` for invalid email/password request shape.

### Login

```http
POST /v1/auth/login
Content-Type: application/json
```

Request:

```json
{
  "email": "student@example.com",
  "password": "correct-horse-battery-staple"
}
```

Planned response:

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "user": {
    "id": "2c81c4b6-b716-43c6-b9d3-3d7d00c6fd15",
    "email": "student@example.com",
    "full_name": "Example Student"
  }
}
```

Planned errors:

- `401` for invalid credentials.
- Response must not reveal whether email or password was wrong.

### Me

```http
GET /v1/auth/me
Authorization: Bearer <jwt>
```

Planned response:

```json
{
  "id": "2c81c4b6-b716-43c6-b9d3-3d7d00c6fd15",
  "email": "student@example.com",
  "full_name": "Example Student"
}
```

Planned errors:

- `401` for missing, invalid, or expired JWT.

### Logout

```http
POST /v1/auth/logout
Authorization: Bearer <jwt>
```

Planned response:

```json
{
  "ok": true
}
```

MVP note: if JWTs are stateless, frontend deletes the stored token and backend
returns success for a valid token. Token revocation can be a later hardening
item.

## Planned Job Ownership Behavior

### Create Score Job With Optional JWT

```http
POST /v1/jobs/create-score
Authorization: Bearer <jwt>
Content-Type: application/json
```

Planned behavior:

- If `Authorization: Bearer <jwt>` is present and valid, set
  `analysis_jobs.user_id = current_user.id`.
- If Authorization is missing, keep the current guest behavior.
- Guest jobs still return `job_id` and `access_token`.
- Logged-in jobs may still return `access_token` for backward compatibility, but
  owner JWT must also authorize result/report/download.
- Invalid Authorization should fail with `401`; it should not silently fall back
  to guest mode.

### Result And Report Authorization

These endpoints must allow either valid guest access token or owner JWT:

```http
GET /v1/jobs/{job_id}/result?access_token=<guest-job-secret>
GET /v1/jobs/{job_id}/report?access_token=<guest-job-secret>
GET /v1/jobs/{job_id}/report/download?access_token=<guest-job-secret>
```

or:

```http
GET /v1/jobs/{job_id}/result
Authorization: Bearer <jwt>
```

```http
GET /v1/jobs/{job_id}/report
Authorization: Bearer <jwt>
```

```http
GET /v1/jobs/{job_id}/report/download
Authorization: Bearer <jwt>
```

Planned behavior:

- `access_token` path continues to work for guest compatibility.
- Owner JWT path works only when `analysis_jobs.user_id` matches current user.
- Non-owner JWT returns `403`.
- Missing both guest token and JWT returns `401` or `403`.

### History

```http
GET /v1/jobs/history
Authorization: Bearer <jwt>
```

Planned response:

```json
{
  "items": [
    {
      "job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
      "status": "succeeded",
      "progress": 100,
      "created_at": "2026-05-31T12:00:00Z",
      "updated_at": "2026-05-31T12:01:30Z",
      "target_role": "Backend Engineer",
      "overall_fit_score": 88,
      "has_report": true
    }
  ]
}
```

Planned behavior:

- Requires valid JWT.
- Returns only jobs where `analysis_jobs.user_id = current_user.id`.
- Does not return guest `access_token`, `access_token_hash`, storage paths, raw
  CV text, local file paths, or S3 object keys.

## Token Safety Rules

- Do not log JWTs.
- Do not log passwords.
- Do not log job `access_token` values.
- Do not log full URLs that include `access_token`.
- Do not expose local file paths, storage paths, buckets, or S3 object keys in
  API responses.
- Do not expose raw CV text in public API responses.
- `localStorage` is acceptable only as MVP frontend token storage if the
  frontend owner documents that decision and accepts the tradeoff. Prefer memory
  state or `sessionStorage` for the guest job token.
- Never commit real `.env` files or secrets.

## Backend Implementation Plan

1. Add auth settings and dependencies: JWT secret, algorithm, expiry, password
   hashing library, and JWT library.
2. Add `User` model and Alembic migration; add nullable
   `analysis_jobs.user_id` with an index and foreign key.
3. Add auth schemas and security utilities for password hashing, JWT creation,
   JWT decoding, and current-user dependency.
4. Add `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/me`, and
   `/v1/auth/logout` routes.
5. Update `POST /v1/jobs/create-score` to accept optional auth and attach owned
   jobs to `current_user.id`.
6. Update result/report/download authorization to allow valid guest token or
   owner JWT.
7. Add `GET /v1/jobs/history` for current user's jobs only.
8. Add focused backend tests for auth endpoints, ownership checks, guest
   backward compatibility, and history filtering.
9. Add CORS configuration for the separate Next frontend.
10. Run migrations only against local/disposable databases first; do not run
    migrations against Render DB without an explicit deployment step.

## Files Likely To Change Next

- `backend/requirements.txt`: add password hashing and JWT dependencies.
- `backend/app/core/config.py`: add JWT/CORS settings.
- `backend/app/main.py`: include auth router and CORS middleware.
- `backend/app/db/models.py`: add `User`; add nullable `AnalysisJob.user_id`.
- `backend/app/db/init_db.py`: update `EXPECTED_ALEMBIC_HEAD` after migration.
- `backend/app/schemas/auth.py`: new auth request/response schemas.
- `backend/app/schemas/responses.py`: likely add history response schemas.
- `backend/app/api/routes/auth.py`: new auth endpoints.
- `backend/app/api/routes/jobs.py`: optional auth on create-score, owner-or-token
  authorization, and history endpoint.
- `backend/app/api/routes/utils.py`: possibly shared auth/UUID helpers if needed.
- `backend/app/core/security.py` or `backend/app/services/auth.py`: new password
  hashing and JWT helpers.
- `backend/alembic/versions/<new_revision>_add_users_and_job_ownership.py`: new
  migration.
- `backend/tests/`: focused auth and job ownership tests in the next task.
- `scripts/smoke_test_mvp.py`: optionally add non-secret auth smoke coverage
  after backend auth exists.

## Contract Gaps And TODOs

- Decide exact JWT library and password hashing package.
- Decide user fields beyond `id`, `email`, `password_hash`, `full_name`,
  `created_at`, and `updated_at`.
- Decide email normalization and uniqueness behavior.
- Decide password length/complexity MVP validation.
- Decide JWT expiry duration and whether refresh tokens are out of scope.
- Decide whether logged-in create-score should still return guest
  `access_token`; recommended for backward compatibility in the MVP.
- Decide exact `401` versus `403` convention for missing credentials on
  result/report endpoints.
- Decide pagination parameters for `GET /v1/jobs/history`.
- Add CORS allowed origins before separate Next frontend integration.
- Add Render migration/deployment checklist for the new auth migration.

## Files Inspected For This Audit

- `backend/app/main.py`
- `backend/app/api/routes/health.py`
- `backend/app/api/routes/cv.py`
- `backend/app/api/routes/jobs.py`
- `backend/app/api/routes/ui.py`
- `backend/app/api/routes/utils.py`
- `backend/app/db/models.py`
- `backend/app/db/session.py`
- `backend/app/db/init_db.py`
- `backend/app/core/config.py`
- `backend/app/schemas/requests.py`
- `backend/app/schemas/responses.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260522_0001_initial_schema.py`
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/tests/test_storage.py`
- `backend/tests/test_frontend_static.py`
- `backend/tests/test_smoke_test_mvp.py`
- `scripts/smoke_test_mvp.py`
- `frontend/templates/index.html`
- `frontend/templates/login.html`
- `frontend/static/app.js`
- `README.md`
- `docs/02_api_contract_next_frontend.md`
- `docs/03_access_token_protection_spec.md`
- `docs/06_phase2_product_spec.md`
- `docs/roadmap.md`
