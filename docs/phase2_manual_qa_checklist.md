# Phase 2 Manual QA Checklist — AI CV Fit

**Ngày:** Sau khi Quân hoàn thành frontend Phase 2
**Người thực hiện:** Đạt (Backend Quality Owner)
**Mục tiêu:** Manual test toàn bộ flow sau khi frontend Phase 2 hoàn thành

---

## Trước Khi Bắt Đầu

### Environment Setup

```powershell
# Backend URL
$API_BASE_URL = "https://cvfit.onrender.com"

# Hoặc local
# $API_BASE_URL = "http://localhost:8000"

# Test credentials
$TEST_EMAIL = "phuc_test@example.com"
$TEST_PASSWORD = "TestPassword123!"
$TEST_NAME = "Test User"

# Browser DevTools
# 1. Open DevTools (F12)
# 2. Mở tab Console
# 3. Mở tab Network
```

### Pre-flight Checks

```
□ Backend health check: curl.exe -i "$API_BASE_URL/health"
□ Database connection OK
□ Redis connection OK
□ S3 storage accessible
□ Worker đang chạy
□ Không có error logs gần đây trên Render
```

---

## PHẦN 1: Guest Flow Test (Không Login)

### 1.1 Trang Chủ

```
□ Trang chủ load được
□ Không có error trong Console (Error level)
□ Không có access_token trong Console
□ Layout hiển thị đúng
□ Images/CSS/JS load đúng
□ Mobile responsive (nếu applicable)
```

### 1.2 Upload CV

```
□ Upload button hiển thị
□ Click upload → file picker mở ra
□ Chọn file PDF hợp lệ → preview hiển thị filename
□ Chọn file DOCX hợp lệ → preview hiển thị filename
□ Upload file không hợp lệ (exe, txt, jpg) → error message hiển thị
□ Upload file quá lớn (>10MB) → error message hiển thị
□ Upload file rỗng → error message hiển thị
□ Xóa file đã chọn → upload box về trạng thái ban đầu
```

### 1.3 Job Description Input

```
□ Textarea hiển thị placeholder
□ Paste JD text ngắn (< 30 chars) → validation message
□ Paste JD text đủ (> 30 chars) → validation pass
□ Textarea resize được
□ Clear button hoạt động
```

### 1.4 Analyze Flow

```
□ Chưa upload CV → Analyze button disabled hoặc error message
□ Chưa paste JD → Analyze button disabled hoặc error message
□ Đủ điều kiện → Analyze button enabled

□ Click Analyze → loading state hiển thị
□ Progress bar hiển thị và di chuyển
□ Status message hiển thị step hiện tại

□ Job tạo thành công → polled status thay đổi
□ Job queued → running → succeeded
□ Job failed → error message hiển thị rõ ràng

□ Job timeout → thông báo "Analysis is taking longer than expected"
□ Cancel button hoạt động (nếu có)
```

### 1.5 Result Dashboard

```
□ Result dashboard hiển thị sau khi job succeeded
□ Overall fit score hiển thị (VD: 75.9)
□ Score breakdown hiển thị đầy đủ:
  □ Skill match
  □ Responsibility match
  □ Experience level
  □ Project relevance
  □ CV quality

□ Matched skills hiển thị
□ Missing skills hiển thị

□ Evidence section hiển thị (nếu Phase 2 enrichment done):
  □ Claim
  □ JD Requirement
  □ CV Evidence
  □ Status (found/partial/missing)

□ Top actions/recommendations hiển thị

□ Interview questions hiển thị (nếu Phase 2 enrichment done)

□ Career roadmap hiển thị (nếu Phase 2 enrichment done)
```

### 1.6 Report Download

```
□ Download button hiển thị sau khi result sẵn sàng
□ Click Download → DOCX file download
□ DOCX file mở được (Word, Google Docs)
□ DOCX content chứa:
  □ Overall fit score
  □ Score breakdown
  □ Skill gaps
  □ Recommendations
  □ Evidence (nếu Phase 2 enrichment done)
  □ Interview questions (nếu Phase 2 enrichment done)
  □ Career roadmap (nếu Phase 2 enrichment done)
□ File size > 0 bytes
□ Filename đúng format (cvfit_report_*.docx)
```

