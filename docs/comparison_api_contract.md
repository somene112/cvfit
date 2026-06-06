# Phase 4 Re-analysis And Comparison API Contract

## Purpose

Phase 4 adds a planned re-analysis and comparison workflow:

1. A user uploads a revised CV for the same JD, or optionally an updated JD.
2. The backend creates a new linked analysis job.
3. The original job remains immutable.
4. The user compares the original and revised jobs by score, evidence, resolved gaps, remaining gaps, and keyword stuffing warnings.

This document is a contract only. It does not implement endpoints, database fields, migrations, or frontend code.

## Current Architecture To Preserve

- `AnalysisJob.result_json` stores completed analysis output.
- `POST /v1/jobs/create-score` creates analysis jobs.
- `GET /v1/jobs/{job_id}/result` returns result data.
- Result/report/download access is authorized by either owner JWT or guest `access_token`.
- Logged-in history returns only jobs owned by the current user.
- Guest `access_token` values are secrets and must be redacted from logs and docs.

## Re-analysis Endpoint

```http
POST /v1/jobs/{job_id}/reanalyze
Content-Type: multipart/form-data
```

Purpose:

- Upload a revised CV for the same JD.
- Optionally submit updated `jd_text`.
- Create a linked analysis job.
- Preserve current owner JWT and guest access-token behavior.

### Request Example: Logged-In User

```http
POST /v1/jobs/7f7ee6ba-15f3-4771-9a10-5124c77a5c2b/reanalyze
Authorization: Bearer <jwt>
Content-Type: multipart/form-data
```

Multipart fields:

| Field | Required | Notes |
| --- | --- | --- |
| `file` | Yes | Revised CV file. Same validation rules as current CV upload. |
| `jd_text` | No | Optional updated JD. If omitted, reuse the original job's JD. |

### Request Example: Guest User

```http
POST /v1/jobs/7f7ee6ba-15f3-4771-9a10-5124c77a5c2b/reanalyze
Content-Type: multipart/form-data
```

Multipart fields:

| Field | Required | Notes |
| --- | --- | --- |
| `file` | Yes | Revised CV file. |
| `jd_text` | No | Optional updated JD. |
| `access_token` | Yes for guest | Current guest job secret for the parent job. Prefer multipart field over query string to reduce accidental URL logging. |

Compatibility note: if a transition implementation accepts `?access_token=...`, logs and error messages must redact the token and must not print full URLs.

### Response Example

```json
{
  "job_id": "b629ab3e-7d38-47b2-b9fa-c14ccabf7a31",
  "access_token": "new-guest-job-secret",
  "parent_job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "analysis_group_id": "grp_91d1377b",
  "revision_number": 2,
  "status": "queued"
}
```

### Behavior

- Logged-in users can reanalyze their own jobs.
- Guest users can reanalyze only with a valid access token for the parent job.
- Original job remains immutable.
- New job gets:
  - `parent_job_id`
  - `analysis_group_id`
  - `revision_number`
- If the parent job already has an `analysis_group_id`, reuse it.
- If the parent job has no group yet, create a new group and treat the original as revision `1`.
- The revised job receives its own guest `access_token` when guest compatibility requires it.
- Updated `jd_text` creates a new JD association for the revised job; omitted `jd_text` reuses the original JD.
- Polling uses the existing `GET /v1/jobs/{job_id}` status endpoint.
- Result retrieval uses the existing `GET /v1/jobs/{job_id}/result` endpoint.

### Planned Errors

| Status | Condition |
| --- | --- |
| `400` | Invalid UUID, invalid multipart request, missing file, unsupported file type, oversized file, or failed parse. |
| `401` | Invalid Bearer token. |
| `403` | Logged-in user does not own the parent job, or guest access token is missing/wrong. |
| `404` | Parent job not found. |
| `409` | Parent job is not in a state that can be reanalyzed, for example missing JD data or failed original parse. |
| `422` | Request shape is valid HTTP but semantically invalid. |

## Comparison Endpoint

```http
GET /v1/jobs/{base_job_id}/comparison/{new_job_id}
```

Purpose:

- Compare two jobs in the same revision group or otherwise allowed access scope.
- Show progress from an earlier job to a later job.
- Explain evidence quality and remaining risks, not only score delta.

