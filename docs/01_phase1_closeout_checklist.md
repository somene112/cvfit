# Phase 1 Closeout Checklist — AI CV Fit

Deadline nội bộ: Thứ Bảy, 30/05/2026  
Nguyên tắc: không chốt bằng cảm tính; mỗi mục cần có evidence.

| Nhóm việc | Task | Owner | Status | Evidence cần có | Blocker | Must-have before close? | Can move Phase 2? |
|---|---|---:|---|---|---|---|---|
| Deploy | Render backend chạy ổn | Phúc | TODO | `/health` OK, logs không crash | Env / build / start command | Yes | No |
| Deploy | Worker chạy ổn | Phúc/Đạt | TODO | queue job chạy từ queued → running → succeeded/failed rõ | Redis/Celery/env | Yes | No |
| Storage | S3 upload/download smoke | Phúc | TODO | upload CV thành công, report download được | AWS credentials, bucket, region | Yes | No |
| Security MVP | Access token bảo vệ result/report | Phúc/Đạt | TODO | không token → 401/403; token đúng → 200; token sai → 401/403 | API chưa enforce | Yes | No |
| API Contract | Contract cho Next frontend | Phúc | TODO | `docs/api-contract-next.md` merge vào repo | Endpoint chưa thống nhất | Yes | No |
| Frontend | Next landing page | Quân | TODO | mở được page deploy/local | Design/API mismatch | Yes | No, nếu Jinja fallback |
| Frontend | Analyze page: upload CV + paste JD | Quân | TODO | gửi request thật tới backend | CORS/API contract | Yes | No, nếu Jinja fallback |
| Frontend | Loading/result/download flow | Quân + Phúc | TODO | job polling + result + download OK | access_token handling | Yes | No, nếu Jinja fallback |
| Migration | Alembic baseline validation | Đạt/Phúc | DONE | disposable PostgreSQL/pgvector DB chạy `alembic upgrade head` OK | none | Yes | No |
| Cleanup | S3 lifecycle cleanup | Phúc/Đạt | DONE | lifecycle policy applied and verified on bucket | none | Should | Yes, nếu có runbook |
| Docs | Runbook smoke test | Phúc | TODO | `docs/runbook-phase1.md` có lệnh chạy | thiếu endpoint/env | Yes | No |
| Product | Phase 2 Product Spec | Phúc | TODO | `docs/phase2-product-spec.md` | chưa thống nhất scope | Should | No |
| Demo | Demo script 3–5 phút | Phúc | TODO | script + fallback notes | Next chưa ổn | Yes | No |

## Definition of Done Phase 1

Phase 1 chỉ nên close khi đạt tối thiểu:

- Người dùng upload được CV/PDF hoặc DOCX hợp lệ.
- Người dùng paste JD.
- Backend tạo job async thành công.
- FE hoặc Jinja fallback hiển thị được trạng thái loading.
- Result trả về score/feedback tối thiểu.
- Report download được.
- Result/report bị chặn nếu thiếu hoặc sai access_token.
- Không log raw CV, không log access_token.
- Có lệnh smoke test repeatable.
- Có quyết định rõ: Next frontend dùng demo chính hay Jinja fallback.

## Quy tắc xử lý nếu có blocker

| Blocker | Quyết định |
|---|---|
| Next frontend chưa gọi được API thật | Giữ Jinja làm fallback demo; Quân tiếp tục Phase 2 polish |
| Alembic chưa chắc chắn | Không chạy trực tiếp lên production DB; validate trên disposable DB trước |
| S3 cleanup chưa set được | Viết runbook + tạo issue Phase 1.5; không block demo nếu storage smoke OK |
| Login chưa có | Không ép làm trước deadline; dùng access_token guest mode |
| Worker lỗi | Ưu tiên sửa trước mọi feature khác vì analysis flow phụ thuộc worker |

## Evidence note - backend access-token audit 2026-05-27

- Checked implemented Phase 1 backend endpoints: `POST /v1/cv/upload`, `POST /v1/jobs/create-score`, `GET /v1/jobs/{job_id}`, `GET /v1/jobs/{job_id}/result`, `GET /v1/jobs/{job_id}/report`, and `GET /v1/jobs/{job_id}/report/download`.
- Added small compatibility support for the documented `cv_id` and `job_description` create-score request fields while preserving existing `cv_file_id` and `jd_text`.
- Verified result/report/download endpoints require `access_token`; missing or wrong tokens are rejected, correct tokens are accepted.
- Added tests for documented request aliases, queued create-score response status, result internal-path scrubbing, report metadata internal-path hiding, and sanitized worker error messages.
- Added root pytest config so `python -m pytest backend/tests -q` works from the repository root without manual `PYTHONPATH` or temp-dir setup.
- Render deployment smoke was later completed; see evidence note below.

## Evidence note - Render backend smoke 2026-05-27

- Render backend smoke passed against the deployed backend.
- `/health` returned OK.
- CV upload completed successfully using a temporary dummy DOCX.
- Create-score returned `job_id` and `access_token`.
- Missing and wrong access tokens were rejected for result, report metadata, and report download.
- Correct access token allowed result, report metadata, and report download.

## Evidence note - Alembic disposable DB validation 2026-05-27

- Alembic heads checked: single head `20260522_0001`.
- Alembic history checked: `<base> -> 20260522_0001 (head)`.
- App metadata imported cleanly with `analysis_jobs`, `cv_files`, `jd_docs`, and `text_embeddings`.
- `alembic upgrade head` validated against a disposable local PostgreSQL/pgvector database.
- Baseline schema check passed, including required tables, `alembic_version`, and `vector` extension.
- Production DB was not touched.

## Evidence note - S3 lifecycle cleanup 2026-05-27

- Lifecycle policy applied to bucket `2026-fpt-exe-app` in region `ap-southeast-2`.
- Existing bucket lifecycle config was checked before apply; no lifecycle config existed.
- Verified lifecycle rules after apply: `expire-temporary-uploads`, `expire-raw-cv-uploads`, `expire-generated-reports`, and `abort-incomplete-multipart-uploads`.
- No manual S3 object deletion was performed.
