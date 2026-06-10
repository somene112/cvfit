# Application Workspace Contract — Phase 5

**Version:** 1.0
**Date:** 2026-06-10
**Owner (backend):** Phúc
**Owner (frontend):** Quân
**Status:** Contract only — no implementation in this PR

---

## A. Scope

This contract covers four sub-systems for Phase 5:

1. **Application Workspace v1** — CRUD for job applications and the ability to attach an existing analysis job to an application.
2. **Career Profile / Evidence Vault v1** — CRUD for persistent career evidence items (skills, projects, experience, etc.).
3. **Application Package v1** — generate, retrieve, and download stub for a bundled application artifact.
4. **Readiness Summary v1** — derive and return a readiness summary for an application from its attached analysis result.

All endpoints require JWT Bearer auth. No guest access_token support for these resources.

---

## B. Data Model Proposal

> Implementation in Alembic migration PR3. No tables are created in this PR.

### `applications`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | indexed; ownership scope |
| `job_title` | string NOT NULL | |
| `company_name` | string nullable | |
| `jd_text` | text NOT NULL | user-provided JD for this application |
| `target_role` | string nullable | optional freeform role label |
| `status` | enum NOT NULL | see enum definitions |
| `best_analysis_job_id` | UUID nullable FK → jobs | the analysis job attached to this application |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### `career_profile_items`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | indexed; ownership scope |
| `item_type` | enum NOT NULL | see enum definitions |
| `title` | string NOT NULL | |
| `description` | text nullable | |
| `skills_json` | JSON nullable | for skill items: list of skill strings |
| `evidence_text` | text nullable | supporting evidence for this item |
| `source` | string nullable | e.g., "GitHub", "certificate link", "employer" |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### `application_artifacts`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | indexed; ownership scope |
| `application_id` | UUID FK → applications | |
| `artifact_type` | enum NOT NULL | see enum definitions |
| `payload_json` | JSON NOT NULL | structured artifact content |
| `storage_key` | string nullable | only populated when a file is exported; not exposed raw |
| `created_at` | timestamp | |

---

## C. Enum and Status Definitions

### `application.status`

| Value | Meaning |
|---|---|
| `draft` | Application created but analysis not attached |
| `analyzing` | Analysis job is in progress |
| `improving_cv` | User is acting on improvement suggestions |
| `ready_to_apply` | Readiness summary reached a usable state |
| `interview_prep` | User is in interview practice phase |
| `applied` | User has submitted the application externally |
| `archived` | Application is closed/no longer active |

### `career_profile_item.item_type`

| Value |
|---|
| `skill` |
| `project` |
| `experience` |
| `education` |
| `certification` |
| `achievement` |
| `link` |

### `application_artifact.artifact_type`

| Value |
|---|
| `application_package` |
| `cover_letter_draft` |
| `interview_practice_result` |
| `readiness_summary` |

---

## D. API Endpoints

### Applications

#### `POST /v1/applications`

Create a new application.

- **Auth:** JWT Bearer required
- **Request body:**
  ```json
  {
    "job_title": "Backend Engineer",
    "company_name": "Acme Corp",
    "jd_text": "We are looking for...",
    "target_role": "Backend"
  }
  ```
- **Response `201`:**
  ```json
  {
    "id": "uuid",
    "user_id": "uuid",
    "job_title": "Backend Engineer",
    "company_name": "Acme Corp",
    "jd_text": "We are looking for...",
    "target_role": "Backend",
    "status": "draft",
    "best_analysis_job_id": null,
    "created_at": "2026-06-10T10:00:00Z",
    "updated_at": "2026-06-10T10:00:00Z"
  }
  ```
- **Errors:** 401, 422

---

#### `GET /v1/applications`

