# AI CV Fit App — Phase 3 Team Plan

**Ngày lập:** 2026-06-03  
**Team:** Phúc — Quân — Đạt  
**Trạng thái đầu vào:** Phase 2 đã hoàn thành, đã qua review/audit.  
**Mục tiêu Phase 3:** nâng sản phẩm từ “MVP có frontend/auth/history” thành một hệ thống **đáng tin hơn, giải thích được hơn, có evidence rõ hơn và demo thuyết phục hơn**.

---

## 1. Tư duy chính của Phase 3

Phase 1 chủ yếu là **deployable baseline**.  
Phase 2 chủ yếu là **frontend + auth + product flow**.  
Phase 3 nên tập trung vào:

> **Scoring Quality & Explainability**

Tức là không chỉ trả một con số `fit_score`, mà phải trả lời được:

1. Vì sao CV này được điểm như vậy?
2. Skill nào match với JD?
3. Skill nào thiếu?
4. Evidence nằm ở dòng/bullet nào trong CV?
5. JD yêu cầu phần nào?
6. User nên sửa CV thế nào mà không bịa kinh nghiệm?
7. Report có đủ rõ để user tin và làm theo không?
8. Hệ thống có thể được test bằng bộ CV/JD mẫu không?

---

## 2. Phase 3 Product Direction

Phase 3 định vị AI CV Fit App theo hướng:

> **Evidence-based Career Readiness Analyzer**

Không chỉ là “CV-JD keyword checker”, mà là hệ thống đánh giá mức độ sẵn sàng ứng tuyển dựa trên:

- CV-JD Fit Score.
- Skill coverage.
- Experience/project relevance.
- Evidence from CV.
- Missing evidence.
- Improvement actions.
- Report giải thích được.
- Regression/evaluation set để kiểm tra chất lượng.

---

## 3. Phase 3 Goals

## Goal 1 — Explainable Scoring

Mỗi điểm số cần có breakdown:

```text
Overall Fit Score
Skill Match Score
Experience Match Score
Responsibility Match Score
Project Relevance Score
CV Quality Score
```

Mỗi score cần có:

- lý do,
- evidence,
- confidence,
- limitation nếu có.

---

## Goal 2 — Evidence-based Feedback

Mỗi nhận xét quan trọng cần có evidence:

```text
JD yêu cầu: FastAPI, PostgreSQL, Docker
CV tìm thấy: PostgreSQL, Docker
Missing: FastAPI
Evidence: bullet số 3 trong project Backend API
```

Không nên chỉ nói:

```text
Bạn thiếu FastAPI.
```

Mà nên nói:

```text
JD yêu cầu FastAPI, nhưng hệ thống chưa tìm thấy bằng chứng rõ ràng trong CV. Nếu bạn thật sự có kinh nghiệm FastAPI, hãy thêm vào project/backend bullet cụ thể.
```

---

## Goal 3 — Result Dashboard v2

Frontend cần hiển thị result có cấu trúc tốt hơn:

- Score overview.
- Score breakdown.
- Matched skills.
- Missing skills.
- Evidence cards.
- Top improvement actions.
- Report download.
- Optional: compare before/after if user re-analyzes.

---

## Goal 4 — Report DOCX v2

Report cần chuyên nghiệp hơn:

- Executive summary.
- Score breakdown table.
- Strengths.
- Gaps.
- Evidence.
- Suggested edits.
- Next action roadmap.

---

## Goal 5 — Evaluation Set & Quality Gates

Cần có bộ test CV/JD mẫu để tránh scoring “ảo”:

- 5 easy cases.
- 5 medium cases.
- 5 hard cases.
- 3 edge cases:
  - CV rất ngắn.
  - JD quá dài.
  - CV không liên quan JD.
- Expected behavior cho từng case.

Mục tiêu không phải perfect score, mà là output hợp lý, nhất quán, không hallucinate.

---

## 4. Phase 3 Must-have

Phase 3 bắt buộc hoàn thành các việc sau:

1. Chuẩn hóa schema result JSON v2.
2. Thêm score breakdown rõ ràng.
3. Thêm evidence mapping CV/JD.
4. Thêm missing skill explanation.
5. Thêm top improvement actions.
6. Cập nhật frontend result dashboard v2.
7. Cập nhật DOCX report v2.
8. Tạo evaluation dataset CV/JD mẫu.
9. Thêm tests cho scoring/evidence.
10. Đảm bảo Render smoke test vẫn pass.
11. Không làm vỡ auth/history flow từ Phase 2.
12. Không bịa kinh nghiệm trong suggestions.

