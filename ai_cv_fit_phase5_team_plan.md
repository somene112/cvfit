# AI CV Fit App — Phase 5 Team Plan

**Ngày lập:** 2026-06-10  
**Team:** Phúc — Quân — Đạt  
**Trạng thái đầu vào:** Phase 4 đã hoàn thành và đã qua review/audit.  
**Phase 5 theme:** **Application Readiness Suite — Career Workspace, Application Package, Interview Practice, Demo Hardening**

---

## 1. Tư duy chính của Phase 5

Phase 1 đã tạo deployable baseline.  
Phase 2 đã có frontend/auth/product flow.  
Phase 3 đã nâng scoring/explainability/result/report/evaluation.  
Phase 4 đã có improvement loop, before/after comparison, safe action plan, interview prep, learning roadmap.

Phase 5 nên chuyển sản phẩm từ:

```text
Tôi biết CV của mình fit thế nào và sửa được gì
```

sang:

```text
Tôi có một workspace để chuẩn bị ứng tuyển thật:
- lưu target jobs,
- chọn CV version tốt nhất,
- tạo application package,
- luyện phỏng vấn,
- theo dõi readiness,
- xuất demo/report chuyên nghiệp.
```

Phase 5 cần giúp sản phẩm nhìn giống một **career readiness platform** thay vì một công cụ chấm điểm đơn lẻ.

---

## 2. Phase 5 Objective

Phase 5 có mục tiêu xây dựng lớp sản phẩm phục vụ demo gần cuối:

1. Tạo **Application Workspace** cho user.
2. Cho phép user quản lý các target jobs/JDs.
3. Gắn CV versions, analyses, comparisons, roadmap, interview prep vào một application workspace.
4. Tạo **Application Package** gồm:
   - best-fit CV analysis,
   - cover letter draft,
   - interview prep pack,
   - learning roadmap,
   - readiness summary,
   - downloadable report.
5. Bổ sung **Interview Practice v2**:
   - user trả lời câu hỏi,
   - hệ thống chấm bằng rubric đơn giản,
   - feedback không bịa và bám evidence.
6. Bổ sung **Career Profile / Evidence Vault v1**:
   - lưu skills/projects/experience user khai báo,
   - dùng làm nguồn evidence an toàn cho rewrite/cover letter/interview.
7. Tăng product polish:
   - dashboard,
   - empty states,
   - demo data,
   - onboarding,
   - observability,
   - release checklist.
8. Đảm bảo toàn bộ flow vẫn evidence-first, không khuyến khích bịa CV.

---

## 3. Product Direction Phase 5

AI CV Fit App nên được định vị là:

> **Career Readiness Platform for Students/Freshers**  
> Một nền tảng giúp ứng viên phân tích CV với JD, cải thiện CV có bằng chứng, chuẩn bị phỏng vấn, tạo application package và theo dõi mức độ sẵn sàng ứng tuyển.

Không cạnh tranh trực diện bằng “ATS score” đơn thuần. Thay vào đó, Phase 5 phải chứng minh:

```text
Analysis → Improvement → Comparison → Interview Practice → Application Package → Readiness Tracking
```

---

## 4. Product Pillars Phase 5

Phase 5 gồm 7 pillar lớn.

---

# Pillar 1 — Application Workspace

User có thể tạo workspace cho từng job/JD muốn ứng tuyển.

Mỗi workspace gồm:

```text
application_id
job_title
company_name optional
jd_text
target_role
created_at
status
linked_cv_versions
analysis_jobs
best_analysis_job
interview_prep
learning_roadmap
cover_letter_draft
readiness_score
```

Status đề xuất:

```text
draft
analyzing
improving_cv
ready_to_apply
interview_prep
applied
archived
```

Mục tiêu:

- gom mọi thứ của một lần ứng tuyển vào một nơi,
- tránh user phải tìm lại job_id/report rời rạc,
- làm demo product có cấu trúc hơn.

---

# Pillar 2 — Application Package Generator

Từ result/comparison/interview/roadmap, hệ thống sinh một package:

1. Readiness summary.
2. Best CV version recommendation.
3. Cover letter draft v1.
4. Interview prep pack.
5. Learning roadmap.
6. Evidence checklist.
7. Exportable DOCX/PDF/Markdown report.