List all applications for the authenticated user.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "job_title": "Backend Engineer",
        "company_name": "Acme Corp",
        "status": "draft",
        "best_analysis_job_id": null,
        "created_at": "2026-06-10T10:00:00Z",
        "updated_at": "2026-06-10T10:00:00Z"
      }
    ],
    "total": 1
  }
  ```
- **Errors:** 401

---

#### `GET /v1/applications/{application_id}`

Get a single application.

- **Auth:** JWT Bearer required
- **Response `200`:** Full application object (same shape as POST 201).
- **Errors:** 401, 403 (not owner), 404

---

#### `PATCH /v1/applications/{application_id}`

Update mutable fields of an application.

- **Auth:** JWT Bearer required
- **Request body (all fields optional):**
  ```json
  {
    "job_title": "Senior Backend Engineer",
    "company_name": "New Corp",
    "jd_text": "Updated JD...",
    "target_role": "Senior Backend",
    "status": "improving_cv"
  }
  ```
- **Response `200`:** Updated application object.
- **Errors:** 401, 403, 404, 422

---

#### `DELETE /v1/applications/{application_id}`

Delete an application and its artifacts.

- **Auth:** JWT Bearer required
- **Response `204`:** No content.
- **Errors:** 401, 403, 404

---

#### `POST /v1/applications/{application_id}/attach-analysis/{job_id}`

Attach an existing analysis job to an application and update `best_analysis_job_id`.

- **Auth:** JWT Bearer required
- **Request body:** empty
- **Ownership rule:** `job_id` must belong to the same user as `application_id`.
- **Response `200`:**
  ```json
  {
    "application_id": "uuid",
    "best_analysis_job_id": "uuid",
    "status": "analyzing"
  }
  ```
- **Errors:** 401, 403 (job or application not owned by user), 404, 422

---

#### `GET /v1/applications/{application_id}/readiness`

Get the readiness summary for an application. Derived from the attached analysis result; returns 404 if no analysis is attached.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "application_id": "uuid",
    "job_title": "Backend Engineer",
    "fit_score": 72,
    "matched_skills_count": 8,
    "missing_skills_count": 3,
    "top_missing_skills": ["Kubernetes", "Redis", "Docker"],
    "readiness_level": "moderate",
    "next_action": "Attach or upload an updated CV to address the top 3 missing skills.",
    "disclaimer": "Readiness level is derived from CV-to-JD analysis and does not guarantee any hiring outcome."
  }
  ```
- **Errors:** 401, 403, 404 (application not found or no analysis attached)

---

### Application Package

#### `POST /v1/applications/{application_id}/package/generate`

Trigger application package generation. Stores result as `application_package` artifact.

> **PR5A implementation note:** Generation is synchronous and deterministic (no LLM queue). Response status code is `201 Created` with `status: "generated"` rather than `202 Accepted / status: "generating"`. Future async generation may use `202` when a background queue is introduced. Frontend should handle both `201` and `202` from this endpoint, and treat `status: "generated"` as ready to fetch.

- **Auth:** JWT Bearer required
- **Request body:** empty (uses attached analysis job + career profile items)
- **Response `201`:**
  ```json
  {
    "application_id": "uuid",
    "artifact_id": "uuid",
    "status": "generated",
    "artifact_type": "application_package"
  }
  ```
- **Errors:** 401, 403, 404, 422 (no analysis attached)

---

#### `GET /v1/applications/{application_id}/package`

