# AI CV Fit App — Phase 6 Implementation Plan

**Ngày lập:** 2026-06-18  
**Team:** Phúc — Quân — Đạt  
**Trạng thái đầu vào:** Phase 5 đã hoàn thành, đã có closeout/audit, deployed checks và GA4 verification.  
**Phase 6 Theme:** **Product Expansion & JobReady Parity — Lightweight Career Operating System**

---

## 1. Phase 6 Baseline

Phase 5 đã đưa AI CV Fit App từ một application readiness MVP thành sản phẩm có các mảnh quan trọng:

- Application workspace.
- Career profile/evidence vault.
- Cover letter draft.
- Interview practice.
- Learning/help shell.
- Readiness dashboard.
- GA4 happy-path event verification.
- Deployed frontend/backend smoke pass.
- Team sign-off.

Theo định hướng Phase 6 đã chuẩn bị, Phase 6 nên chuyển từ “application readiness suite” sang một **career operating system nhẹ**, nơi user không chỉ phân tích CV/JD mà còn quản lý target jobs, học theo gap, luyện phỏng vấn nâng cao, nhận help assistant, chia sẻ readiness package và theo dõi usage/product metrics.

---

## 2. Phase 6 Product Goal

Phase 6 có mục tiêu:

> Giúp ứng viên quản lý nhiều target jobs, đóng skill gaps, luyện phỏng vấn, tạo/share readiness evidence và theo dõi tiến độ ứng tuyển — nhưng chưa overbuild marketplace, payment thật hoặc recruiter portal phức tạp.

Nói ngắn gọn:

```text
Saved Jobs
→ Learning Roadmap
→ Interview Practice v2
→ Help Assistant
→ Shareable Readiness
→ Usage/Plan Shell
→ Analytics & Product Ops
```

---

## 3. Phase 6 Modules

Phase 6 được chia thành 7 module chính:

```text
Phase 6A — Target Jobs / Saved JD Workspace
Phase 6B — Learning Roadmap Expansion
Phase 6C — Interview Practice v2
Phase 6D — Help Assistant / Career Coach v1
Phase 6E — Shareable Readiness / Recruiter-lite
Phase 6F — Usage / Plan / Credits Shell
Phase 6G — Analytics & Product Ops
```

Thứ tự triển khai ưu tiên:

```text
1. Phase 6A Target Jobs
2. Phase 6B Learning Roadmap
3. Phase 6C Interview Practice v2
4. Phase 6D Help Assistant
5. Phase 6E Shareable Readiness
6. Phase 6F Usage/Plan Shell
7. Phase 6G Analytics & Product Ops Closeout
```

---

## 4. Scope Discipline

## 4.1 In Scope

Phase 6 làm:

- Saved JD / Target Jobs workspace.
- Learning roadmap thật, dựa trên gaps từ analysis.
- Interview session flow nâng cấp.
- Guided Help Assistant có guardrails.
- Shareable readiness package với redact/revoke.
- Usage/plan shell chưa có payment thật.
- Analytics QA, event coverage, funnel spec, demo health check.
- E2E deployed closeout report.

## 4.2 Out of Scope for Early Phase 6

Không làm sớm:

- Full job marketplace scraping.
- Payment checkout thật.
- Recruiter company portal đầy đủ.
- Course marketplace.
- Video/WebRTC interview.
- Admin analytics dashboard lớn.
- Automated apply-to-job.
- Public share without security review.

Những phần này có thể để late Phase 6 hoặc Phase 7.

---

# 5. Phase 6A — Target Jobs / Saved JD Workspace

## 5.1 Goal

Biến `applications` hiện tại thành khu quản lý nhiều job mục tiêu rõ ràng hơn.

Hiện user có thể chuẩn bị một application, nhưng chưa có cảm giác:

```text
Tôi đang quản lý nhiều công việc muốn ứng tuyển.
```

Phase 6A cần tạo experience:

```text
/jobs
→ saved target jobs
→ each job has JD, company, status, readiness, best CV analysis, package
```

---

## 5.2 User Value

User có thể:

- lưu nhiều JD,
- lọc theo trạng thái,
- xem readiness từng job,
- gắn analysis vào từng job,
- mở application package từ từng job,
- biết job nào đã sẵn sàng apply.

---

## 5.3 Frontend Scope

Routes:

```text
/jobs
/jobs/new
/jobs/[id]
/jobs/[id]/compare
```

