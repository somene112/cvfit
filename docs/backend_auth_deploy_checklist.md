# Backend Auth Deploy Checklist

Owner: Phuc

Use this checklist before exposing the Phase 2 auth-enabled backend to a
separate Next frontend. Do not run production migrations or smoke tests until
the team explicitly schedules that deployment step.

## Required Env Vars

Render backend must set:

```env
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ALLOWED_ORIGINS=https://<next-frontend-domain>
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOWED_METHODS=GET,POST,OPTIONS
CORS_ALLOWED_HEADERS=Authorization,Content-Type
```

Local Next frontend defaults:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Do not use the insecure local fallback `JWT_SECRET_KEY` in production. Do not
set `CORS_ALLOW_CREDENTIALS=true` with `CORS_ALLOWED_ORIGINS=*`.

## Migration Safety

- Full migration workflow: [Database migrations](database_migrations.md).
- Do not run the auth migration on Render DB until a backup and schema check are
  complete.
- Validate Alembic on a disposable/local Postgres database first.
- Confirm `alembic heads` shows the expected single head before deployment.
- Current expected head is `20260531_0001`.
- Confirm `python scripts/check_db_schema.py` passes against the intended
  database after migration.
- If Render is currently at old head `20260522_0001`, apply the auth migration
  only after backup and disposable/local validation.
- Downgrading from `20260531_0001` removes `users` and
  `analysis_jobs.user_id`; do not downgrade production without explicit
  data-loss approval.

## Smoke Checklist

Run these with synthetic data only:

- `GET /health`
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me` with `Authorization: Bearer <jwt>`
- `POST /v1/auth/logout` with `Authorization: Bearer <jwt>`
- `POST /v1/cv/upload`
- guest `POST /v1/jobs/create-score` without Authorization
- logged-in `POST /v1/jobs/create-score` with owner JWT
- `GET /v1/jobs/history` with owner JWT
- result/report access by guest `access_token`
- result/report access by owner JWT

The auth smoke helper is opt-in because it creates one synthetic account:

```powershell
$env:API_BASE_URL="https://<backend-domain>"
$env:AUTH_SMOKE_ALLOW_MUTATING="1"
python scripts/smoke_test_auth_api.py
```

The smoke helper redacts JWTs in output. Do not paste raw JWTs, passwords, or job
`access_token` values into logs or chats.

## Report Download Handoff

For Quân:

- Login/register/history calls should use `NEXT_PUBLIC_API_BASE_URL`.
- Logged-in API calls should send `Authorization: Bearer <jwt>`.
- A normal browser anchor cannot attach Authorization headers.
- For report download, either use the guest `download_url` that includes the job
  `access_token`, or use `fetch()` with the owner JWT and download the returned
  blob client-side.
- Do not `console.log` JWTs, passwords, full URLs containing `access_token`, or
  local file paths.

## Current Non-Goals

- No frontend UI changes in this backend step.
- No S3 lifecycle cleanup changes.
- No production deployment in this checklist.
- No Render DB migration without an explicit deployment window.
