# Phase 1 Smoke Test Runbook

## Repeatable backend smoke script

Use the scripted smoke test after deploying the backend and worker. It uploads one tester-provided dummy PDF/DOCX CV, creates a job, verifies access-token protection, waits for the job, fetches result/report metadata, and verifies DOCX download. The script does not print the access token or raw CV content.

No safe sample CV is committed in this repo. Use a dummy CV only; do not use a real personal CV.

```powershell
$env:API_BASE_URL="https://cvfit.onrender.com"
$env:TEST_CV_PATH="D:\path\to\dummy_cv.docx"
python scripts/smoke_phase1_backend.py
```

Optional timeout override:

```powershell
$env:SMOKE_TIMEOUT_SECONDS="300"
```

## Backend health

```powershell
$API_BASE_URL="https://cvfit.onrender.com"
curl.exe -i "$API_BASE_URL/health"
```

Expected:
- 200 OK
- JSON health payload
- no crash in Render logs

## Upload CV

```powershell
curl.exe -i -X POST "$API_BASE_URL/v1/cv/upload" `
  -F "file=@D:\path\to\sample_cv.pdf"
```

Save `cv_id`.

## Create score job

```powershell
$CV_ID="<cv_id>"

curl.exe -i -X POST "$API_BASE_URL/v1/jobs/create-score" `
  -H "Content-Type: application/json" `
  -d "{\"cv_id\":\"$CV_ID\",\"job_description\":\"We need a Python FastAPI developer with PostgreSQL experience.\"}"
```

Save:
- `job_id`
- `access_token`

## Poll job

```powershell
$JOB_ID="<job_id>"
curl.exe -i "$API_BASE_URL/v1/jobs/$JOB_ID"
```

Expected:
- queued/running/succeeded/failed
- no sensitive report content in plain status endpoint

## Result security test

```powershell
curl.exe -i "$API_BASE_URL/v1/jobs/$JOB_ID/result"
curl.exe -i "$API_BASE_URL/v1/jobs/$JOB_ID/result?access_token=wrong-token"
```

Expected:
- 401/403

Correct token:

```powershell
$TOKEN="<access_token>"
curl.exe -i "$API_BASE_URL/v1/jobs/$JOB_ID/result?access_token=$TOKEN"
```

Expected:
- 200
- score/feedback JSON

## Download report

```powershell
curl.exe -L -o report.docx "$API_BASE_URL/v1/jobs/$JOB_ID/report/download?access_token=$TOKEN"
dir report.docx
```

Expected:
- report.docx exists
- file size > 0

## Frontend smoke

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Open:

```text
http://localhost:3000
```

Check:
- landing page
- analyze page
- result page
- download report
- no token in browser console