UI cần có:

1. Saved jobs list.
2. Create target job form:
   - job title,
   - company,
   - JD text,
   - target role,
   - source URL optional.
3. Job status badge.
4. Filter by status.
5. Readiness score card.
6. Attached analyses.
7. Best CV/version card.
8. Open application package CTA.
9. Compare CV fit across jobs.

Status:

```text
saved
analyzing
ready_to_apply
interviewing
applied
rejected
offer
archived
```

---

## 5.4 Backend Scope

Endpoints đề xuất:

```text
POST /v1/target-jobs
GET /v1/target-jobs
GET /v1/target-jobs/{job_id}
PATCH /v1/target-jobs/{job_id}
DELETE /v1/target-jobs/{job_id}
POST /v1/target-jobs/{job_id}/attach-analysis/{analysis_job_id}
GET /v1/target-jobs/{job_id}/readiness
GET /v1/target-jobs/{job_id}/package
```

Có thể map sang bảng `applications` hiện tại nếu đã có, hoặc tạo alias route để tránh migration lớn.

---

## 5.5 Data Model Notes

Nếu đã có bảng `applications`, mở rộng thay vì tạo bảng mới:

```text
applications.job_title
applications.company_name
applications.jd_text
applications.target_role
applications.status
applications.source_url nullable
applications.best_analysis_job_id nullable
applications.last_readiness_score nullable
applications.archived_at nullable
```

Nếu muốn tách rõ hơn:

```text
target_jobs
  id
  user_id
  title
  company
  jd_text
  status
  source_url
  created_at
  updated_at
```

Khuyến nghị: **reuse `applications` nếu schema hiện tại đã đủ gần**, chỉ bổ sung field nhỏ nếu cần.

---

## 5.6 Analytics Events

```text
target_job_created
target_job_updated
target_job_status_changed
target_job_analysis_attached
target_job_readiness_viewed
target_job_package_opened
```

---

## 5.7 Acceptance Criteria

- User tạo được target job từ JD.
- User edit title/company/status/JD.
- User filter được danh sách jobs.
- User gắn được CV analysis vào target job.
- User xem được score/readiness theo từng job.
- User mở được application package từ job.
- Không cần scraping/payment/recruiter portal.

---

# 6. Phase 6B — Learning Roadmap Expansion

## 6.1 Goal

Biến `/learning` shell thành roadmap thật dựa trên analysis gaps.

---

## 6.2 User Value

User không chỉ biết “thiếu FastAPI”, mà có task cụ thể:

```text
Learn FastAPI routing
Build mini API project
Add evidence to profile
Practice explaining API error handling
```

---

## 6.3 Frontend Scope

Routes:

```text
/learning
/learning/[id]
/jobs/[id]/learning
```

UI cần có:

1. Learning task list.
2. Group by skill category.
3. Priority:
   - high,
   - medium,
   - low.
4. Task type:
   - article,
   - project,
   - practice,
   - interview_prep,
   - profile_evidence.
5. Progress:
   - todo,
   - in_progress,
   - done.
6. Link task to job/application.
7. CTA: “Add evidence to profile”.
8. CTA: “Practice interview for this skill”.

---

## 6.4 Backend Scope

Endpoints đề xuất:

```text
POST /v1/learning/roadmaps/generate
GET /v1/learning/tasks
GET /v1/learning/tasks/{task_id}
PATCH /v1/learning/tasks/{task_id}
POST /v1/target-jobs/{job_id}/learning/generate
```

Learning task fields:

```text
id
user_id
target_job_id nullable
application_id nullable
analysis_job_id nullable
skill
category
priority
task_type
title
description
evidence_to_add
status
created_at
updated_at
```

---

## 6.5 Generation Rules

Roadmap phải dựa trên:

- missing skills,
- weak evidence,
- interview feedback,
- profile gaps.

Không được fake personalization.

Nếu thiếu dữ liệu:

```text
“Based on current analysis only...”
```

---

## 6.6 Analytics Events

```text
learning_roadmap_generated
learning_task_started
learning_task_completed
learning_task_linked_to_profile
learning_task_opened
```

---

## 6.7 Acceptance Criteria

- Một application/target job sinh được learning roadmap.
- User tick progress được.
- Roadmap task liên kết được với job/profile/evidence.
- Learning task không claim user đã có skill.
- Không làm course marketplace.

---