Package này cần có disclaimer:

```text
This package is generated from your uploaded CV, JD and extracted evidence. Do not include skills or experience that are not true.
```

---

# Pillar 3 — Cover Letter Draft v1

Tạo cover letter draft từ:

- JD,
- CV evidence,
- matched skills,
- projects,
- readiness summary.

Guardrail bắt buộc:

- Không bịa công ty/project/skill.
- Nếu thiếu evidence, không tự thêm.
- Dùng wording trung tính.
- Có phần “needs user review”.

Cấu trúc cover letter:

```text
Opening
Why this role/company
Relevant evidence from CV
Contribution fit
Closing
Review notes
```

---

# Pillar 4 — Interview Practice v2

Phase 4 có Interview Prep Pack. Phase 5 nâng thành practice nhẹ:

1. User chọn câu hỏi.
2. User nhập câu trả lời.
3. Backend chấm theo rubric:
   - relevance,
   - specificity,
   - evidence,
   - structure,
   - risk/gap.
4. Feedback:
   - điểm mạnh,
   - thiếu evidence gì,
   - nên bổ sung ý nào,
   - câu trả lời mẫu outline.

Không làm full voice/chat interview engine trong Phase 5.

---

# Pillar 5 — Career Profile / Evidence Vault v1

User có thể khai báo structured evidence:

```text
skills
projects
education
certifications
work_experience
achievements
links
```

Mục tiêu:

- dùng làm nguồn evidence an toàn,
- giảm nguy cơ hallucination,
- giúp cover letter/rewrite/interview prep bám dữ liệu user thật.

MVP chỉ cần CRUD nhẹ:

- add project,
- add skill,
- add achievement,
- link evidence to CV/JD suggestions.

---

# Pillar 6 — Readiness Dashboard

Dashboard tổng hợp:

1. Applications in progress.
2. Average fit score.
3. Top missing skills.
4. Recent improvements.
5. Interview prep status.
6. Roadmap progress.
7. Ready-to-apply applications.

MVP có thể chỉ là dashboard đơn giản sau login.

---

# Pillar 7 — Demo & Release Hardening

Vì hạn demo gần, Phase 5 cần có demo readiness:

1. Seed demo user.
2. Sample CV/JD.
3. Demo script.
4. Error-proof flow.
5. Loading states.
6. Render smoke.
7. Frontend smoke/manual QA.
8. Basic observability/log checklist.
9. Production-ish privacy copy.
10. Cleanup policy.

---

## 5. Phase 5 Scope

## 5.1 Must-have

Các việc bắt buộc để chốt Phase 5:

1. Application Workspace v1.
2. User có thể lưu target JD/job.
3. Workspace gắn với analysis jobs.
4. Best analysis selection hoặc latest analysis display.
5. Application Package v1.
6. Cover Letter Draft v1 có guardrails.
7. Interview Practice v2:
   - answer input,
   - rubric scoring,
   - feedback.
8. Career Profile / Evidence Vault v1 tối thiểu:
   - skills,
   - projects,
   - achievements.
9. Readiness Dashboard v1.
10. Frontend pages cho workspace/package/interview/profile.
11. Backend APIs cho workspace/profile/interview/package.
12. Tests cho auth/ownership/access control.
13. Guardrails v3.
14. Evaluation cases cho cover letter/interview/profile evidence.
15. Render smoke pass.
16. Demo script và seed/demo data.

---

## 5.2 Should-have

1. Application status tracking.
2. Export application package as DOCX.
3. Cover letter edit/save.
4. Interview answer history.
5. Roadmap progress tracking.
6. Profile evidence linking to suggestions.
7. Admin/debug demo panel.
8. Basic usage analytics:
   - jobs analyzed,
   - reports generated,
   - failures,
   - average job duration.

---

## 5.3 Could-have

1. PDF export.
2. Email package to user.
3. Shareable read-only application package.
4. Multi-job comparison.
5. LinkedIn profile checklist.
6. Company-specific preparation notes.
7. Calendar reminder for interview prep.
8. Import JD from URL.
9. Recruiter view demo-only.

---

