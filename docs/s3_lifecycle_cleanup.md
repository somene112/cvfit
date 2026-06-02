# S3 Lifecycle Cleanup — Phase 2 Hoàn Thiện

## Tổng Quan

File này là document hoàn thiện Phase 2 về S3 lifecycle cleanup, bổ sung chi tiết theo yêu cầu trong `phase.txt`. Document `docs/04_s3_cleanup_runbook.md` đã có phần cơ bản; file này bổ sung thêm retention policy chi tiết theo environment, checklist verification, và Phase 2/3 expansion notes.

---

## 1. Retention Policy Theo Environment

### 1.1 Render Smoke Test Environment

| Object Type | Prefix | Retention | Action |
|-------------|--------|-----------|--------|
| Temporary uploads | `tmp/` | 1-3 ngày | Auto-expire |
| Smoke test CVs | `uploads/` | 1-3 ngày | Auto-expire |
| Smoke test reports | `reports/` | 1-3 ngày | Auto-expire |

**Ghi chú:** Smoke test environment chỉ dùng cho automated tests. Objects tự động expire sau 1-3 ngày, không cần manual cleanup.

### 1.2 Development Environment

| Object Type | Prefix | Retention | Action |
|-------------|--------|-----------|--------|
| All uploads | `uploads/` | 7-14 ngày | Auto-expire |
| All reports | `reports/` | 7-14 ngày | Auto-expire |
| Temporary files | `tmp/` | 1 ngày | Auto-expire |

**Ghi chú:** Dev environment dùng cho local development và testing. 7-14 ngày đủ để debug mà không tốn nhiều storage.

### 1.3 Production Environment (Guest Mode - Phase 2)

| Object Type | Prefix | Retention | Action |
|-------------|--------|-----------|--------|
| Raw CV uploads | `uploads/` | 30 ngày | Auto-expire |
| Generated reports | `reports/` | 30 ngày | Auto-expire |
| Temporary files | `tmp/` | 1 ngày | Auto-expire |

**Ghi chú:** Guest mode (không login) — user không có account nên không cần giữ lâu. 30 ngày đủ để quay lại lấy kết quả.

### 1.4 Production Environment (User-Owned - Phase 3+)

| Object Type | Prefix | Retention | Action |
|-------------|--------|-----------|--------|
| Retained CVs (user opted-in) | `uploads/retained/` | User-defined (30-365 ngày) | Auto-expire hoặc user delete |
| User-owned reports | `reports/user-{user_id}/` | User-defined (30-365 ngày) | Auto-expire hoặc user delete |
| Temporary guest uploads | `uploads/guest/` | 7 ngày | Auto-expire |
| Guest reports | `reports/guest/` | 7 ngày | Auto-expire |

**Ghi chú:** Phase 3+ sẽ tách prefix cho user-owned vs guest. Xem chi tiết trong Section 4.

---

## 2. S3 Lifecycle Policy Files

### 2.1 Render Smoke / Development Policy (`infra/s3-lifecycle-dev.json`)

```json
{
  "Rules": [
    {
      "ID": "expire-temporary-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "tmp/" },
      "Expiration": { "Days": 1 }
    },
    {
      "ID": "expire-all-uploads-dev",
      "Status": "Enabled",
      "Filter": { "Prefix": "uploads/" },
      "Expiration": { "Days": 7 }
    },
    {
      "ID": "expire-all-reports-dev",
      "Status": "Enabled",
      "Filter": { "Prefix": "reports/" },
      "Expiration": { "Days": 7 }
    },
    {
      "ID": "abort-incomplete-multipart-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
```

### 2.2 Production Policy (`infra/s3-lifecycle.json`)

```json
{
  "Rules": [
    {
      "ID": "expire-temporary-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "tmp/" },
      "Expiration": { "Days": 1 }
    },
    {
      "ID": "expire-raw-cv-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "uploads/" },
      "Expiration": { "Days": 30 }
    },
    {
      "ID": "expire-generated-reports",
      "Status": "Enabled",
      "Filter": { "Prefix": "reports/" },
      "Expiration": { "Days": 30 }
    },
    {
      "ID": "abort-incomplete-multipart-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
```

---

## 3. Áp Dụng Lifecycle Policy

### 3.1 Verify AWS Credentials