# 7. Phase 6C — Interview Practice v2

## 7.1 Goal

Nâng interview Q&A thành interview room/session có flow rõ hơn.

---

## 7.2 User Value

User có thể:

- tạo interview session,
- chọn loại câu hỏi,
- chọn difficulty,
- trả lời nhiều lần,
- xem score trend,
- nhận suggested improved answer,
- export interview summary.

---

## 7.3 Frontend Scope

Routes:

```text
/interview/sessions
/interview/sessions/new
/interview/sessions/[id]
/jobs/[id]/interview
```

UI cần có:

1. Interview setup page.
2. Question type selector:
   - technical,
   - behavioral,
   - project,
   - HR,
   - gap_check.
3. Difficulty:
   - easy,
   - medium,
   - hard.
4. Session question list.
5. Answer input.
6. Submit answer.
7. Rubric detail:
   - relevance,
   - evidence,
   - clarity,
   - structure,
   - confidence,
   - risk.
8. Retry answer.
9. Score trend.
10. Export summary.

---

## 7.4 Backend Scope

Endpoints đề xuất:

```text
POST /v1/interview/sessions
GET /v1/interview/sessions
GET /v1/interview/sessions/{session_id}
POST /v1/interview/sessions/{session_id}/questions/generate
POST /v1/interview/sessions/{session_id}/answers
GET /v1/interview/sessions/{session_id}/answers
GET /v1/interview/sessions/{session_id}/summary
```

Data model:

```text
interview_sessions
  id
  user_id
  target_job_id nullable
  application_id nullable
  analysis_job_id nullable
  session_type
  difficulty
  status
  created_at
  updated_at

interview_session_questions
  id
  session_id
  question_type
  difficulty
  question_text
  related_evidence_json
  rubric_json

interview_session_answers
  id
  session_id
  question_id
  answer_text
  score_json
  feedback_json
  attempt_number
  created_at
```

---

## 7.5 Guardrails

- Không chấm quá tự tin.
- Không nói user chắc chắn pass phỏng vấn.
- Feedback phải bám JD/CV/profile evidence.
- Nếu câu trả lời bịa skill, đánh dấu risk.
- Không expose raw answer in analytics.

---

## 7.6 Analytics Events

```text
interview_session_created
interview_question_generated
interview_answer_submitted
interview_feedback_viewed
interview_retry_clicked
interview_summary_exported
```

---

## 7.7 Acceptance Criteria

- User tạo được interview session.
- Có nhiều loại câu hỏi.
- User submit answer và nhận rubric.
- User xem lịch sử answer.
- User retry answer.
- Có recommendation cải thiện.
- Không cần video/camera/WebRTC.

---

# 8. Phase 6D — Help Assistant / Career Coach v1

## 8.1 Goal

Nâng `/help` static FAQ thành guided assistant có guardrails.

---

## 8.2 User Value

User có thể hỏi:

```text
Tôi nên làm gì tiếp?
Tại sao score thấp?
Job nào của tôi đã ready_to_apply?
Tôi nên luyện câu hỏi nào?
Skill gap quan trọng nhất là gì?
Cover letter có thiếu evidence gì?
```

Assistant trả lời dựa trên dữ liệu hiện tại, không đoán bừa.

---

## 8.3 Scope

Không làm chatbot tự do hoàn toàn. Làm **guided assistant** với action intents:

```text
next_best_action
explain_score
explain_gap
suggest_learning
suggest_interview_practice
explain_application_status
help_product_usage
```

---

## 8.4 Frontend Scope

Routes:

```text
/help
/help/assistant
```

UI cần có:

1. Prompt chips:
   - “What should I do next?”
   - “Why is my score low?”
   - “What should I learn first?”
   - “How should I prepare for interview?”
2. Context selector:
   - target job,
   - application,
   - latest analysis.
3. Assistant response card.
4. Linked actions:
   - open learning task,
   - start interview session,
   - view comparison,
   - open package.
5. Fallback messages.

---

## 8.5 Backend Scope

Endpoints:

```text
POST /v1/help/assistant
GET /v1/help/suggestions
```

Input:

```json
{
  "intent": "next_best_action",
  "target_job_id": "...",
  "application_id": "...",
  "analysis_job_id": "..."
}
```

Output:

```json
{
  "answer": "...",
  "based_on": ["analysis_result", "learning_tasks", "interview_feedback"],
  "recommended_actions": [],
  "limitations": []
}
```

