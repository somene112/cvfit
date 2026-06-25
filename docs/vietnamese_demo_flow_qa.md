# Vietnamese-First Demo Flow — QA Guide

This document describes the Vietnamese-first demo path, the expected on-screen
language, how to switch language, and what is intentionally out of scope.

It covers the work added on top of **PR #86** (Quân's frontend Vietnamese pass).

---

## Relation to PR #86

**PR #86 (merged) already delivered the bulk of the frontend Vietnamese UI:**

- `LanguageContext` is hard-set to Vietnamese (`lang = 'vi'`); the app is
  Vietnamese-only and Vietnamese is the default for every new session.
- All static UI strings, navigation labels, buttons, empty/loading/error states,
  and billing/usage/pricing copy across the demo pages are Vietnamese.

**This PR completes the remaining gaps:**

1. **Admin Monitoring page** (`/admin`) — new, Vietnamese-native.
2. **Backend-generated content** now responds in Vietnamese when the caller
   requests `language=vi` (previously English-only). Wired for the cover letter,
   application package, and interview-session feedback; the help assistant and
   summary endpoints also support it.
3. **Navigation** gains a **Quản trị** (Admin) link, shown only to admins.

---

## How to switch VI / EN

- The UI is **Vietnamese-only** by design (PR #86 hard-set `lang = 'vi'` and made
  the toggle a no-op). New sessions are Vietnamese with no action required.
- Backend generation is **bilingual** and defaults to English for backward
  compatibility. The Vietnamese-first frontend service layer requests `vi`
  explicitly, so generated artifacts come back Vietnamese in the demo.
- To force a specific language at the API level, pass `language=vi` or
  `language=en`:
  - Cover letter: `POST /v1/applications/{id}/cover-letter/generate?language=vi`
  - Package: `POST /v1/applications/{id}/package/generate?language=vi`
  - Interview answer: body `{ "question_id": "...", "answer_text": "...", "language": "vi" }`
  - Interview questions: body `{ "count": 5, "language": "vi" }`
  - Interview summary: `GET /v1/interview/sessions/{id}/summary?language=vi`
  - Help assistant: body `{ "intent": "...", "language": "vi" }`
  - Anything not recognizably Vietnamese resolves to English.

---

## Exact demo path (Vietnamese-first)

1. **Đăng nhập** — Login page (Vietnamese).
2. **Phân tích CV** — Dashboard: upload CV + paste mô tả công việc (JD), run analysis.
3. **Lịch sử / Kết quả** — History + result view (Vietnamese labels, scores).
4. **Phỏng vấn** — Interview practice (`/interview/sessions`):
   - Generated questions are Vietnamese when requested with `language=vi`.
   - Answer feedback (strengths/improvements/risk flags/disclaimer) is Vietnamese.
5. **Hồ sơ ứng tuyển** — Applications → **Thư xin việc** (cover letter) and
   **Bộ hồ sơ** (package): generated drafts are Vietnamese.
6. **Mức sử dụng / Thanh toán / Bảng giá** — Usage, billing, pricing (Vietnamese).
7. **Trợ giúp** — Help page (Vietnamese).
8. **Quản trị** — Admin page (admins only), fully Vietnamese.

---

## Expected Vietnamese navigation labels

| Route                | Label (VI)          |
| -------------------- | ------------------- |
| `/dashboard`         | Phân tích CV        |
| `/history`           | Lịch sử             |
| `/applications`      | Hồ sơ ứng tuyển     |
| `/jobs`              | Việc làm            |
| `/interview/sessions`| Phỏng vấn           |
| `/profile`           | Hồ sơ năng lực      |
| `/learning`          | Học tập             |
| `/usage`             | Mức sử dụng         |
| `/help`              | Trợ giúp            |
| `/admin`             | Quản trị            |
| (logout)             | Đăng xuất           |