---

## 5. Phase 3 Should-have

Nếu còn thời gian:

1. Role Readiness Score.
2. Confidence score cho từng match.
3. Compare result giữa các lần phân tích.
4. Report preview trên frontend.
5. Better parsing cho CV sections:
   - Skills
   - Projects
   - Experience
   - Education
6. Export result JSON for debugging.
7. Admin/debug mode nội bộ để xem raw parse/scoring.

---

## 6. Phase 3 Could-have

Nếu dư thời gian:

1. Interview question generator v1.
2. Cover letter draft v1.
3. CV bullet rewrite assistant v1.
4. Learning roadmap dựa trên missing skills.
5. Email report to user.

Những phần này chỉ nên làm nếu **guardrails và evidence** đã đủ tốt.

---

## 7. Not in Phase 3

Không nên làm trong Phase 3:

1. Payment/subscription.
2. Recruiter dashboard lớn.
3. Multi-tenant organizations.
4. Full AI interview engine.
5. Job board crawling.
6. Complex LLM rewrite không có evidence.
7. Mobile app.
8. Browser extension.

---

# 8. Result JSON v2 — Đề xuất Contract

Phase 3 nên chuẩn hóa output thành dạng gần như sau:

```json
{
  "overall": {
    "fit_score": 75.9,
    "fit_level": "good",
    "summary": "CV matches many backend requirements but lacks clear FastAPI evidence."
  },
  "score_breakdown": {
    "skill_match": 82,
    "experience_match": 70,
    "responsibility_match": 76,
    "project_relevance": 78,
    "cv_quality": 72
  },
  "matched_skills": [
    {
      "skill": "PostgreSQL",
      "required_by_jd": true,
      "evidence": [
        {
          "source": "cv",
          "text": "Built PostgreSQL-backed job tracking API",
          "section": "Projects"
        }
      ],
      "confidence": 0.91
    }
  ],
  "missing_skills": [
    {
      "skill": "FastAPI",
      "reason": "JD mentions FastAPI but no clear evidence was found in CV.",
      "suggestion": "If you have FastAPI experience, add a project bullet describing the API endpoint or backend service you built."
    }
  ],
  "improvement_actions": [
    {
      "priority": "high",
      "title": "Add clearer backend API evidence",
      "description": "The JD expects backend API experience. Add concrete API project bullets with framework, database and deployment details.",
      "safe_rewrite_note": "Only add FastAPI if you have actually used it."
    }
  ],
  "limitations": [
    "This analysis is an estimate and does not guarantee hiring outcomes."
  ]
}
```

---

# 9. Team Assignment

---

# 9.1 Phúc — Scoring / Backend / Product Lead

## Vai trò

Phúc chịu trách nhiệm chính về scoring v2, API contract, backend schema, integration và kiểm soát chất lượng sản phẩm.

## Nhiệm vụ chính

### A. Result JSON v2 Contract

Tạo hoặc cập nhật:

```text
docs/result_schema_v2.md
```

Nội dung cần có:

- Overall fit.
- Score breakdown.
- Matched skills.
- Missing skills.
- Evidence.
- Improvement actions.
- Limitations.
- Backward compatibility note.

### B. Backend Scoring v2

Cập nhật scoring service để trả thêm:

1. `score_breakdown`
2. `matched_skills`
3. `missing_skills`
4. `evidence`
5. `improvement_actions`
6. `limitations`

Không cần thay toàn bộ scoring algorithm ngay. Có thể bọc quanh logic hiện tại để enrich output.

### C. Evidence Mapping

Cần xác định:

- skill match đến từ dòng nào trong CV,
- JD yêu cầu skill ở đoạn nào,
- confidence của match,
- nếu không có evidence thì ghi missing evidence.

### D. API Compatibility

Đảm bảo frontend mới nhận result v2 được.

Nếu cần giữ compatibility:

```text
result.fit_score vẫn tồn tại
result.overall.fit_score cũng có
```

### E. Render/Smoke

Sau khi scoring v2 merge:

- chạy local tests,
- chạy local smoke,
- deploy Render nếu cần,
- chạy smoke test Render.