---

## 8.6 Guardrails

Assistant chỉ trả lời dựa trên:

- current application,
- analysis result,
- interview feedback,
- cover letter/package,
- product FAQ,
- learning tasks.

Không trả lời:

- job market facts không có source,
- salary prediction,
- guarantee hiring,
- sensitive inference,
- raw private data.

Fallback:

```text
I cannot determine this from your current data.
```

---

## 8.7 Analytics Events

```text
help_assistant_opened
help_assistant_prompt_clicked
help_assistant_response_generated
help_assistant_action_clicked
help_assistant_fallback_shown
```

---

## 8.8 Acceptance Criteria

- User hỏi “Tôi nên làm gì tiếp?” và nhận câu trả lời dựa trên readiness/application.
- User hỏi “Tại sao score thấp?” và assistant trích gap từ analysis.
- Assistant có fallback rõ.
- Không trả lời ngoài phạm vi career/CV/JD/app usage.
- Không expose IDs/token/private text.

---

# 9. Phase 6E — Shareable Readiness / Recruiter-lite

## 9.1 Goal

Tạo shareable readiness package trước khi làm recruiter portal thật.

---

## 9.2 User Value

User có thể gửi link tóm tắt readiness cho mentor/reviewer/recruiter mà không lộ raw CV/JD/private evidence quá mức.

---

## 9.3 Frontend Scope

Routes:

```text
/share/[token]
/jobs/[id]/share
/applications/[id]/share
```

UI cho owner:

1. Generate share link.
2. Visibility settings:
   - summary only,
   - include score breakdown,
   - include package,
   - include cover letter,
   - include learning roadmap,
   - hide raw CV,
   - hide raw JD.
3. Expiry date.
4. Revoke link.
5. Copy link.

Public/restricted view:

1. Readiness summary.
2. Score overview.
3. Selected evidence only.
4. Package summary.
5. No private raw text by default.

---

## 9.4 Backend Scope

Endpoints:

```text
POST /v1/share-links
GET /v1/share-links
GET /v1/share-links/{id}
PATCH /v1/share-links/{id}
DELETE /v1/share-links/{id}
GET /v1/public/share/{token}
```

Data model:

```text
share_links
  id
  user_id
  target_type
  target_id
  token_hash
  visibility_json
  expires_at nullable
  revoked_at nullable
  created_at
```

Token rule:

- Store only hash.
- Do not log raw token.
- Allow revoke.
- Optional expiry.

---

## 9.5 Analytics Events

```text
share_link_created
share_link_copied
share_link_opened
share_link_revoked
share_visibility_updated
```

---

## 9.6 Acceptance Criteria

- User tạo share link.
- Người nhận xem readiness summary đã redact.
- User revoke được link.
- Link hết hạn nếu expiry set.
- Không lộ raw CV/JD/private evidence nếu chưa chọn.
- Không cần full recruiter portal.

---

# 10. Phase 6F — Usage / Plan / Credits Shell

## 10.1 Goal

Tạo usage/plan visibility mà chưa làm payment thật.

---

## 10.2 User Value

User hiểu giới hạn demo/free plan, các feature dùng bao nhiêu, và sản phẩm có cảm giác commercial-ready hơn.

---

## 10.3 Frontend Scope

Route:

```text
/usage
```

UI:

1. Current plan card.
2. Usage this month:
   - analyses,
   - interview answers,
   - cover letters,
   - application packages,
   - share links.
3. Feature limits copy.
4. Upgrade teaser disabled.
5. No checkout.

Example copy:

```text
Free demo: 5 analyses/month
Interview practice: 20 answers/month
Cover letter/package: 10 generations/month
```

---

## 10.4 Backend Scope

Endpoints:

```text
GET /v1/usage/me
GET /v1/plans
```

Optional:

```text
usage_events
  id
  user_id
  event_type
  quantity
  created_at
```

If not building enforcement yet, return computed usage from existing records.

---

## 10.5 Guardrails

- Không tạo payment fake.
- Không block core demo quá mạnh.
- Không hiển thị “paid” nếu chưa có checkout thật.
- No secret pricing logic.

---

## 10.6 Analytics Events

```text
usage_page_viewed
plan_card_viewed
upgrade_teaser_clicked
limit_warning_shown
```

---

## 10.7 Acceptance Criteria

