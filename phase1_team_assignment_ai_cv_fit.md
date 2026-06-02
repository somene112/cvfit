# AI CV Fit App — Phase 1 Team Assignment

## 1. Trạng thái hiện tại

Phase 0 Final Baseline đã được chốt ở mức kỹ thuật:

- Repository đã tách rõ `backend/` và `frontend/`.
- Backend dùng FastAPI, Celery worker, Redis, PostgreSQL/pgvector.
- Frontend hiện là Jinja template + vanilla JS.
- Storage abstraction đã hỗ trợ `local` và `s3`.
- Local Docker E2E smoke test đã pass.
- S3-backed Docker smoke test đã pass.
- Dependency đã được split, Docker dùng CPU-only Torch.
- Tài liệu roadmap và Phase 1 plan đã có.

Phase 1 bắt đầu từ nền này, mục tiêu là đưa project từ baseline chạy được sang MVP demo/deploy được.

---

## 2. Mục tiêu Phase 1

Phase 1 tập trung vào 3 hướng chính:

1. Deploy thử trên Render với S3-compatible storage.
2. Làm UI đủ đẹp và rõ để demo.
3. Tăng chất lượng backend: access token, migration baseline, tests, S3 cleanup.

Definition of Done của Phase 1:

- Render API URL `/health` chạy được.
- Upload CV từ UI/API chạy được.
- Tạo scoring job chạy được.
- Worker xử lý job thành công.
- Result JSON trả về đúng.
- DOCX report download được.
- S3 lưu CV/report đúng prefix.
- UI có loading/error/result state rõ ràng.
- Result/report không còn chỉ dựa vào public `job_id` nếu access token MVP được merge.
- Có migration baseline và test coverage tăng.

---

## 3. Phân công team

## Phúc — Backend / Deployment Lead

### Trách nhiệm chính

Phúc phụ trách triển khai hạ tầng MVP và kiểm chứng deploy flow.

### Việc cần làm

1. Review các tài liệu deploy hiện có:
   - `docs/render_deployment.md`
   - `docs/render_manual_setup_checklist.md`
   - `docs/s3_smoke_test.md`

2. Setup Render:
   - Render Web Service cho FastAPI API.
   - Render Background Worker cho Celery.
   - Render Redis/Key Value.
   - Render Postgres.
   - S3-compatible bucket/prefix cho CV và report.

3. Set env vars giống nhau cho API và worker:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `STORAGE_BACKEND=s3`
   - `S3_BUCKET`
   - `S3_REGION`
   - `S3_PREFIX`
   - `S3_ENDPOINT_URL` nếu dùng provider không phải AWS S3.
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `CV_MAX_UPLOAD_MB`

4. Chạy smoke test sau deploy:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_s3.py
```

5. Ghi lại lỗi và cách fix nếu Render deploy fail.

### Deliverables

- Render Web Service chạy được.
- Render Worker chạy được.
- Smoke test against Render URL pass.
- Deploy checklist được cập nhật nếu có chỉnh sửa thực tế.

---

## Quân — Frontend / UI Owner

### Trách nhiệm chính

Quân phụ trách làm UI demo rõ ràng, dễ hiểu, không cần đọc JSON thô.

### Việc cần làm

1. Làm lại bố cục trang chính trong:
   - `frontend/templates/index.html`
   - `frontend/static/app.js`

2. Cải thiện các khu vực chính:
   - Upload CV section.
   - JD input section.
   - Submit/analyze button.
   - Loading/progress state.
   - Error state.
   - Result section.
   - Download report button.

3. Result dashboard nên hiển thị:
   - Overall fit score.
   - Matched skills.
   - Missing skills.
   - Strengths.
   - Improvement suggestions.
   - Report download CTA.

4. Không đổi API contract nếu chưa thống nhất với backend.

### Deliverables

- UI demo mượt từ upload đến report.
- Có loading/error/result states rõ ràng.
- Không phá smoke test hiện tại.
- Có screenshot/demo flow để team review.

---

## Đạt — Backend Quality / Database / Testing Owner

### Trách nhiệm chính

Đạt phụ trách tăng độ an toàn và maintainability cho backend.

### Việc cần làm

1. Thiết kế access token MVP:
   - Mỗi job có `access_token`.
   - Result/report endpoint cần token.
   - Frontend nhận/lưu token sau khi tạo job.
   - Chưa cần full login/auth.

2. Alembic migration baseline:
   - Init Alembic.
   - Tạo migration đầu tiên cho schema hiện tại.
   - Document cách chạy migration.

3. Mở rộng tests:
   - Bad token.
   - Missing token.
   - Valid token.
   - Bad job id.
   - Missing report.
   - Upload invalid file.
   - Worker failure.

4. S3 cleanup/lifecycle:
   - Viết checklist hoặc docs cho cleanup object theo prefix.
   - Gợi ý lifecycle policy cho bucket/prefix dev/demo.

### Deliverables

- Access token MVP PR.
- Alembic baseline PR.
- Test suite tăng coverage.
- S3 cleanup checklist.

---

## 4. Branch đề xuất

```bash
# Phúc
git checkout -b phase1/render-deploy-s3

# Quân
git checkout -b phase1/frontend-mvp-polish

# Đạt
git checkout -b phase1/backend-quality-access-token
```

---

## 5. Timeline gợi ý 5 ngày

### Ngày 1

- Phúc: kiểm tra checklist Render, chuẩn bị env vars và services.
- Quân: vẽ lại UI flow, xác định result fields cần hiển thị.
- Đạt: đọc models/routes, đề xuất thiết kế access token và migration.

### Ngày 2

- Phúc: deploy API + worker lần đầu trên Render.
- Quân: implement layout/upload/JD/loading/error states.
- Đạt: implement access token MVP hoặc Alembic baseline.

### Ngày 3

- Phúc: chạy smoke test against Render URL, fix env/deploy issues.
- Quân: implement result dashboard + download report UX.
- Đạt: thêm tests cho access token/API cases.

### Ngày 4

- Phúc: cập nhật deploy docs theo kinh nghiệm thật.
- Quân: polish UI, kiểm tra lỗi edge cases.
- Đạt: hoàn thiện migration docs + S3 cleanup checklist.

### Ngày 5

- Cả team: merge từng PR nhỏ.
- Chạy lại local Docker smoke test.
- Chạy lại Render smoke test.
- Chuẩn bị demo script.

---

## 6. Integration checklist

Trước khi merge vào main:

```bash
python -m compileall backend/app
cd backend && python -m pytest
cd ..
docker compose config
python scripts/smoke_test_local.py
```

Nếu test Render:

```bash
API_BASE_URL=https://<render-api-url> python scripts/smoke_test_s3.py
```

Không merge nếu:

- Smoke test fail.
- Có file CV/report bị track vào Git.
- Có secret trong code/docs.
- UI gọi sai API contract.
- Worker không xử lý được job.

---

## 7. Thứ tự ưu tiên Phase 1

1. Render deploy + smoke test.
2. UI polish cho demo.
3. Access token MVP.
4. Alembic migration baseline.
5. S3 cleanup/lifecycle checklist.
6. Test coverage mở rộng.