Retrieve the latest application package artifact.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "artifact_id": "uuid",
    "application_id": "uuid",
    "artifact_type": "application_package",
    "payload_json": {
      "cover_letter_draft": {},
      "readiness_summary": {},
      "matched_skills": [],
      "missing_skills": [],
      "disclaimer": ""
    },
    "created_at": "2026-06-10T10:00:00Z"
  }
  ```
  Note: `storage_key` is never returned. Only structured payload is exposed.
- **Errors:** 401, 403, 404

---

#### `GET /v1/applications/{application_id}/package/download`

Download stub. Returns the payload as a JSON download in Phase 5 v1. DOCX/PDF export is future work.

- **Auth:** JWT Bearer required
- **Response `200`:** `Content-Disposition: attachment; filename="application_package.json"`, body is the payload JSON.
- **Errors:** 401, 403, 404

---

### Cover Letter

#### `POST /v1/applications/{application_id}/cover-letter/generate`

Trigger cover letter draft generation. Uses attached analysis job, career profile items, and application workspace metadata. Stores result as `cover_letter_draft` artifact.

> **PR5A implementation note:** Same as package/generate — synchronous, returns `201 Created` with `status: "generated"`. Frontend should treat `status: "generated"` as ready to fetch via GET.

- **Auth:** JWT Bearer required
- **Request body:** empty (all inputs sourced from attached analysis + profile)
- **Ownership rule:** application must belong to the authenticated user; attached analysis job must belong to the same user.
- **Response `201`:**
  ```json
  {
    "application_id": "uuid",
    "artifact_id": "uuid",
    "status": "generated",
    "artifact_type": "cover_letter_draft"
  }
  ```
- **Errors:** 401, 403, 404, 422 (no analysis attached — cannot generate without CV evidence)

---

#### `GET /v1/applications/{application_id}/cover-letter`

Retrieve the latest cover letter draft artifact.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "artifact_id": "uuid",
    "application_id": "uuid",
    "artifact_type": "cover_letter_draft",
    "payload_json": {
      "opening": "",
      "why_role_company": "",
      "relevant_evidence": [
        {
          "evidence_item": "",
          "source": "cv_bullet | profile_item | matched_skill",
          "cv_reference": ""
        }
      ],
      "contribution_fit": "",
      "closing": "",
      "review_notes": [],
      "missing_evidence": [],
      "disclaimer": "This is a draft cover letter generated from your CV and job description. It must be reviewed and edited before submission. It does not guarantee any hiring outcome."
    },
    "created_at": "2026-06-10T10:00:00Z"
  }
  ```
  Note: `storage_key` is never returned.
- **Errors:** 401, 403, 404 (no draft generated yet)

---

#### `PATCH /v1/applications/{application_id}/cover-letter`

Update the user's edits to the cover letter draft. Stores the updated text back into the `cover_letter_draft` artifact's `payload_json`. Does not re-trigger AI generation.

- **Auth:** JWT Bearer required
- **Request body (all fields optional):**
  ```json
  {
    "opening": "Updated opening text.",
    "why_role_company": "Updated motivation section.",
    "contribution_fit": "Updated contribution section.",
    "closing": "Updated closing text."
  }
  ```
- **Response `200`:** Updated artifact object (same shape as GET response).
- **Errors:** 401, 403, 404, 422

---

### Career Profile

#### `POST /v1/profile/items`

Add a career profile item.

- **Auth:** JWT Bearer required
- **Request body:**
  ```json
  {
    "item_type": "project",
    "title": "E-commerce API",
    "description": "Built a REST API for an e-commerce platform using FastAPI and PostgreSQL.",
    "skills_json": ["FastAPI", "PostgreSQL", "Redis"],
    "evidence_text": "GitHub: github.com/user/ecommerce-api",
    "source": "GitHub"
  }
  ```
- **Response `201`:**
  ```json
  {
    "id": "uuid",
    "user_id": "uuid",
    "item_type": "project",
    "title": "E-commerce API",
    "description": "Built a REST API...",
    "skills_json": ["FastAPI", "PostgreSQL", "Redis"],
    "evidence_text": "GitHub: github.com/user/ecommerce-api",
    "source": "GitHub",
    "created_at": "2026-06-10T10:00:00Z",
    "updated_at": "2026-06-10T10:00:00Z"
  }
  ```
- **Errors:** 401, 422

---

#### `GET /v1/profile/items`

List all career profile items for the authenticated user.