- User thấy usage/limits rõ ràng.
- Không có checkout giả.
- Không có payment fake.
- Không block core demo flow quá mạnh.
- Có thể dùng làm slide/business model shell.

---

# 11. Phase 6G — Analytics & Product Ops

## 11.1 Goal

Vì Phase 5 đã có GA4 verification, Phase 6 cần tracking discipline và product ops để phục vụ demo/thuyết trình.

---

## 11.2 Scope

Docs/scripts:

```text
docs/phase6_analytics_event_plan.md
docs/phase6_funnel_dashboard_spec.md
docs/phase6_product_metrics_template.md
docs/phase6_demo_health_check.md
scripts/smoke_phase6_e2e.py
```

Không nhất thiết build admin dashboard thật.

---

## 11.3 Funnel cần theo dõi

```text
landing_view
signup/login
target_job_created
analysis_started
analysis_succeeded
learning_roadmap_generated
interview_session_created
share_link_created
usage_page_viewed
```

---

## 11.4 Product Metrics Template

Metrics:

1. Target jobs created.
2. Analyses per user.
3. Learning tasks generated.
4. Learning tasks completed.
5. Interview sessions created.
6. Interview answers submitted.
7. Share links created.
8. Packages generated.
9. Conversion to ready_to_apply.
10. Error rate / failed jobs.

---

## 11.5 Acceptance Criteria

- Event coverage table exists.
- Critical GA4 events are manually verified.
- Phase 6 E2E report exists.
- Demo health check script/spec exists.
- No raw CV/JD/answer text in analytics.

---

# 12. Cross-cutting Architecture

## 12.1 Proposed Routes

Frontend routes:

```text
/jobs
/jobs/new
/jobs/[id]
/jobs/[id]/compare
/jobs/[id]/learning
/jobs/[id]/interview
/learning
/learning/[id]
/interview/sessions
/interview/sessions/new
/interview/sessions/[id]
/help
/help/assistant
/share/[token]
/usage
```

---

## 12.2 Proposed Backend Areas

```text
backend/app/api/routes/target_jobs.py
backend/app/api/routes/learning.py
backend/app/api/routes/interview_sessions.py
backend/app/api/routes/help_assistant.py
backend/app/api/routes/share_links.py
backend/app/api/routes/usage.py

backend/app/services/target_jobs/
backend/app/services/learning/
backend/app/services/interview/
backend/app/services/help/
backend/app/services/share/
backend/app/services/usage/
```

---

## 12.3 Feature Flags

Nên có feature flags/env:

```text
ENABLE_PHASE6_TARGET_JOBS=true
ENABLE_PHASE6_LEARNING=true
ENABLE_PHASE6_INTERVIEW_V2=true
ENABLE_PHASE6_HELP_ASSISTANT=true
ENABLE_PHASE6_SHARE_LINKS=false initially
ENABLE_PHASE6_USAGE_SHELL=true
```

Share links nên bật sau khi privacy review.

---

## 12.4 Privacy Rules

Bắt buộc:

1. Không log raw CV text.
2. Không log raw JD text.
3. Không log interview answer text vào analytics.
4. Không log tokens/JWT/share token.
5. Share token chỉ lưu hash.
6. Share public view redact by default.
7. Help assistant không expose private IDs/token.
8. Usage metrics không chứa nội dung cá nhân.
9. Demo data phải synthetic.

---

# 13. Team Assignment

---

# 13.1 Phúc — Backend Architecture / Product Lead / Deploy

## Role

Phúc dẫn Phase 6 về architecture, API contracts, DB/migrations, backend implementation, deploy, smoke, release và PR review.

---

## Main Responsibilities

1. Phase 6 technical architecture.
2. API contracts for all modules.
3. Backend models/migrations.
4. Target Jobs backend.
5. Learning Roadmap backend.
6. Interview Session backend.
7. Help Assistant backend.
8. Shareable Readiness backend.
9. Usage shell backend.
10. Analytics event contract.
11. Feature flags.
12. Render deploy/smoke.
13. E2E closeout report.

---

## Files/Folders likely touched

```text
backend/app/api/routes/
backend/app/db/models.py
backend/app/schemas/
backend/app/services/
backend/alembic/versions/
scripts/smoke_phase6_e2e.py
scripts/smoke_test_s3.py
docs/phase6_kickoff_plan.md
docs/phase6_technical_scope.md
docs/phase6_api_contract.md
docs/phase6_acceptance_criteria.md
README.md
```