```powershell
# Kiểm tra credentials trước khi apply bất kỳ policy nào
aws sts get-caller-identity
aws configure get region
```

### 3.2 Apply Render Smoke / Dev Policy

```powershell
# Set biến môi trường
$env:S3_BUCKET = "your-dev-bucket"
$env:AWS_REGION = "ap-southeast-2"

# Verify hiện tại
aws s3api get-bucket-lifecycle-configuration --bucket $env:S3_BUCKET --region $env:AWS_REGION

# Apply dev policy
aws s3api put-bucket-lifecycle-configuration `
  --bucket $env:S3_BUCKET `
  --region $env:AWS_REGION `
  --lifecycle-configuration file://infra/s3-lifecycle-dev.json

# Verify đã apply
aws s3api get-bucket-lifecycle-configuration --bucket $env:S3_BUCKET --region $env:AWS_REGION
```

### 3.3 Apply Production Policy

```powershell
# Set biến môi trường
$env:S3_BUCKET = "2026-fpt-exe-app"
$env:AWS_REGION = "ap-southeast-2"

# Nếu dùng S3_PREFIX (recommended cho production)
# Thay đổi prefix trong policy file trước khi apply:
# "Prefix": "uploads/" -> "Prefix": "cvfit-prod/uploads/"
# "Prefix": "reports/" -> "Prefix": "cvfit-prod/reports/"
# "Prefix": "tmp/" -> "Prefix": "cvfit-prod/tmp/"

# Verify hiện tại
aws s3api get-bucket-lifecycle-configuration --bucket $env:S3_BUCKET --region $env:AWS_REGION

# Apply production policy
aws s3api put-bucket-lifecycle-configuration `
  --bucket $env:S3_BUCKET `
  --region $env:AWS_REGION `
  --lifecycle-configuration file://infra/s3-lifecycle.json

# Verify đã apply
aws s3api get-bucket-lifecycle-configuration --bucket $env:S3_BUCKET --region $env:AWS_REGION
```

### 3.4 Nếu Dùng S3_PREFIX

```powershell
# Tạo policy file riêng cho prefix-based setup
# Thay cvfit-prod bằng giá trị S3_PREFIX thực tế của bạn

$prefix = "cvfit-prod"

# Tạo policy với prefix
$policy = @"
{
  "Rules": [
    {
      "ID": "expire-temporary-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "${prefix}/tmp/" },
      "Expiration": { "Days": 1 }
    },
    {
      "ID": "expire-raw-cv-uploads",
      "Status": "Enabled",
      "Filter": { "Prefix": "${prefix}/uploads/" },
      "Expiration": { "Days": 30 }
    },
    {
      "ID": "expire-generated-reports",
      "Status": "Enabled",
      "Filter": { "Prefix": "${prefix}/reports/" },
      "Expiration": { "Days": 30 }
    },
    {
      "ID": "abort-incomplete-multipart-uploads",
      " "Status": "Enabled",
      "Filter": { "Prefix": "${prefix}/" },
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
"@

# Lưu và apply
$policy | Out-File -FilePath infra/s3-lifecycle-prod.json -Encoding utf8
aws s3api put-bucket-lifecycle-configuration `
  --bucket $env:S3_BUCKET `
  --region $env:AWS_REGION `
  --lifecycle-configuration file://infra/s3-lifecycle-prod.json
