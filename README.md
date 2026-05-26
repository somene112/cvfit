# AI CV Fit App

FastAPI-based CV-to-job-description fit scoring MVP. The app uploads a CV, accepts pasted JD text, runs an async Celery job, stores results in PostgreSQL, and returns JSON plus a downloadable DOCX report.

## Folder Structure

```text
backend/
  app/                  FastAPI app, API routes, DB, services, workers
  tests/                pytest tests
  requirements.txt      backend Python dependencies
  requirements-ml.txt   ML runtime dependencies with CPU-only Torch
  requirements-dev.txt  local test/development dependencies
frontend/
  templates/            Jinja templates
  static/               vanilla JS/static assets
scripts/                smoke tests and operational scripts
docs/                   deployment and baseline docs
docker/                 API and worker Dockerfiles
docker-compose.yml      local API/worker/Postgres/Redis stack
```

## Architecture

FastAPI + Celery + Redis + PostgreSQL.

## Local Docker Run

For a fresh local Docker database, start Postgres and Redis first, run Alembic,
then start the API and worker:

```powershell
docker compose up --build -d postgres redis
cd backend
$env:DATABASE_URL="postgresql+psycopg2://cvfit:cvfit@localhost:5432/cvfit"
alembic upgrade head
cd ..
docker compose up --build -d
```

Open:

```text
http://localhost:8000
```

Stop:
```bash
docker compose down
```

## Local Backend-Only Run

Start PostgreSQL and Redis separately, make sure `DATABASE_URL` points to that
local database, then:

```bash
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

In another shell:

```bash
cd backend
celery -A app.workers.celery_app:celery_app worker --loglevel=INFO -Q cvfit
```

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

There is intentionally no root requirements.txt; install from backend/requirements.txt for runtime or backend/requirements-dev.txt for local development and tests.

## CI Checks

GitHub Actions runs backend hygiene checks plus disposable PostgreSQL migration
validation on pull requests and pushes to `main`. The backend job uses only
safe local/test environment values:

```env
DATABASE_URL=sqlite+pysqlite:///:memory:
REDIS_URL=redis://localhost:6379/0
```

CI does not use Render `DATABASE_URL`, S3 credentials, API tokens, or any
production secret. Database migrations and existing production-like database
adoption remain operator-controlled; CI never upgrades or stamps Render
PostgreSQL.

The backend job checks:

```bash
python scripts/ci_guard.py
python -m compileall backend/app
cd backend && python -m pytest --basetemp pytest-cache-files-local -p no:cacheprovider
cd backend && alembic heads
cd backend && alembic history
docker compose config
```

The PostgreSQL migration job starts a disposable `pgvector/pgvector:pg16`
service with local CI-only credentials, runs `alembic upgrade head`, verifies
the current revision is `20260522_0001`, and runs `python scripts/check_db_schema.py`
against that disposable database. It does not use Render secrets, call Render
APIs, deploy, or run adoption/stamp helpers.

On Windows Anaconda Prompt, run the same local checks with:

```bat
set "DATABASE_URL=sqlite+pysqlite:///:memory:"
set "REDIS_URL=redis://localhost:6379/0"
set "PYTHONPYCACHEPREFIX=backend/pytest-cache-files-local/pycache-prefix"
python scripts/ci_guard.py
python -m compileall backend/app
cd backend
python -m pytest --basetemp pytest-cache-files-local -p no:cacheprovider
alembic heads
alembic history
cd ..
docker compose config
set "PYTHONPYCACHEPREFIX="
```

After a deploy, verify the public API without touching the database directly:

```bat
set "API_BASE_URL=https://your-render-api.onrender.com"
curl "%API_BASE_URL%/health"
```

## Database Migrations

Migration workflow and Render adoption notes are in [Database migrations](docs/database_migrations.md). For a disposable/local PostgreSQL validation run:

```bash
cd backend
DATABASE_URL=postgresql+psycopg2://cvfit:cvfit@localhost:5432/cvfit alembic upgrade head
cd ..
python scripts/check_db_schema.py
```

API and worker startup do not silently create or patch database tables. If the
schema is missing or behind Alembic head, startup fails with an error that tells
you to run `alembic upgrade head` against the intended local/disposable
database. Do not run migrations blindly against an existing production database
without a backup and schema/adoption checks.

## Smoke Test

With the Docker stack running:

```bash
python scripts/smoke_test_local.py
```

The smoke test uploads a temporary DOCX CV, creates a score job, waits for worker completion, validates result JSON, checks report metadata, and downloads a non-empty DOCX report.

## Phase 0 Status

Phase 0 is closed as the current baseline. Verified items include the backend/frontend split, FastAPI API, Celery worker, Redis, PostgreSQL/pgvector, local/S3 storage abstraction, local Docker E2E smoke test, S3-backed Docker smoke test, result JSON, DOCX report download, safe report metadata, CPU-only Torch dependency path, and repository hygiene for generated files.

Current status: Phase 1A Render MVP smoke test has passed. Phase 1B access-token MVP passed local and Render smoke tests.

Key docs:

- [Phase 0 baseline](docs/phase0_baseline.md)
- [Roadmap](docs/roadmap.md)
- [Phase 1 team plan](docs/phase1_team_plan.md)
- [Render deployment guide](docs/render_deployment.md)
- [Render manual setup checklist](docs/render_manual_setup_checklist.md)
- [Phase 1 Render execution runbook](docs/phase1_render_execution.md)
- [Database migrations](docs/database_migrations.md)
- [S3 smoke test guide](docs/s3_smoke_test.md)