## 5.4 Out-of-scope

Không làm trong Phase 5:

1. Payment/subscription.
2. Real recruiter multi-tenant dashboard.
3. Full job board crawling at scale.
4. Voice interview.
5. Browser extension.
6. Mobile app.
7. Enterprise admin system.
8. Full collaborative editing.
9. Automated apply-to-job feature.
10. Uncontrolled LLM rewrite without evidence.

---

## 6. Proposed Backend Data Model

Có thể thêm các bảng:

## applications

```text
id
user_id
job_title
company_name
jd_text
target_role
status
best_analysis_job_id nullable
created_at
updated_at
```

## career_profile_items

```text
id
user_id
item_type
title
description
skills_json
evidence_text
source
created_at
updated_at
```

item_type:

```text
skill
project
experience
education
certification
achievement
link
```

## interview_answers

```text
id
user_id
application_id
job_id nullable
question
answer_text
rubric_json
feedback_json
created_at
```

## application_artifacts

```text
id
user_id
application_id
artifact_type
payload_json
storage_key nullable
created_at
```

artifact_type:

```text
application_package
cover_letter_draft
interview_practice_result
readiness_summary
```

Có thể giản lược nếu migration quá nặng, nhưng Phase 5 nên bắt đầu có cấu trúc dữ liệu tốt.

---

## 7. Proposed API Endpoints

## Applications

```text
POST /v1/applications
GET /v1/applications
GET /v1/applications/{application_id}
PATCH /v1/applications/{application_id}
DELETE /v1/applications/{application_id}
POST /v1/applications/{application_id}/attach-analysis/{job_id}
GET /v1/applications/{application_id}/readiness
```

## Application Package

```text
POST /v1/applications/{application_id}/package/generate
GET /v1/applications/{application_id}/package
GET /v1/applications/{application_id}/package/download
```

## Cover Letter

```text
POST /v1/applications/{application_id}/cover-letter/generate
GET /v1/applications/{application_id}/cover-letter
PATCH /v1/applications/{application_id}/cover-letter
```

## Career Profile / Evidence Vault

```text
POST /v1/profile/items
GET /v1/profile/items
GET /v1/profile/items/{item_id}
PATCH /v1/profile/items/{item_id}
DELETE /v1/profile/items/{item_id}
```

## Interview Practice

```text
GET /v1/applications/{application_id}/interview/questions
POST /v1/applications/{application_id}/interview/answers
GET /v1/applications/{application_id}/interview/answers
```

---

## 8. Frontend Pages

Quân cần làm hoặc mở rộng:

```text
/dashboard
/applications
/applications/new
/applications/[id]
/applications/[id]/package
/applications/[id]/cover-letter
/applications/[id]/interview
/profile
/profile/evidence
```

Các page chính:

1. Dashboard.
2. Applications list.
3. Application detail.
4. Application package.
5. Cover letter editor.
6. Interview practice.
7. Career profile/evidence vault.

---

## 9. Team Assignment

---

# 9.1 Phúc — Backend/Product/Architecture Lead

## Vai trò

Phúc chịu trách nhiệm backend architecture, API contract, application workspace, package generation, cover letter guardrails, interview scoring, migration, deploy và release.

## Responsibilities

1. Phase 5 product/API contract.
2. Data model design.
3. Alembic migrations.
4. Application workspace backend.
5. Career profile/evidence vault backend.
6. Application package backend.
7. Cover letter draft backend.
8. Interview practice backend.
9. Readiness summary logic.
10. Render deploy/smoke.
11. Docs/release notes.

## Files/Folders likely touched

```text
backend/app/api/routes/
backend/app/api/routes/applications.py
backend/app/api/routes/profile.py
backend/app/api/routes/interview.py
backend/app/db/models.py
backend/app/schemas/
backend/app/services/application/
backend/app/services/cover_letter/
backend/app/services/interview/
backend/app/services/profile/
backend/app/services/readiness/
backend/app/services/reporting/
backend/alembic/versions/
docs/phase5_team_plan.md
docs/application_workspace_contract.md
docs/cover_letter_guardrails.md
docs/interview_practice_contract.md
README.md
scripts/smoke_test_local.py
scripts/smoke_test_s3.py
```