- **Auth:** JWT Bearer required
- **Query params:** `item_type` (optional filter, one of the enum values)
- **Response `200`:**
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "item_type": "project",
        "title": "E-commerce API",
        "skills_json": ["FastAPI", "PostgreSQL"],
        "created_at": "2026-06-10T10:00:00Z"
      }
    ],
    "total": 1
  }
  ```
- **Errors:** 401

---

#### `GET /v1/profile/items/{item_id}`

Get a single career profile item.

- **Auth:** JWT Bearer required
- **Response `200`:** Full item object (same shape as POST 201).
- **Errors:** 401, 403, 404

---

#### `PATCH /v1/profile/items/{item_id}`

Update a career profile item.

- **Auth:** JWT Bearer required
- **Request body (all fields optional):**
  ```json
  {
    "title": "Updated Title",
    "description": "Updated description.",
    "skills_json": ["FastAPI", "PostgreSQL", "Docker"],
    "evidence_text": "Updated evidence.",
    "source": "LinkedIn"
  }
  ```
- **Response `200`:** Updated item object.
- **Errors:** 401, 403, 404, 422

---

#### `DELETE /v1/profile/items/{item_id}`

Delete a career profile item.

- **Auth:** JWT Bearer required
- **Response `204`:** No content.
- **Errors:** 401, 403, 404

---

## E. Error Contract

| Status Code | When |
|---|---|
| `401 Unauthorized` | Missing or invalid JWT Bearer token |
| `403 Forbidden` | Authenticated but not the owner of the resource |
| `404 Not Found` | Resource does not exist, or is owned by another user and should not be revealed |
| `422 Unprocessable Entity` | Validation error — missing required field, invalid enum value, etc. |
| `500 Internal Server Error` | Unexpected server error |

Error response shape (consistent with existing Phase 1–4 contract):

```json
{
  "detail": "human-readable error message"
}
```

For 422, follow FastAPI default validation error shape:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## F. Ownership and Security Rules

- Every application, career profile item, and artifact **must** be scoped by `user_id`.
- `GET /v1/applications`, `GET /v1/profile/items` must return only the authenticated user's rows.
- **403** (not 404) is returned when the resource exists but belongs to a different user, for application-level actions. However, per existing convention, 404 is acceptable when the goal is to not reveal existence to non-owners.
- `attach-analysis`: the `job_id` must belong to the same `user_id` as the application. If the job belongs to a different user, return 403.
- `package/download`: the response must never include raw `storage_key`, JWT, access tokens, or internal storage paths. Only structured `payload_json` is exposed.
- `readiness` endpoint: never expose raw CV text, report paths, or analysis internals beyond the summary fields.

---

## G. Compatibility Notes

- Existing routes (`/v1/auth/*`, `/v1/jobs/*`, `/v1/jobs/{id}/result`, `/v1/jobs/{id}/report`, `/v1/jobs/history`) must not change.
- Phase 5 tables (`applications`, `career_profile_items`, `application_artifacts`) are additive. They reference `users.id` and (optionally) `jobs.id` as foreign keys but do not alter existing tables.
- Analysis job/result structures (Result JSON v2/v3) are reused as-is by the readiness and package endpoints. Phase 5 does not re-implement scoring.
- `best_analysis_job_id` references an existing `jobs` row. The analysis job itself is never duplicated.
- `application_package` artifact stores structured output in `payload_json`. DOCX/PDF export is future work and uses `storage_key` when implemented; `storage_key` is never returned in Phase 5 v1.

---

## H. Frontend Integration Notes

### Expected Pages

| Route | Purpose |
|---|---|
| `/dashboard` | Readiness dashboard — all application statuses |
| `/applications` | Application list |
| `/applications/new` | New application form |
| `/applications/[id]` | Application detail: JD, status, attached analysis, readiness summary |
| `/applications/[id]/package` | Application package view and download |
| `/applications/[id]/cover-letter` | Cover letter draft view |
| `/applications/[id]/interview` | Interview practice flow |
| `/profile` | Career profile overview |
| `/profile/evidence` | Evidence vault CRUD |

### Expected States

| State | Trigger |
|---|---|
| **Loading** | Any API request in flight |
| **Empty** | No applications, no profile items |
| **Error** | 401 → redirect to login; 403/404 → inline error message; 500 → generic error with retry |
| **Draft** | Application created, no analysis attached |
| **No Analysis** | `GET /readiness` returns 404 → show "Attach an analysis job to see readiness" prompt |
| **Generating** | Package generation in progress (`status: "generating"`) |
| **Ready** | Package available → show view/download buttons |

### Auth

All new pages require the user to be logged in (JWT Bearer). Unauthenticated users should be redirected to the login page. There is no guest access_token flow for Phase 5 resources.