## Deliverables của Phúc

- `docs/result_schema_v2.md`
- Backend result JSON v2.
- Evidence mapping basic.
- Improvement actions basic.
- Limitations wording.
- API contract update.
- Smoke test pass.

## Definition of Done

- Frontend có thể render result v2.
- Old smoke scripts không vỡ hoặc được update hợp lý.
- Result có score breakdown.
- Result có matched/missing skills.
- Result có evidence hoặc explanation rõ.
- Không bịa skill/experience.
- Tests pass.

---

# 9.2 Quân — Frontend Result Dashboard v2

## Vai trò

Quân chịu trách nhiệm biến result v2 thành UI dễ hiểu, thuyết phục và demo tốt.

## Nhiệm vụ chính

### A. Result Dashboard v2

Cần hiển thị:

1. Overall score lớn, dễ nhìn.
2. Fit level:
   - excellent
   - good
   - partial
   - weak
3. Score breakdown cards:
   - skill match,
   - experience match,
   - responsibility match,
   - project relevance,
   - CV quality.
4. Matched skills section.
5. Missing skills section.
6. Evidence cards.
7. Top improvement actions.
8. Download report button.
9. Limitations/disclaimer.

### B. UX Flow

Result page nên có flow:

```text
Score summary
→ Why this score?
→ Matched evidence
→ Missing skills
→ What to improve next?
→ Download report
```

### C. Empty/Error States

Cần xử lý:

- không có matched skills,
- không có evidence,
- job failed,
- token invalid,
- report missing,
- backend trả result v1/v2 khác nhau.

### D. Visual Clarity

Không cần quá cầu kỳ, nhưng cần rõ:

- user biết mình mạnh ở đâu,
- thiếu gì,
- hành động tiếp theo là gì.

## Deliverables của Quân

- Result dashboard v2.
- Components:
  - ScoreSummary
  - ScoreBreakdown
  - MatchedSkills
  - MissingSkills
  - EvidenceCard
  - ImprovementActions
  - ReportDownloadButton
- Error/empty states.
- Responsive layout.

## Definition of Done

- Result không còn cảm giác JSON thô.
- User hiểu vì sao mình được điểm đó.
- User thấy được top actions.
- Download report vẫn hoạt động.
- Auth/history flow không vỡ.
- Frontend không log token.

---

# 9.3 Đạt — Evaluation / Tests / Guardrails Owner

## Vai trò

Đạt chịu trách nhiệm tạo bộ đánh giá chất lượng, test scoring/evidence và kiểm tra guardrails.

## Nhiệm vụ chính

### A. Evaluation Dataset

Tạo folder:

```text
evaluation/
  cases/
    easy/
    medium/
    hard/
    edge/
```

Mỗi case gồm:

```text
cv_text.txt
jd_text.txt
expected_behavior.md
```

Tối thiểu:

- 5 easy cases.
- 5 medium cases.
- 5 hard cases.
- 3 edge cases.

### B. Evaluation Script

Tạo script:

```text
scripts/evaluate_scoring_cases.py
```

Script nên:

1. Load CV/JD cases.
2. Chạy parser/scorer.
3. Xuất kết quả summary.
4. Không cần strict numeric assertion quá sớm.
5. Check các rule:
   - CV không liên quan thì score không được cao.
   - Missing skill phải xuất hiện.
   - Evidence không được rỗng nếu match skill.
   - Không có câu “guarantee hired”.

### C. Tests

Thêm tests cho:

1. Result schema v2 có field bắt buộc.
2. Missing skills explanation.
3. Improvement actions không bịa.
4. Evidence mapping tồn tại.
5. Low-fit case không score quá cao.
6. Token/auth flow không bị vỡ.
7. Report v2 generation không lỗi.

### D. Guardrails v1.5

Cập nhật hoặc tạo:

```text
docs/guardrails_v1_5.md
```

Nội dung:

- Không guarantee tuyển dụng.
- Không bịa skill.
- Không bịa experience.
- Evidence vs suggestion phải phân biệt rõ.
- Nếu thiếu evidence, nói thiếu evidence.
- Rewrite phải conditional: “nếu bạn thật sự có kinh nghiệm...”.

## Deliverables của Đạt

- Evaluation dataset.
- Evaluation script.
- Scoring/evidence tests.
- Guardrails v1.5 docs.
- Test report summary.