## Deliverables

1. `docs/application_workspace_contract.md`
2. `docs/interview_practice_contract.md`
3. `docs/cover_letter_guardrails.md`
4. Application APIs.
5. Profile APIs.
6. Package generation API.
7. Cover letter generation API.
8. Interview practice API.
9. Alembic migrations.
10. Readiness summary logic.
11. Render smoke pass.
12. Demo data/seed script if needed.

## Acceptance Criteria

- Logged-in user can create an application workspace.
- User can attach analysis job to application.
- User can generate application package.
- User can generate cover letter draft.
- User can save/view career profile evidence.
- User can answer interview question and receive rubric feedback.
- User cannot access another user's application/profile/interview data.
- Auth/history/result flows from earlier phases still work.
- Render smoke passes.

## Dependencies

- Quân needs API contracts early.
- Đạt needs output schema to write tests/evaluation.
- Phúc needs guardrail cases from Đạt to refine generation logic.

---

# 9.2 Quân — Frontend/Product UX Owner

## Vai trò

Quân chịu trách nhiệm biến Phase 5 thành demo sản phẩm hoàn chỉnh: dashboard, applications, package, cover letter, interview practice, profile/evidence UI.

## Responsibilities

1. Dashboard v1.
2. Applications list/detail.
3. New application flow.
4. Application package UI.
5. Cover letter editor UI.
6. Interview practice UI.
7. Career profile/evidence vault UI.
8. Readiness score/progress UI.
9. Empty/loading/error states.
10. Demo polish.

## Files/Folders likely touched

```text
frontend/
frontend/app/dashboard/
frontend/app/applications/
frontend/app/applications/[id]/
frontend/app/profile/
frontend/components/applications/
frontend/components/package/
frontend/components/cover-letter/
frontend/components/interview/
frontend/components/profile/
frontend/components/readiness/
frontend/lib/api.ts
frontend/lib/auth.ts
frontend/lib/types.ts
```

## Deliverables

1. Dashboard page.
2. Applications list page.
3. New application page.
4. Application detail page.
5. Application package page.
6. Cover letter draft/editor page.
7. Interview practice page.
8. Career profile page.
9. Readiness summary widgets.
10. Demo-polished loading/error/empty states.

## Acceptance Criteria

- User sees dashboard after login.
- User can create application workspace.
- User can view target JD/application detail.
- User can navigate to package/cover letter/interview/profile.
- User can generate and view cover letter.
- User can answer interview question.
- User can see feedback.
- UI does not leak JWT/access token.
- UI handles 401/403/404/500 gracefully.
- Demo can be run without explaining internal API details.

## Dependencies

- Needs Phúc's API contracts.
- Needs Đạt's QA checklist and guardrail wording.
- Needs stable backend for final integration.

---

# 9.3 Đạt — QA/Evaluation/Guardrails/Release Owner

## Vai trò

Đạt chịu trách nhiệm kiểm tra chất lượng, test security/ownership, đánh giá guardrails cho cover letter/interview/profile, và chuẩn bị demo closeout.

## Responsibilities

1. Evaluation cases for application package.
2. Cover letter guardrail tests.
3. Interview practice evaluation.
4. Career profile/evidence validation tests.
5. Application ownership/access tests.
6. API route tests.
7. Frontend manual QA checklist.
8. Demo data QA.
9. Release checklist.
10. Phase 5 closeout audit.

## Files/Folders likely touched

```text
backend/tests/
evaluation/cases/application_package/
evaluation/cases/cover_letter/
evaluation/cases/interview_practice/
evaluation/cases/profile_evidence/
scripts/evaluate_application_package.py
scripts/evaluate_interview_practice.py
docs/guardrails_v3.md
docs/phase5_demo_checklist.md
docs/phase5_closeout_audit.md
```

## Evaluation Requirements

### Cover Letter

Tối thiểu:

1. 5 good evidence cases.
2. 3 weak evidence cases.
3. 3 missing skill cases.
4. 3 hallucination-risk cases.
5. 2 irrelevant CV/JD cases.

### Interview Practice

Tối thiểu:

