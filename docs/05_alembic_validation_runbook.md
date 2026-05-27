# Alembic Validation Runbook — Phase 1

## Mục tiêu

Không chạy migration lên production DB nếu chưa validate trên DB sạch hoặc DB disposable.

## Checklist

1. Pull code mới nhất.
2. Kiểm tra `.env` dùng DB test/disposable, không phải production.
3. Chạy test.
4. Chạy `alembic current`.
5. Chạy `alembic upgrade head`.
6. Kiểm tra bảng/column quan trọng.
7. Chạy app smoke test.
8. Chỉ sau đó mới cân nhắc production migration.

## Commands — PowerShell

```powershell
cd D:\Nguyen_Duc_Hoang_Phuc\SP26\EXE101\project

git status
git pull origin main

cd backend
python -m pytest -q
alembic current
alembic history
alembic upgrade head
alembic current
```

## Disposable DB strategy

Dùng một database test riêng, ví dụ:

```env
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/cvfit_migration_test
```

Không dùng production URL khi thử migration lần đầu.

Migration hiện tại dùng PostgreSQL-specific features (`vector` extension,
PostgreSQL UUID/JSONB/ENUM), nên không dùng SQLite để thay thế validation
`alembic upgrade head`.

## Commands - Windows cmd.exe disposable Docker

```cmd
cd D:\Nguyen_Duc_Hoang_Phuc\SP26\EXE101\project

docker run -d --rm --name cvfit-alembic-validation ^
  -e POSTGRES_USER=cvfit ^
  -e POSTGRES_PASSWORD=cvfit ^
  -e POSTGRES_DB=cvfit_migration_test ^
  -p 55432:5432 ^
  pgvector/pgvector:pg16

set DATABASE_URL=postgresql+psycopg2://cvfit:cvfit@localhost:55432/cvfit_migration_test
set REDIS_URL=redis://localhost:6379/0

cd backend
alembic heads
alembic history
alembic current
alembic upgrade head
alembic current

cd ..
python scripts\check_db_schema.py
docker stop cvfit-alembic-validation
```

Expected result:
- `alembic heads` shows one head: `20260522_0001`.
- `alembic current` after upgrade shows `20260522_0001 (head)`.
- `python scripts\check_db_schema.py` reports baseline schema check passed.
- Production DB is not touched.

## Smoke sau migration

```powershell
uvicorn app.main:app --reload --port 8000
curl.exe -i http://localhost:8000/health
```

Sau đó chạy luồng:
- upload CV,
- create score job,
- poll job,
- get result với token,
- download report với token.

## Production caution

Nếu production đã có bảng được tạo thủ công trước đó, cần xác định:
- Alembic version table đã có chưa?
- schema hiện tại có drift so với models không?
- có cần `alembic stamp head` cho baseline không?

Không stamp bừa nếu chưa so schema.