```

---

## 4. Checklist Verification

### 4.1 Trước Khi Apply

```
□ Đã kiểm tra AWS credentials (sts get-caller-identity)
□ Đã xác định đúng bucket cho environment (dev vs production)
□ Đã backup/restore plan cho production bucket
□ Đã thông báo cho team về policy change
□ Đã kiểm tra current lifecycle policy (nếu có)
□ Đã confirm retention days phù hợp với compliance requirements
□ Đã review policy JSON không có typo
□ Đã confirm không có production data sẽ bị xóa quá sớm
```

### 4.2 Sau Khi Apply

```
□ Đã verify bằng get-bucket-lifecycle-configuration
□ Đã check tất cả rules có Status = "Enabled"
□ Đã xác nhận không có rule sai prefix
□ Đã test thử upload một object và verify expire hoạt động (optional)
□ Đã update docs với policy version và ngày apply
□ Đã thông báo cho team về policy đã apply
```

### 4.3 Privacy Checklist

```
□ Không log raw CV text trong application logs
□ Không log S3 signed URL hoặc access token
□ Không expose local_path, storage_path, s3_key trong API response
□ Report download chỉ qua access_token hoặc owner JWT
□ Raw CV có TTL (lifecycle policy đã apply)
□ Generated report có TTL (lifecycle policy đã apply)
□ Incomplete multipart upload được abort sau 7 ngày
□ Không xóa production objects thủ công nếu không cần thiết
```

---

## 5. Phase 3+ Expansion: User-Owned vs Guest Separation

### 5.1 Tại Sao Cần Tách

Khi có user accounts (Phase 3+):
- User có thể muốn giữ lại reports lâu hơn guest
- User có thể muốn download lại report sau vài tuần
- Cần differentiate giữa user-owned data và temporary guest data
- Privacy regulation có thể yêu cầu different retention cho authenticated vs anonymous users

### 5.2 Proposed Prefix Structure

```
uploads/
├── guest/              # Anonymous uploads (7 ngày expire)
│   └── {uuid}.pdf
├── retained/           # User opted-in retention (30-365 ngày)
│   └── {user_id}/
│       └── {uuid}.pdf
uploads/

reports/
├── guest/             # Guest reports (7 ngày expire)
│   └── {job_id}.docx
├── user-{user_id}/    # User-owned reports (30-365 ngày)
│   └── {job_id}.docx
reports/

tmp/                  # Temporary files (1 ngày expire)
```

### 5.3 Phase 3 Checklist

```
□ Tạo migration để thêm user ownership vào CV file metadata
□ Update storage helpers để save vào prefix đúng dựa trên user_id
□ Tạo s3-lifecycle-user-owned.json với longer retention
□ Apply user-owned policy cho prefixes mới
□ Update docs để reflect prefix separation
□ Test lifecycle cho cả guest và user-owned objects
```

---

## 6. Emergency Response

### 6.1 Nếu Policy Sai

```powershell
# Disable policy bằng cách apply empty policy
aws s3api delete-bucket-lifecycle-configuration `
  --bucket $env:S3_BUCKET `
  --region $env:AWS_REGION

# Verify đã disabled
aws s3api get-bucket-lifecycle-configuration --bucket $env:S3_BUCKET --region $env:AWS_REGION
# Nếu return ResourceNotFoundException = đã disabled thành công
```

### 6.2 Nếu Object Bị Xóa Sớm

- Objects có thể được recover trong vài ngày tùy provider (S3 Glacier hoặc S3 Glacier Deep Archive)
- Kiểm tra bucket versioning — nếu enabled, có thể restore từ previous version
- Không có cách restore nếu bucket không có versioning và object đã expire

### 6.3 Nếu Cần Extend Retention

```powershell
# Update policy với longer expiration
# Sửa "Expiration": { "Days": 30 } thành giá trị mới
# Apply lại policy
aws s3api put-bucket-lifecycle-configuration `
  --bucket $env:S3_BUCKET `
  --region $env:AWS_REGION `
  --lifecycle-configuration file://infra/s3-lifecycle-updated.json
```

---

## 7. AWS Provider-Specific Notes

### 7.1 AWS S3 (Amazon S3)

- Hỗ trợ đầy đủ tất cả lifecycle actions
- Có S3 Intelligent-Tiering cho objects access pattern không đoán trước được
- S3 Object Lock có thể dùng cho compliance retention

### 7.2 Backblaze B2

- Lifecycle rules có thể configure qua B2 Cloud Storage
- Sử dụng `s3-compatible` endpoint thay vì AWS S3 endpoint
- Cần update `S3_ENDPOINT_URL` trong app config

### 7.3 Cloudflare R2

- R2 không có native lifecycle rules như S3
- Cần implement custom cleanup job hoặc dùng Workers
- Xem R2 pricing để estimate storage costs

### 7.4 MinIO (Local/On-Premise)

- MinIO hỗ trợ lifecycle rules tương tự AWS S3
- Có thể dùng `mc ilm` command để manage lifecycle
- Testing trên MinIO trước khi apply lên cloud

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-30 | Initial Phase 1 S3 lifecycle (30-day policy) |
| 2.0 | 2026-06-02 | Phase 2 hoàn thiện — thêm dev/smoke retention, provider notes, Phase 3 expansion |