---

## Deliverables

1. `docs/phase6_api_contract.md`
2. `docs/phase6_technical_scope.md`
3. Target Jobs backend APIs.
4. Learning Roadmap APIs.
5. Interview Session APIs.
6. Help Assistant API.
7. Share Links API.
8. Usage API.
9. DB migrations.
10. Phase 6 E2E smoke script.
11. Render smoke report.

---

## Acceptance Criteria

- Backend routes are protected by user ownership.
- Old Phase 5 flows still work.
- Target job CRUD works.
- Learning roadmap generation/progress works.
- Interview sessions work.
- Help assistant returns scoped, guarded responses.
- Share link stores token hash and supports revoke.
- Usage page can fetch usage data.
- Tests pass.
- Render smoke pass.

---

## Dependencies

- Quân depends on Phúc for API contracts and data shape.
- Đạt depends on Phúc for endpoint behavior and privacy rules.
- Phúc depends on Đạt for guardrail edge cases.
- Phúc depends on Quân for integration feedback.

---

# 13.2 Quân — Frontend Product / UX Lead

## Role

Quân chịu trách nhiệm làm Phase 6 thành sản phẩm nhìn được và demo được: target jobs, learning, interview room, help assistant, share, usage và responsive polish.

---

## Main Responsibilities

1. Target Jobs UI.
2. Learning Roadmap UI.
3. Interview Room v2 UI.
4. Help Assistant UI.
5. Shareable Readiness UI.
6. Usage page.
7. Responsive/product polish.
8. GA4 walkthrough support.
9. Demo script support.

---

## Files/Folders likely touched

```text
frontend/app/jobs/
frontend/app/learning/
frontend/app/interview/
frontend/app/help/
frontend/app/share/
frontend/app/usage/
frontend/components/jobs/
frontend/components/learning/
frontend/components/interview/
frontend/components/help/
frontend/components/share/
frontend/components/usage/
frontend/lib/api.ts
frontend/lib/auth.ts
frontend/lib/analytics.ts
frontend/lib/types.ts
```

---

## Deliverables

1. `/jobs` list.
2. `/jobs/new`.
3. `/jobs/[id]`.
4. `/learning` roadmap page.
5. `/interview/sessions` and session detail.
6. `/help/assistant`.
7. `/share/[token]` public/restricted page.
8. `/usage` page.
9. Empty/loading/error states.
10. Responsive demo polish.
11. GA4 event trigger points in UI.

---

## Acceptance Criteria

- User can create/manage target jobs.
- User can view/generate learning tasks.
- User can create interview session and answer questions.
- User can use guided help assistant.
- User can create/open/revoke share link if enabled.
- User can view usage shell.
- UI handles 401/403/404/500.
- UI does not leak tokens/private data.
- UI is demo-ready and responsive.

---

## Dependencies

- Needs API contracts from Phúc.
- Needs analytics event plan from Phúc/Đạt.
- Needs guardrail wording from Đạt.
- Needs backend deployed/stable for integration.

---

# 13.3 Đạt — QA / Guardrails / Analytics / E2E Lead

## Role

Đạt chịu trách nhiệm đảm bảo Phase 6 không vỡ product quality: tests, privacy, analytics, guardrails, E2E, evaluation và demo closeout.

---

## Main Responsibilities

1. QA plan.
2. Acceptance tests.
3. Privacy/security review.
4. Guardrails for help assistant/share/interview/learning.
5. Analytics event verification.
6. E2E checklist.
7. Regression tests.
8. Demo health checklist.
9. Phase 6 closeout audit.

---

## Files/Folders likely touched

```text
backend/tests/
frontend tests if available
evaluation/cases/phase6/
docs/phase6_guardrails.md
docs/phase6_analytics_event_plan.md
docs/phase6_demo_checklist.md
docs/phase6_privacy_review.md
docs/phase6_deployed_e2e_execution_report.md
scripts/smoke_phase6_e2e.py
```

---

## Deliverables

1. `docs/phase6_guardrails.md`
2. `docs/phase6_analytics_event_plan.md`
3. `docs/phase6_privacy_review.md`
4. `docs/phase6_demo_checklist.md`
5. Phase 6 evaluation cases.
6. Backend access-control tests.
7. Analytics verification report.
8. Phase 6 E2E closeout report.

---

## Acceptance Criteria