## Definition of Done

- Có ít nhất 18 evaluation cases.
- Script chạy được.
- Có test cho result schema/evidence.
- Guardrails wording rõ.
- Không có output quá tự tin hoặc bịa kinh nghiệm.

---

# 10. Report DOCX v2

Phase 3 nên nâng cấp report DOCX.

## Sections đề xuất

1. Cover / Title.
2. Executive summary.
3. Overall fit score.
4. Score breakdown table.
5. Matched skills.
6. Missing skills.
7. Evidence highlights.
8. Improvement actions.
9. Limitations.
10. Generated timestamp.

## Owner

- Phúc: backend data/report structure.
- Quân: góp ý layout/UX nội dung.
- Đạt: test report generation và wording guardrails.

---

# 11. Phase 3 Timeline đề xuất

## Day 1 — Contract & Dataset

### Phúc
- Tạo `docs/result_schema_v2.md`.
- Thiết kế result JSON v2.
- Review scoring hiện tại.

### Quân
- Thiết kế UI result dashboard v2.
- Tạo component skeleton.

### Đạt
- Tạo evaluation folder.
- Viết 5 easy cases.

---

## Day 2 — Backend Result v2

### Phúc
- Implement score breakdown.
- Implement matched/missing skill structure.
- Implement basic evidence mapping.

### Quân
- Render score summary + breakdown cards.

### Đạt
- Thêm medium/hard cases.
- Bắt đầu evaluation script.

---

## Day 3 — Evidence & Actions

### Phúc
- Add improvement actions.
- Add limitations.
- Update API contract.

### Quân
- Render matched skills, missing skills, evidence cards.
- Error/empty states.

### Đạt
- Tests cho schema/evidence/missing skills.
- Guardrails docs.

---

## Day 4 — Report v2

### Phúc
- Update DOCX report v2 generation.
- Keep report download compatible.

### Quân
- Polish dashboard UX.
- Align dashboard content with report sections.

### Đạt
- Test report generation.
- Run evaluation cases.

---

## Day 5 — Integration & Smoke

### Cả team
- Merge PRs.
- Run tests.
- Run local smoke.
- Deploy Render if needed.
- Run Render smoke.
- Update README/docs.
- Prepare demo script.

---

# 12. Integration Rules

1. Không đổi result API contract mà không update `docs/result_schema_v2.md`.
2. Không merge dashboard frontend nếu backend result v2 chưa ổn.
3. Không xóa support cho result v1 nếu frontend đang cần fallback.
4. Không thêm LLM rewrite nếu guardrails chưa có.
5. Không để score cao cho CV không liên quan JD.
6. Không output câu guarantee tuyển dụng.
7. Không log CV raw text/token/JWT.
8. Smoke test phải pass sau merge lớn.
9. Evaluation cases phải chạy trước Phase 3 closeout.

---

# 13. Phase 3 Definition of Done

Phase 3 hoàn thành khi:

1. Result JSON v2 có contract rõ.
2. Backend trả score breakdown.
3. Backend trả matched skills.
4. Backend trả missing skills.
5. Backend trả evidence/explanation.
6. Backend trả improvement actions.
7. Frontend dashboard v2 hiển thị result rõ.
8. DOCX report v2 có score breakdown và actions.
9. Có evaluation dataset tối thiểu 18 cases.
10. Có evaluation script chạy được.
11. Guardrails v1.5 có.
12. Tests pass.
13. Local smoke pass.
14. Render smoke pass.
15. README/docs cập nhật.
16. Demo cho thấy sản phẩm đáng tin hơn keyword checker đơn giản.

---

# 14. Immediate Next Actions

1. Phúc tạo branch:
   ```bash
   phase3/phuc-result-v2-backend
   ```
2. Quân tạo branch:
   ```bash
   phase3/quan-result-dashboard-v2
   ```
3. Đạt tạo branch:
   ```bash
   phase3/dat-evaluation-guardrails
   ```
4. Phúc tạo `docs/result_schema_v2.md` trước để Quân và Đạt bám theo.
5. Đạt bắt đầu evaluation dataset song song.
6. Quân dựng dashboard component skeleton dựa trên schema v2.
7. Merge theo thứ tự:
   - result schema v2 docs,
   - backend result v2,
   - evaluation tests,
   - frontend dashboard,
   - report v2,
   - final smoke/release.