> Note: "Thanh toán" (billing) is reached via **Mức sử dụng** → it is not a
> separate top-level nav item (unchanged from PR #86).

---

## Expected generated-content language (VI mode)

- **Cover letter**: opening, why-role/company, contribution/fit, closing,
  review notes, missing-evidence notes, and disclaimer are Vietnamese.
- **Application package**: readiness summary, next actions, evidence-checklist
  notes, and disclaimer are Vietnamese.
- **Interview questions**: fallback questions and evidence-derived questions are
  Vietnamese; the rubric labels and limitations are Vietnamese.
- **Interview feedback**: strengths, improvements, risk flags, and disclaimer
  are Vietnamese.
- **Help assistant**: answer, limitations, and suggestion labels are Vietnamese.

---

## Allowed English / untranslated terms

These are intentionally left as-is (proper nouns / technical terms / user data):

- **CV**, **AI**
- **JD** — acceptable where already used, though **"mô tả công việc"** is preferred
  and is used in new copy.
- Technology names: **Python, SQL, Git, TensorFlow, PyTorch**, etc.
- **Company names** and **job titles** (user-provided).
- **User content**: raw CV text, JD text, and the user's own interview answers
  are never translated.
- Machine-readable identifiers (intent keys, `recommended_actions`, status enums)
  are not translated.

---

## Out of scope (known remaining)

- **Full app-wide translation** of every secondary page is not part of this PR.
- **Historical generated artifacts** created in English are left unchanged; only
  newly generated content honors `language=vi`.
- The interview/package/help contract mismatches and the cover-letter save issue
  noted in earlier revisions are **now fixed** — see "Priority 2 Demo Hardening"
  below.
- **Legacy Phase 5 interview practice** and **learning roadmap** generated text
  are not yet localized (the demo uses the Phase 6 interview sessions flow).

---

## Switching the language contract back to English (regression check)

Because the backend defaults to English, omitting `language` (or sending
`language=en`) reproduces the exact prior English output. This is covered by
existing tests (`test_phase5_package_cover_letter.py`,
`test_phase6_interview_sessions.py`, `test_phase6_help_assistant.py`) plus the
new `test_vietnamese_generation.py`, which asserts both the Vietnamese output and
the unchanged English default.

---

## Admin Analytics v2 — demo script

The `/admin` dashboard (admins only) now shows database-derived product-usage
metrics, not just raw counts. All numbers come from aggregate PostgreSQL queries
— no private content, no GA4.

**Why internal DB metrics (not GA4):**

> "GA4 mới được gắn nên chưa phản ánh toàn bộ lịch sử truy cập. Vì vậy dashboard
> quản trị dùng dữ liệu nội bộ từ PostgreSQL để đo mức sử dụng thực tế của sản
> phẩm: người dùng, lượt phân tích CV, hồ sơ ứng tuyển, phiên phỏng vấn và
> trạng thái vận hành."

**Demo steps:**

1. **Open `/admin`** (set `ADMIN_EMAILS` to your account email in backend env first).
2. **Tổng quan sử dụng sản phẩm** — total users, users who ran a CV analysis,
   total analyses, analysis success rate, applications, interview sessions, and
   latest activity time.
3. **Phễu sử dụng** — Người dùng → Đã phân tích CV → Tạo hồ sơ ứng tuyển →
   Luyện phỏng vấn, with conversion percentages between steps.
4. **Hoạt động 7 ngày / 30 ngày** — new users / analyses / applications /
   interview sessions created in each window.
5. **Độ sâu sử dụng** — averages per user (analyses, applications, interview
   sessions) and answers per session.
6. **Thanh toán** — when `ENABLE_BILLING=false`, a neutral **"Chưa bật"** badge +
   "Thanh toán chưa được mở cho người dùng thật." Orders/revenue are shown only
   as secondary operational metrics (0đ is **not** a top-line KPI). When billing
   is enabled, revenue/orders are shown as normal cards.
7. **Trạng thái tính năng** — Billing / Credit gating / Share links bật/tắt.

**Privacy/safety:** the overview is aggregate-only (counts, percentages, status
breakdowns, timestamps). No emails, raw CV/JD/answers, cover letters, package
content, checkout URLs, signatures, webhook payloads, or secrets. Read-only — no
admin mutation endpoints. Percentages/averages return `—` (not a fake 0) when the
denominator is zero.

**Out of scope:** GA4 historical reconstruction, payment rollout, real payments,
admin mutations, and full enterprise analytics (charts/cohorts/retention curves).

---

## Priority 2 Demo Hardening

Demo-blocking frontend/backend contract bugs fixed in `fix/demo-flow-priority-2`
(backend response contracts unchanged — the frontend adapts via normalizers):

- **Interview session detail** now renders correctly. The page consumed `q.text`
  / `feedback.overall_score`, but the backend returns `question_text` and a
  `score` (0-5) + `feedback` object. A normalizer in `interviewSessionsApi.js`
  maps `question_text → text`, flattens `score`/`feedback` (strengths → summary,
  improvements → suggestions), and scales the rubric 0-5 → 0-10. New sessions
  also auto-generate questions in Vietnamese on first open, since `create` did
  not previously generate any.
- **Application package** now renders the readiness summary. The page read
  `payload.summary`; the backend nests it under `payload.readiness_summary.*`.
  The page now reads `readiness_summary.{summary,fit_score,readiness_level,
  next_actions}` and formats the fit score safely (handles 0-1 and 0-100).
- **Help page** now calls the real endpoints. `helpApi` previously POSTed to a
  non-existent `/v1/help/ask`. It now uses `GET /v1/help/suggestions?language=vi`
  and `POST /v1/help/assistant` with a supported `intent`. The assistant page is
  suggestion/intent-based: Vietnamese suggestion chips, safe owned-object context
  only (never raw CV/JD/answer text), and renders answer + "Dựa trên" +
  limitations + fallback badge + recommended-action links. No LLM/external call.
- **Cover letter "Save Changes"** persists. The save handler + PATCH endpoint were
  already wired, free, and ungated; the backend now uses the canonical
  `flag_modified(artifact, "payload_json")` JSONB pattern to guarantee the edit is
  flushed. Editing the existing draft is owner-scoped, consumes **no** credits, is
  never blocked by credit gating, and creates no new artifact. Covered by
  `test_cover_letter_save_edits.py`.

**Still out of scope:** legacy Phase 5 interview practice + learning roadmap
localization; persisting prior interview answers across reloads (answers show
live in-session).