### Request Example: Logged-In User

```http
GET /v1/jobs/7f7ee6ba-15f3-4771-9a10-5124c77a5c2b/comparison/b629ab3e-7d38-47b2-b9fa-c14ccabf7a31
Authorization: Bearer <jwt>
```

### Request Example: Guest User

```http
GET /v1/jobs/7f7ee6ba-15f3-4771-9a10-5124c77a5c2b/comparison/b629ab3e-7d38-47b2-b9fa-c14ccabf7a31?access_token=<comparison-token>
```

Guest token options to decide during implementation:

- Accept the newest job's `access_token` when the jobs share an analysis group.
- Or require both base and new job tokens through a safer request pattern.

Do not leak tokens in logs, docs, analytics, browser console, or error messages.

### Output Example

```json
{
  "base_job_id": "7f7ee6ba-15f3-4771-9a10-5124c77a5c2b",
  "new_job_id": "b629ab3e-7d38-47b2-b9fa-c14ccabf7a31",
  "score_delta": 12.4,
  "base_score": 63.5,
  "new_score": 75.9,
  "breakdown_delta": {
    "skill_match": 8,
    "experience_match": 5
  },
  "resolved_missing_skills": [],
  "still_missing_skills": [],
  "newly_matched_skills": [],
  "new_evidence": [],
  "keyword_stuffing_warnings": [],
  "improvement_summary": "The revised CV improved backend evidence, but deployment evidence still needs concrete project detail.",
  "next_actions": []
}
```

Expanded field notes:

- `score_delta`: `new_score - base_score`.
- `breakdown_delta`: Component-level deltas when both results expose comparable score keys.
- `resolved_missing_skills`: Gaps from the base result that now have meaningful evidence.
- `still_missing_skills`: Gaps that remain missing or weakly evidenced.
- `newly_matched_skills`: Skills newly supported by evidence in the revised result.
- `new_evidence`: New CV evidence snippets or evidence IDs in the revised result.
- `keyword_stuffing_warnings`: Warnings for repeated JD keywords without meaningful context.
- `improvement_summary`: Short evidence-first summary.
- `next_actions`: Follow-up actions, preferably linked to v3 `improvement_actions`.

### Comparison Rules

- Score delta is not enough; evidence quality matters.
- Resolved gaps require actual evidence, not repeated keywords.
- Keyword stuffing should produce warnings.
- Unrelated CV length increase should not be treated as real improvement.
- Comparison must not fabricate claims.
- New evidence should be short, relevant, and traceable to parsed CV text.
- A missing skill should not move to resolved unless there is specific CV evidence.
- A rewritten bullet with stronger structure but no new facts can improve CV quality, but should not falsely resolve a missing skill.
- If the JD changed, the comparison must say that results are not a pure CV-only before/after comparison.

### Auth Rules

- Logged-in user must own both jobs or have allowed access to both jobs.
- Guest comparison requires a valid token/access pattern.
- Guest token comparison must only allow jobs in the same allowed analysis group.
- Do not return any `access_token`, `access_token_hash`, JWT, storage path, local path, S3 key, raw CV text, or report path.
- Do not log full URLs containing `access_token`.

### Planned Errors

| Status | Condition |
| --- | --- |
| `400` | Invalid UUID or invalid comparison request. |
| `401` | Invalid Bearer token. |
| `403` | Caller lacks access to either job. |
| `404` | Either job is not found. |
| `409` | One or both jobs are not complete, results are unavailable, or jobs are not comparable. |

## Backend Implementation Notes For Later PRs

Likely surfaces:

- `backend/app/api/routes/jobs.py`: add route handlers after contracts/evaluation are ready.
- `backend/app/db/models.py`: may need revision linkage fields if JSON metadata is not enough.
- `backend/alembic/versions/`: may need migration for `parent_job_id`, `analysis_group_id`, and `revision_number`.
- `backend/app/workers/tasks.py`: create v3 result metadata and report v3 sections.
- `backend/app/services/scoring/result_v2.py`: likely basis for a v3 builder/enricher.
- `backend/app/services/reporting/report_docx.py`: add report v3 support after result v3 stabilizes.

No implementation should be added in the contract-only PR.
