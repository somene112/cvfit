# Interview Practice Contract — Phase 5

**Version:** 1.0
**Date:** 2026-06-10
**Owner (backend):** Phúc
**Owner (evaluation/QA):** Đạt
**Status:** Contract only — no implementation in this PR

---

## A. Scope

Phase 5 implements **Interview Practice v2** as a lightweight typed-answer practice flow.

**In scope:**
- Generate interview questions from JD requirements, CV evidence, and analysis result.
- Accept typed answers from the user.
- Score answers on a rubric and return evidence-grounded feedback.
- Store answers and feedback per application.

**Out of scope (Phase 5):**
- Full voice/audio interview.
- Live chat interview engine.
- Real-time interviewer persona.
- Video recording or playback.

This builds on the Interview Prep Pack introduced in Phase 4 (Result JSON v3 `interview_prep` field), but adds a submission and feedback loop tied to the application workspace.

---

## B. Data Model Proposal

> Implementation in Alembic migration PR3. No tables are created in this PR.

### `interview_answers`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | indexed; ownership scope |
| `application_id` | UUID FK → applications | |
| `job_id` | UUID nullable FK → jobs | the analysis job that sourced the questions |
| `question` | text NOT NULL | the question text as generated |
| `answer_text` | text NOT NULL | the user's typed answer |
| `rubric_json` | JSON NOT NULL | scores per rubric dimension |
| `feedback_json` | JSON NOT NULL | structured feedback |
| `created_at` | timestamp | |

---

## C. Endpoints

### `GET /v1/applications/{application_id}/interview/questions`