### 1.7 Console Check (Guest Flow)

```
□ Mở DevTools Console tab
□ Refresh trang
□ Load lại file
□ Upload CV và tạo job
□ KIỂM TRA: Không có access_token trong console
□ KIỂM TRA: Không có password trong console
□ KIỂM TRA: Không có JWT trong console
□ KIỂM TRA: Không có raw CV text trong console
□ KIỂM TRA: Không có local_path/storage_path trong console
□ KIỂM TRA: Không có s3_key trong console

□ Chỉ được phép log:
  □ HTTP request paths (/v1/cv/upload, /v1/jobs/create-score, etc.)
  □ Status messages (uploading, analyzing, etc.)
  □ Error messages (user-friendly, không có stack trace)
```

### 1.8 Network Tab Check (Guest Flow)

```
□ Mở DevTools Network tab
□ Refresh trang
□ Upload CV và tạo job
□ KIỂM TRA Request /v1/cv/upload:
  □ Không có CV content trong query params
  □ Content-Type đúng

□ KIỂM TRA Request /v1/jobs/create-score:
  □ Response chứa access_token
  □ access_token KHÔNG được log ra console

□ KIỂM TRA Request /v1/jobs/{id}/result:
  □ access_token trong query param (?access_token=xxx)
  □ Response không chứa internal fields

□ KIỂM TRA Request /v1/jobs/{id}/report/download:
  □ access_token trong query param
  □ Response là DOCX binary
```

---

## PHẦN 2: Logged-in Flow Test

### 2.1 Registration

```
□ Link/button "Register" hoặc "Sign up" hiển thị
□ Click → registration form hiển thị

□ Nhập email hợp lệ → validation pass
□ Nhập email không hợp lệ → error message
□ Nhập password ngắn (< 8 chars) → error message
□ Nhập password đủ (> 8 chars) → validation pass
□ Nhập full_name → validation pass

□ Submit → success message hoặc redirect
□ Email đã tồn tại → error message 409

□ Console check: Không có password/token leak
```

### 2.2 Login

```
□ Link/button "Login" hoặc "Sign in" hiển thị
□ Click → login form hiển thị

□ Nhập email đúng + password đúng → login success
□ Nhập email đúng + password sai → error message 401
□ Nhập email sai → error message 401
□ Submit không nhập gì → validation error

□ Login success → redirect hoặc home page update
□ User info hiển thị (email/name)

□ Console check: Không có password/token leak
```

### 2.3 Logged-in Upload + Create Score

```
□ Upload CV → thành công
□ Paste JD → đủ điều kiện
□ Click Analyze

□ Result hiển thị
□ Job xuất hiện trong /history
```

### 2.4 History Page

```
□ Navigate to /history (hoặc click history button)
□ History page hiển thị
□ Job vừa tạo xuất hiện trong danh sách
□ Job hiển thị:
  □ Job ID / Timestamp
  □ Status (succeeded/failed)
  □ Overall fit score
  □ Target role (nếu có)
  □ Has report indicator

□ Click vào job → xem result
□ Download report từ history

□ Console check: access_token_hash, password_hash KHÔNG xuất hiện
```

### 2.5 Multi-User Isolation Test

```
□ Tạo 2 tài khoản khác nhau (User A và User B)
□ User A tạo job
□ User B đăng nhập
□ User B vào /history
□ KIỂM TRA: Không thấy job của User A
□ User B thử access job của User A bằng direct URL
□ KIỂM TRA: Nhận 403 Forbidden

□ User B tạo job riêng
□ User A đăng nhập
□ KIỂM TRA: User A chỉ thấy job của mình
```

### 2.6 Logout

```
□ Click logout button
□ Redirect về home/login page
□ Session cleared
□ Thử access /history → redirect về login
□ Thử access job result bằng access_token (nếu guest flow trước đó) → vẫn được (access_token vẫn valid)
```

---

## PHẦN 3: Error States Test

### 3.1 API Error Handling

```
□ Upload file không hợp lệ → frontend validation message
□ Upload file quá lớn → error message rõ ràng
□ Paste JD quá ngắn → validation message

□ Tạo job với cv_file_id không tồn tại → 404 error
□ Tạo job không có JD → validation error

□ Access /result không có token → 403 (guest) hoặc 401 (chưa login)
□ Access /result với token sai → 403
□ Access /result của job khác → 403

□ Access /history không login → 401 redirect to login
```