1. 5 technical questions.
2. 5 project deep-dive questions.
3. 5 behavioral questions.
4. 3 weak answer feedback cases.
5. 3 strong answer feedback cases.

### Profile Evidence

Tối thiểu:

1. 5 project evidence cases.
2. 5 skill evidence cases.
3. 3 achievement/metric cases.
4. 3 cases where profile evidence should not be used because it is unrelated.

## Tests cần có

1. User cannot access another user's applications.
2. User cannot access another user's profile items.
3. User cannot access another user's interview answers.
4. Application package generation requires owner.
5. Cover letter generation does not fabricate missing evidence.
6. Interview feedback references JD/CV/profile evidence.
7. Profile items validate type and ownership.
8. Empty profile does not break package generation.
9. Wrong token/JWT returns 401/403.
10. Existing analysis/result/report smoke still passes.

## Guardrails v3

Tạo/cập nhật:

```text
docs/guardrails_v3.md
```

Nội dung:

- Cover letter guardrails.
- Interview feedback guardrails.
- Career profile evidence guardrails.
- No fabricated claims.
- No hiring guarantee.
- User review required.
- Token/privacy logging.
- Demo data privacy.
- Output wording standards.

## Deliverables

1. Evaluation datasets.
2. Evaluation scripts.
3. Backend tests.
4. Guardrails v3 docs.
5. Phase 5 demo checklist.
6. Phase 5 closeout audit template.
7. Manual QA report.

## Acceptance Criteria

- Tests pass.
- Evaluation scripts run.
- Guardrails cover all new generative/suggestion features.
- No output fabricates experience.
- No ownership leak.
- Demo checklist complete.
- Render smoke passes.

---

## 10. Phase 5 Timeline Proposal

## Day 1 — Contracts & DB Design

### Phúc
- Create API contracts:
  - application workspace,
  - profile/evidence,
  - cover letter,
  - interview practice.
- Design DB models/migrations.

### Quân
- Create route/page skeleton:
  - dashboard,
  - applications,
  - application detail,
  - profile,
  - interview.

### Đạt
- Create QA plan.
- Draft guardrails v3.
- Create evaluation folder skeletons.

---

## Day 2 — Application Workspace + Profile

### Phúc
- Implement application APIs.
- Implement profile item APIs.
- Add migrations.
- Basic ownership checks.

### Quân
- Implement dashboard/applications UI.
- Implement profile/evidence UI.

### Đạt
- Tests for ownership/profile/application.
- Profile evidence evaluation cases.

---

## Day 3 — Application Package + Cover Letter

### Phúc
- Implement package generator.
- Implement cover letter draft generator.
- Add guardrails in backend.

### Quân
- Implement package page.
- Implement cover letter editor/view page.

### Đạt
- Cover letter evaluation cases.
- Hallucination-risk tests.

---

## Day 4 — Interview Practice

### Phúc
- Implement interview questions/answers APIs.
- Implement rubric feedback logic.

### Quân
- Implement interview practice UI.
- Implement answer submission and feedback display.

### Đạt
- Interview practice evaluation cases.
- Tests for feedback quality and ownership.

---

## Day 5 — Readiness Dashboard + Polish

### Phúc
- Implement readiness summary.
- Ensure package/report works.
- Update smoke scripts if needed.

### Quân
- Dashboard readiness widgets.
- Empty/loading/error polish.
- Responsive demo polish.

### Đạt
- Guardrails v3 final.
- Manual QA checklist.
- Evaluation scripts.

---

## Day 6 — Integration

### Cả team
- Merge PRs.
- Run backend tests.
- Run frontend build/lint if available.
- Run local smoke.
- Deploy Render.
- Run Render smoke.

---

## Day 7 — Demo Hardening & Closeout

### Cả team
- Seed demo data.
- Create demo script.
- Capture screenshots.
- Fix critical UX bugs.
- Write phase closeout audit.
- Final Render smoke.

---

## 11. First PR Sequence

## PR 1 — Phase 5 Contracts Only

Owner: Phúc

Files:

```text
docs/phase5_team_plan.md
docs/application_workspace_contract.md
docs/interview_practice_contract.md
docs/cover_letter_guardrails.md
docs/guardrails_v3.md draft
```

