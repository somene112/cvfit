# Phase 1 Demo Script

Target length: 3-5 minutes.

## Setup

- Use the deployed backend: `https://cvfit.onrender.com`.
- Use a dummy CV only. Do not upload a real personal CV.
- Keep the current FastAPI-served Jinja/vanilla JS UI as the fallback demo path unless a separate Next frontend has been validated.

## Talk Track

1. Open the app and show the upload/JD workflow.
   - Explain that Phase 1 is guest mode: no login, no accounts, no user history.
   - Point out that PDF/DOCX upload and pasted JD are the only required inputs.

2. Upload a dummy CV and paste a realistic JD.
   - Use synthetic content only.
   - Explain that the backend stores the CV privately and creates an async analysis job.

3. Start analysis and show the loading state.
   - The API creates a `job_id` plus an access token.
   - The token is held by the client flow and is not printed in logs or UI.
   - The worker processes the job through Redis and updates status.

4. Show the result and DOCX report download.
   - Result/report endpoints require the correct access token.
   - Missing or wrong token is rejected.
   - DOCX report download is available only after the job succeeds.

5. Close with Phase 1 evidence.
   - Render backend smoke passed.
   - Alembic baseline was validated on disposable PostgreSQL/pgvector.
   - S3 lifecycle cleanup was applied and verified.
   - Full login, user accounts, history, and richer dashboards are Phase 2.

## Fallback Notes

- If the separate Next frontend is not ready, demo the FastAPI-served Jinja/vanilla JS UI.
- If a live smoke job is slow, use the latest smoke evidence in `docs/01_phase1_closeout_checklist.md`.
- If AWS or Render has a transient issue, show the PR summary and run local validation commands from `docs/phase1_closeout_pr_summary.md`.