Generate interview questions for the application. Uses the attached analysis job's JD, CV evidence, missing skills, and existing `interview_prep` from Result JSON v3 if available.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "application_id": "uuid",
    "questions": [
      {
        "question_id": "q_1",
        "question": "Describe a project where you used FastAPI to build a REST API. What challenges did you face?",
        "type": "project_deep_dive",
        "related_jd_requirement": "3+ years FastAPI experience",
        "related_cv_evidence": ["Built REST API for e-commerce platform using FastAPI"],
        "why_this_question": "FastAPI appears in both the JD and your CV evidence."
      },
      {
        "question_id": "q_2",
        "question": "The JD requires Kubernetes experience. How would you approach learning and applying Kubernetes for a production deployment?",
        "type": "gap_probe",
        "related_jd_requirement": "Kubernetes (must-have)",
        "related_cv_evidence": [],
        "why_this_question": "Kubernetes evidence was not found in the parsed CV. This is a must-have JD requirement."
      }
    ],
    "disclaimer": "Questions are generated from your CV, JD, and analysis result. They are practice aids only — real interviewers may ask different questions."
  }
  ```
- **Errors:** 401, 404 (application not found, belongs to another user, or cross-user attached job)

---

### `POST /v1/applications/{application_id}/interview/answers`

Submit a typed answer to a single question. Returns rubric scores and feedback immediately.

- **Auth:** JWT Bearer required
- **Request body:**
  ```json
  {
    "question_id": "q_1",
    "question": "Describe a project where you used FastAPI...",
    "answer_text": "In my e-commerce API project, I used FastAPI to build endpoints for product listing, cart management, and checkout. I faced challenges with async handling..."
  }
  ```
- **Response `201`:**
  ```json
  {
    "answer_id": "uuid",
    "application_id": "uuid",
    "question": "Describe a project where you used FastAPI...",
    "answer_text": "In my e-commerce API project...",
    "rubric": {
      "relevance": 4,
      "specificity": 3,
      "evidence": 4,
      "structure": 3,
      "risk_gap": 1,
      "overall": 3
    },
    "feedback": {
      "strengths": [
        "Answer references a specific project from your CV.",
        "Mentions async handling as a concrete challenge."
      ],
      "missing_evidence": [
        "No mention of scale, load, or production usage.",
        "Challenge description is vague — what specifically was the async issue?"
      ],
      "suggested_improvements": [
        "Add what specific async pattern you used (e.g., background tasks, async DB calls).",
        "Describe an actual outcome: e.g., 'reduced response time from X to Y' if true."
      ],
      "sample_outline": [
        "Situation: e-commerce API project",
        "Task: build product/cart/checkout REST endpoints",
        "Action: used FastAPI async routes + PostgreSQL",
        "Result: describe a real, verifiable outcome"
      ],
      "risk_notes": [
        "If you cannot describe the async issue in detail, be honest about your learning process."
      ],
      "disclaimer": "Feedback is generated from your CV, JD, application workspace, and provided answer. Review before using in a real interview."
    },
    "created_at": "2026-06-10T10:00:00Z"
  }
  ```
- **Errors:** 401, 404, 422

---

### `GET /v1/applications/{application_id}/interview/answers`

List all submitted answers for an application.

- **Auth:** JWT Bearer required
- **Response `200`:**
  ```json
  {
    "application_id": "uuid",
    "answers": [
      {
        "answer_id": "uuid",
        "question": "Describe a project where you used FastAPI...",
        "rubric": {
          "relevance": 4,
          "specificity": 3,
          "evidence": 4,
          "structure": 3,
          "risk_gap": 1,
          "overall": 3
        },
        "created_at": "2026-06-10T10:00:00Z"
      }
    ],
    "total": 1
  }
  ```
- **Errors:** 401, 404

---

## D. Rubric Schema

```json
{
  "relevance": 0,
  "specificity": 0,
  "evidence": 0,
  "structure": 0,
  "risk_gap": 0,
  "overall": 0
}
```

| Dimension | Description | Scale |
|---|---|---|
| `relevance` | Does the answer address the question and JD requirement? | 0–5 |
| `specificity` | Does the answer include specific details (tools, outcomes, context)? | 0–5 |
| `evidence` | Does the answer reference verifiable CV/profile evidence? | 0–5 |
| `structure` | Is the answer structured (e.g., STAR or similar)? | 0–5 |
| `risk_gap` | How much risk does an interview gap pose for this answer? Lower = better. | 0–5 |
| `overall` | Holistic score considering all dimensions | 0–5 |

All dimensions are integers 0–5. `risk_gap` is inverse: 0 means no gap risk, 5 means high gap risk.

Scoring must be deterministic for v1: use rule-based heuristics (keyword matching against CV evidence and JD, structure pattern detection), not a separate LLM scoring call. A separate LLM scoring pass can be added in Phase 6.

---

## E. Feedback Schema

```json
{
  "strengths": [],
  "missing_evidence": [],
  "suggested_improvements": [],
  "sample_outline": [],
  "risk_notes": [],
  "disclaimer": "Feedback is generated from your CV, JD, application workspace, and provided answer. Review before using in a real interview."
}
```

| Field | Type | Description |
|---|---|---|
| `strengths` | list of strings | What the answer does well, grounded in CV evidence |
| `missing_evidence` | list of strings | Evidence from JD/CV that was not addressed in the answer |
| `suggested_improvements` | list of strings | Specific, actionable improvement suggestions |
| `sample_outline` | list of strings | A non-fabricated STAR-style outline using the user's own context |
| `risk_notes` | list of strings | Interview risks if this answer cannot be elaborated on |
| `disclaimer` | string | Always present; exact wording above |

---

## F. Question Generation Rules

- Questions must be derived from: JD requirements, CV evidence, matched/missing skills from the analysis result, and existing `interview_prep` from Result JSON v3 (if available).
- Question types follow the same taxonomy as Phase 4 Interview Prep:
  - `technical` — skills in both CV and JD
  - `behavioral` — soft skills relevant to JD
  - `project_deep_dive` — project evidence in CV matches JD requirement
  - `gap_probe` — skill required by JD but not found in CV
  - `system_design` — senior-level architecture questions
- `project_deep_dive` questions must only be generated when specific project evidence exists in the CV.
- `gap_probe` questions must explicitly state that the skill was not found in the parsed CV.
- Questions must **not** invent claims about user experience.
- If evidence is missing for a topic, the question should ask the user to provide or describe their experience, not assume they have it.
- Maximum 8 questions generated per call. Prioritize must-have JD requirements first.

---

## G. Scoring Rules

- Rubric scores are deterministic/rule-based for v1. No separate LLM scoring call.
- Scores must be explainable: feedback must reference specific parts of the answer and available evidence.
- A weak answer (low `relevance`, `specificity`, `evidence`) must receive:
  - Non-empty `missing_evidence` list
  - Non-empty `suggested_improvements` with concrete guidance
- A strong answer (high scores across dimensions) must still receive:
  - Non-empty `strengths` list
  - At least one polish suggestion in `suggested_improvements`
- `sample_outline` must be derived from the user's own stated context. Never fabricate project names, company names, or metrics in the outline.
- `risk_notes` should indicate what will go wrong in a real interview if the answer cannot be elaborated on.

---

## H. Auth, Ownership, and Error Rules

Same rules as the Application Workspace contract:

- **401** if JWT is missing or invalid.
- **404** if the application does not exist or belongs to another user. Phase 5 backend uses the non-leak convention: cross-user resource access returns 404, not 403, to avoid revealing resource existence.

> PR6A implementation note: `GET /questions` returns **200** (not 404) when no analysis job is attached. The endpoint falls back to generic behavioral questions derived from the application's job title and career profile items. **404 is still returned** if an attached `best_analysis_job_id` resolves to a job owned by a different user (non-leak convention). This deviation from the contract was approved during the PR6A audit.
- **422** for missing required fields or invalid values.

Additional rule: the user cannot read or submit interview answers for another user's application. `application_id` in the path is always validated against the authenticated `user_id`.

---

## I. Test Hooks

Cases Đạt should be able to test in the evaluation skeleton (PR2):

| Case | Expected Behavior |
|---|---|
| **Weak answer** | Low rubric scores; non-empty `missing_evidence` and `suggested_improvements`; `risk_gap` ≥ 3 |
| **Strong answer** | High rubric scores; non-empty `strengths`; at least one polish suggestion |
| **Missing evidence** | Answer references a skill not in CV → `missing_evidence` mentions the gap; `suggested_improvements` asks user to provide real evidence |
| **Unrelated evidence** | Answer references something not in CV or JD → `risk_notes` warns of unverifiable claim; no fabricated confirmation |
| **Another user's application** | `GET /questions`, `POST /answers`, and `GET /answers` return **404** for a different user's application_id (non-leak convention) |
| **Empty profile** | Questions are generated from JD/analysis only; no fabricated evidence; `gap_probe` questions used for CV gaps |
| **Application without attached analysis** | `GET /questions` returns 200 with generic behavioral questions; disclaimer included. (PR6A: 404 was relaxed — see Section H note.) |