Why first:
- Quân needs API contract.
- Đạt needs output rules for tests.
- Reduces backend/frontend mismatch.
- No product code risk.

---

## PR 2 — Evaluation/Guardrails Skeleton

Owner: Đạt

Files:

```text
evaluation/cases/application_package/
evaluation/cases/cover_letter/
evaluation/cases/interview_practice/
evaluation/cases/profile_evidence/
docs/guardrails_v3.md
```

---

## PR 3 — Backend Application/Profile APIs

Owner: Phúc

Files:

```text
backend/app/api/routes/applications.py
backend/app/api/routes/profile.py
backend/app/db/models.py
backend/alembic/versions/
backend/app/schemas/
```

---

## PR 4 — Frontend Workspace/Profile UI

Owner: Quân

Files:

```text
frontend/app/dashboard/
frontend/app/applications/
frontend/app/profile/
frontend/components/
```

---

## PR 5 — Package/Cover Letter Backend + Frontend

Owner: Phúc + Quân

---

## PR 6 — Interview Practice Backend + Frontend

Owner: Phúc + Quân

---

## PR 7 — QA, Guardrails, Demo Closeout

Owner: Đạt + Phúc + Quân

---

## 12. Definition of Done

Phase 5 hoàn thành khi:

1. User có dashboard sau login.
2. User tạo được application workspace.
3. User lưu target JD/job.
4. User gắn analysis vào application.
5. User xem application package.
6. User tạo cover letter draft.
7. Cover letter không bịa evidence.
8. User có career profile/evidence vault.
9. User tạo/sửa/xóa profile items.
10. User có interview practice page.
11. User trả lời câu hỏi và nhận feedback.
12. Interview feedback bám CV/JD/profile evidence.
13. User thấy readiness summary.
14. Ownership/access control đúng.
15. Tests backend pass.
16. Frontend build/lint pass nếu có.
17. Evaluation scripts chạy được.
18. Guardrails v3 có.
19. S3/report/analyze flows không vỡ.
20. Local smoke pass.
21. Render smoke pass.
22. Demo data có.
23. Demo script có.
24. README/docs cập nhật.
25. Không leak token/JWT/secrets.
26. Không hallucinate/fabricate experience.
27. Phase 5 closeout audit ready.

---

## 13. Risks & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Scope quá lớn sát demo | Trễ | Làm theo PR sequence, must-have trước |
| Cover letter hallucinate | Rủi ro cao | Evidence vault + guardrails + tests |
| Interview feedback thiếu chất lượng | Demo yếu | Rubric đơn giản, bám evidence |
| Frontend quá nhiều pages | Quá tải Quân | Skeleton trước, polish sau |
| Backend migration lớn | Deploy lỗi | Migration nhỏ, test local trước |
| Ownership bug | Privacy risk | Đạt ưu tiên tests ownership |
| Render memory/build slow | Demo lỗi | Không đổi model nặng, smoke sớm |
| Application package quá phức tạp | Trễ | Payload JSON trước, export should-have |
| Demo data thiếu | Demo lủng củng | Seed demo data Day 7 |

---

## 14. Validation Commands

Sau mỗi backend PR:

```bash
python -m compileall backend/app
cd backend && python -m pytest --basetemp pytest-cache-files-local -p no:cacheprovider
docker compose config
```

Sau mỗi integration lớn:

```bash
python scripts/smoke_test_local.py
```

Sau deploy:

```bash
set "API_BASE_URL=https://cvfit.onrender.com"
python scripts/smoke_test_s3.py
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run lint
```

Nếu frontend command khác, Quân phải document lại trong README.

---

## 15. Immediate Next Actions

1. Phúc tạo branch:
   ```bash
   git checkout -b phase5/phuc-contracts-application-workspace
   ```
2. Quân tạo branch:
   ```bash
   git checkout -b phase5/quan-career-workspace-ui
   ```
3. Đạt tạo branch:
   ```bash
   git checkout -b phase5/dat-qa-guardrails-demo
   ```
4. PR đầu tiên nên là **contracts/docs only**.
5. Không code backend/frontend lớn trước khi contract PR được review.
6. Chuẩn bị demo data ngay từ đầu, không để sát deadline.