### 3.2 Error Message Format

```
□ Error message không chứa stack trace
□ Error message không chứa internal paths (/app/backend/...)
□ Error message không chứa database query
□ Error message không chứa sensitive data (tokens, passwords)
□ Error message user-friendly, có hướng dẫn cụ thể

□ Ví dụ:
  ✅ "CV file is too large. Max size is 10 MB."
  ❌ "UploadValidationError: file exceeds CV_MAX_UPLOAD_MB"

  ✅ "Please upload a PDF or DOCX file."
  ❌ "Unsupported content type: application/x-msdownload"

  ✅ "Analysis could not be completed. Please try again."
  ❌ "CeleryTimeoutError: task exceeded max retries"
```

### 3.3 Browser Network Error Handling

```
□ Tắt network → thử upload → offline error message
□ Re-enable network → retry thành công

□ Job timeout → friendly message
□ Server error (500) → friendly message, không có stack trace
□ Service unavailable (503) → friendly message
```

---

## PHẦN 4: Security Verification

### 4.1 Token Handling

```
□ Access token KHÔNG được lưu trong localStorage (chỉ memory/sessionStorage)
□ Refresh trang → access token vẫn trong memory
□ Close tab → access token mất (nếu dùng sessionStorage)
□ Browser back → không quay lại result page không có token

□ JWT KHÔNG được log ra console
□ Password KHÔNG được log ra console
□ CV content KHÔNG được log ra console
□ Internal paths KHÔNG được log ra console
```

### 4.2 URL Security

```
□ URL chứa access_token KHÔNG được paste vào chat/docs/email
□ URL chứa access_token KHÔNG được gửi qua analytics
□ URL có token được tạo mới cho mỗi job (không reuse)

□ DevTools → Application tab → kiểm tra:
  □ localStorage không chứa access_token
  □ sessionStorage không chứa access_token
  □ Cookies có appropriate flags (HttpOnly, Secure)
```

### 4.3 CORS Verification

```
□ Frontend từ localhost:3000 gọi API → CORS OK
□ Frontend từ production URL gọi API → CORS OK
□ Frontend từ domain khác gọi API → CORS blocked (nếu không allow)
□ Preflight OPTIONS request hoạt động
```

---

## PHẦN 5: Performance Check

```
□ Page load time < 3s (first load)
□ API response time < 2s (health, upload metadata)
□ Job creation < 1s
□ Poll interval 3s (hợp lý, không quá frequent)
□ Report download < 5s cho file < 1MB

□ Memory usage stable sau nhiều job
□ Không có memory leak khi polling nhiều lần
```

---

## PHẦN 6: Accessibility Check

```
□ Alt text cho images
□ ARIA labels cho interactive elements
□ Keyboard navigation (Tab, Enter, Escape)
□ Focus indicator hiển thị
□ Color contrast đủ (WCAG AA)
□ Error messages associated với form fields (aria-describedby)
```

---

## Bug Report Template

Nếu phát hiện bug, report theo format:

```markdown
## Bug #[N]

**Severity:** Critical / High / Medium / Low
**Priority:** P0 / P1 / P2 / P3
**Environment:** Browser, OS, Backend URL
**Steps to Reproduce:**
1.
2.
3.

**Expected Behavior:**


**Actual Behavior:**


**Console Output:** (nếu có)


**Network Request:** (nếu có)


**Screenshots:**


**Reproduction Rate:** Always / Sometimes / Rarely
**Notes:**
```

---

## Sign-off Sheet

| Test Category | Tester | Date | Result |
|---------------|--------|------|--------|
| Guest Flow Test | | | ✅ PASS / ❌ FAIL |
| Logged-in Flow Test | | | ✅ PASS / ❌ FAIL |
| Error States Test | | | ✅ PASS / ❌ FAIL |
| Security Verification | | | ✅ PASS / ❌ FAIL |
| Performance Check | | | ✅ PASS / ❌ FAIL |
| Accessibility Check | | | ✅ PASS / ❌ FAIL |

**Overall Result:** ✅ ALL PASS / ❌ ISSUES FOUND

**Notes:**