- No cross-user access leaks.
- No raw CV/JD/interview answer in analytics.
- Share public view is redacted by default.
- Help assistant has scoped fallback.
- Learning tasks do not claim user has missing skills.
- Interview feedback does not overclaim.
- Usage shell does not fake payment.
- GA4 critical events verified.
- E2E report PASS.

---

## Dependencies

- Needs Phúc endpoints to test.
- Needs Quân UI to verify events.
- Needs team to provide demo data and routes.

---

# 14. Week-by-week Milestones

## Week 1 — Planning + Target Jobs Foundation

### Phúc
- Create planning docs/contracts.
- Implement target jobs backend.
- Decide reuse `applications` vs `target_jobs`.
- Add migrations if needed.
- Add ownership tests base.

### Quân
- Build `/jobs`, `/jobs/new`, `/jobs/[id]`.
- Create job status/filter UI.
- Add readiness/package links.

### Đạt
- Create Phase 6 QA plan.
- Target job access tests.
- Analytics event table draft.
- Privacy review draft.

### Week 1 Done When

- Target job CRUD works locally.
- User can create/list/update target jobs in UI.
- Ownership tests pass.
- Contract docs exist.

---

## Week 2 — Learning Roadmap + Interview v2

### Phúc
- Implement learning tasks backend.
- Implement interview sessions backend.
- Add progress/status endpoints.
- Add rubric summary endpoint.

### Quân
- Build learning roadmap UI.
- Build interview session UI.
- Implement answer submit/retry flow.

### Đạt
- Learning guardrail tests.
- Interview feedback tests.
- Evaluation cases for roadmap/interview.
- Manual QA for core flows.

### Week 2 Done When

- User can generate/update learning tasks.
- User can create interview session.
- User can submit answer and see feedback.
- Tests/evaluation cover core risks.

---

## Week 3 — Help Assistant + Shareable Readiness

### Phúc
- Implement guided help assistant.
- Implement share link backend behind feature flag.
- Store token hash only.
- Add revoke/expiry support.

### Quân
- Build help assistant page.
- Build share link owner UI.
- Build public share page.
- Add redacted view states.

### Đạt
- Help assistant guardrail cases.
- Share link privacy tests.
- Public view redaction review.
- GA4 event verification start.

### Week 3 Done When

- Help assistant answers scoped intents.
- Share link can be created/revoked.
- Public view redacts private data by default.
- Guardrail tests pass.

---

## Week 4 — Usage Shell + Analytics + E2E Closeout

### Phúc
- Implement usage endpoint.
- Add Phase 6 E2E smoke.
- Deploy/stabilize Render.
- Write backend closeout notes.

### Quân
- Build `/usage`.
- Final polish across Phase 6 routes.
- Add loading/error/empty states.
- Support demo script screenshots.

### Đạt
- Verify GA4 events.
- Run E2E checklist.
- Write deployed E2E report.
- Final privacy/security review.
- Phase 6 closeout audit.

### Week 4 Done When

- Usage shell visible.
- Critical GA4 events verified.
- Deployed E2E PASS.
- Demo script ready.
- Team sign-off complete.

---

# 15. PR Sequence

```text
PR 66 — docs: add Phase 6 kickoff plan
PR 67 — feat: add target jobs workspace
PR 68 — feat: expand learning roadmap
PR 69 — feat: add interview practice sessions v2
PR 70 — feat: add guided help assistant
PR 71 — feat: add shareable readiness package
PR 72 — feat: add usage and plan shell
PR 73 — docs/test: add Phase 6 analytics and E2E closeout
```

---

## 15.1 PR 66 — Phase 6 Planning Docs

Owner: Phúc  
Type: docs only

Files:

```text
docs/phase6_kickoff_plan.md
docs/phase6_team_plan.md
docs/phase6_technical_scope.md
docs/phase6_acceptance_criteria.md
```

Acceptance:

- No code.
- No migrations.
- Privacy grep clean.
- Team plan clear.

---

## 15.2 PR 67 — Target Jobs Workspace

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Target job APIs.
- Target job UI.
- Status/filter.
- Attach analysis.
- Ownership tests.

---

## 15.3 PR 68 — Learning Roadmap v2

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Learning task generation.
- Task progress.
- Learning UI.
- Analytics events.
- Guardrails/tests.

---

## 15.4 PR 69 — Interview Practice v2

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Interview sessions.
- Question types/difficulty.
- Answer retry.
- Rubric detail.
- Session history.
- Export summary if time.

---

## 15.5 PR 70 — Help Assistant

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Guided assistant intents.
- Help UI.
- Guardrails.
- Fallbacks.
- Analytics events.

---

## 15.6 PR 71 — Shareable Readiness

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Share links.
- Redacted public view.
- Revoke/expiry.
- Privacy tests.
- Feature flag initially.

---

## 15.7 PR 72 — Usage / Plan Shell

Owner: Phúc + Quân  
QA: Đạt

Scope:

- Usage endpoint.
- Usage page.
- Plan cards.
- No payment.
- Analytics.

---

## 15.8 PR 73 — Phase 6 Closeout

Owner: Đạt + Phúc + Quân

Scope:

- GA4 verification.
- E2E report.
- Privacy review.
- Demo health check.
- Docs/readme update.
- Team sign-off.

---

# 16. Definition of Done

Phase 6 complete khi:

## Product Gates

1. Target job workspace hoạt động trên deployed app.
2. User có thể create/edit/filter target jobs.
3. User có thể attach analysis vào target job.
4. Learning roadmap sinh task từ gaps.
5. User update learning progress.
6. Interview session history hoạt động.
7. User submit/retry answer và xem rubric.
8. Help assistant/guided help hoạt động với guardrails.
9. Shareable readiness hoạt động hoặc được explicitly deferred bằng docs.
10. Usage shell visible hoặc explicitly deferred bằng docs.

## Technical Gates

1. Backend tests pass.
2. Frontend build/lint pass nếu có.
3. Local smoke pass.
4. Render smoke pass.
5. No old Phase 5 flow broken.
6. Migrations tested before deploy.
7. Feature flags documented.

## Privacy Gates

1. No secrets/tokens/JWT in docs/logs.
2. No raw CV/JD/answer text in analytics.
3. Share tokens stored hashed.
4. Share view redacted by default.
5. Cross-user access tests pass.

## Analytics Gates

1. GA4 critical events listed.
2. Event coverage table complete.
3. Happy-path events verified.
4. Negative-path/error events documented.
5. Funnel dashboard spec exists.

## Demo Gates

1. Demo data ready.
2. Demo script ready.
3. Demo health check pass.
4. Deployed E2E report PASS.
5. Phúc/Quân/Đạt sign-off Done.

---

# 17. Phase 6 Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Scope quá rộng | Trễ demo | PR theo module, feature flags |
| Share link privacy leak | Rất cao | Redact default, token hash, revoke, Đạt test kỹ |
| Help assistant trả lời bừa | Mất trust | Guided intents, scoped context, fallback |
| Learning roadmap fake personalization | Sai product | Dựa vào analysis/profile; fallback rõ |
| Interview feedback overclaim | User hiểu sai | Rubric + caveat + evidence references |
| Payment shell gây hiểu nhầm | Demo risk | No checkout, no fake paid plan |
| Frontend quá nhiều route | Quân quá tải | Prioritize /jobs, /learning, /interview, /help |
| Backend migration phức tạp | Deploy lỗi | Reuse existing applications where possible |
| GA4 event overload | Rối QA | Critical events first |
| Render instability | Demo lỗi | Smoke early after each major PR |

---

# 18. Immediate Next Actions

1. Phúc tạo PR 66 docs/planning.
2. Team review Phase 6 scope.
3. Sau khi PR 66 merge, code đầu tiên là **Phase 6A — Target Jobs / Saved JD Workspace**.
4. Không nhảy thẳng vào payment/chatbot/recruiter portal.
5. Shareable readiness phải có feature flag và privacy review trước khi public.

---

# 19. Recommended Branches

```bash
git checkout -b docs/phase6-kickoff-plan
git checkout -b phase6/phuc-target-jobs-backend
git checkout -b phase6/quan-target-jobs-ui
git checkout -b phase6/dat-phase6-qa-analytics
```

---

# 20. Final Recommendation

Phase 6 nên làm nhiều việc, nhưng thứ tự phải rõ:

```text
Target Jobs first
Learning + Interview second
Help Assistant third
Shareable Readiness fourth
Usage + Analytics closeout last
```

Nếu thời gian demo quá gấp, ưu tiên:

```text
/jobs
/learning
/interview/sessions
/help
/usage
```

Shareable readiness có thể bật sau bằng feature flag nếu privacy review chưa xong.
