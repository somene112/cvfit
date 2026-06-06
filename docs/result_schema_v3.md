# Result JSON v3 Contract

## Purpose

Result JSON v3 is the planned Phase 4 result contract for the Career Readiness Operating System. It extends Result JSON v2 with improvement actions, safe rewrite suggestions, interview preparation, learning roadmap, and comparison-ready metadata.

This document is a contract only. It does not implement backend or frontend logic.

## Compatibility Rules

- Do not remove or rename existing Result JSON v2 fields.
- v3 fields are additive.
- Existing dashboard, history, report, smoke, and evaluation consumers should continue to work.
- Keep the existing API response envelope for `GET /v1/jobs/{job_id}/result`.
- Keep score aliases required by v2 compatibility:
  - API envelope: `overall_fit_score`
  - Nested result root: `result.fit_score`
  - Nested legacy scores: `result.scores.fit_score`
  - Nested v2/v3 summary: `result.overall.fit_score`
- Keep existing owner JWT and guest `access_token` authorization behavior.
- Do not expose `access_token`, `access_token_hash`, raw CV text, local paths, storage paths, S3 object keys, report paths, or secrets.

Recommended marker:

```json
{
  "schema_version": "3.0",
  "metadata": {
    "contract_version": "result_json_v3",
    "scorer_version": "phase4.result_json_v3"
  }
}
```

## Top-Level Result Fields

The nested `result` object should include the v2 fields plus these v3-ready fields:

- `overall`
- `scores`
- `score_breakdown`
- `matched_skills`
- `missing_skills`
- `evidence`
- `improvement_actions`
- `safe_rewrite_suggestions`
- `interview_prep`
- `learning_roadmap`
- `limitations`
- `metadata`
- `schema_version`

`overall`, `scores`, `score_breakdown`, `matched_skills`, `missing_skills`, `evidence`, `limitations`, and `metadata` already exist in v2 concepts. v3 expands their use but should not change the v2 meaning.

## `improvement_actions`

Concrete action items for improving career readiness against the JD.

Fields:

- `id`: Stable action ID unique inside the result, for example `act_001`.
- `priority`: `high`, `medium`, or `low`.
- `category`: Machine-readable category, for example `missing_skill`, `weak_evidence`, `rewrite`, `metrics`, `formatting`, `interview`, or `learning`.
- `title`: Short user-facing action title.
- `status`: `open`, `resolved`, `still_missing`, or `not_applicable`.
- `linked_skill`: Optional normalized skill or requirement label.
- `linked_evidence`: Evidence IDs that justify the action. Prefer both CV and JD evidence where available.
- `reason`: Evidence-first explanation for why the action exists.
- `safe_suggestion`: Conditional suggestion that avoids fabricated claims.
- `do_not_fabricate`: Required boolean. Must be `true` for actions that could lead to CV content changes.

Rules:

- Actions must be grounded in JD requirements, CV evidence, missing evidence, or parser/scorer metadata.
- Missing evidence must be phrased as missing from the parsed CV, not as proof the user lacks the skill.
- Suggestions must be conditional when adding CV content.
- Status is useful for comparison: a later revision can mark an earlier action `resolved`, `still_missing`, or `not_applicable`.

## `safe_rewrite_suggestions`

Guidance for improving CV wording without inventing facts.

Fields:

- `source_evidence`: CV evidence IDs or the original CV snippet used for the rewrite. Prefer IDs when available.
- `suggested_structure`: A structure or template for a better bullet, using only known facts or placeholders for user confirmation.
- `warning`: User-facing guardrail warning.
- `missing_context_to_confirm`: List of facts the user must confirm before using the suggestion, such as metric, scope, user count, deployment context, or business impact.
- `do_not_fabricate`: Required boolean. Must be `true`.

Rules:

- Do not invent employers, dates, years of experience, metrics, certifications, tools, or project outcomes.
- If a stronger bullet needs missing information, ask the user to confirm it instead of writing it as fact.
- A safe suggestion can be a template, not a finished claim.

## `interview_prep`

Interview questions and answer outlines tied to the JD and CV.

Fields:

- `question`: Interview question.
- `type`: Suggested values: `technical`, `behavioral`, `project_deep_dive`, `gap_probe`, or `system_design`.
- `why_this_question`: Why this is likely or useful based on the JD/CV analysis.
- `related_jd_requirement`: JD requirement text or summary.
- `related_cv_evidence`: CV evidence IDs or snippets that can support the answer.
- `suggested_answer_outline`: Bullets or short sections the user can use to prepare.
- `risk_if_user_cannot_answer`: Honest caveat explaining why the user should prepare this area.

Rules:

- Questions must be job-relevant.
- Do not ask about protected or irrelevant personal information.
- Answer outlines must not invent experience.
- Gap questions should help the user prepare honestly, not encourage false claims.

## `learning_roadmap`

Learning plan for gaps that should not be claimed until completed.

Fields:

- `skill`: Skill or requirement label.
- `priority`: `high`, `medium`, or `low`.
- `why`: Evidence-first explanation tied to the JD and current CV evidence.
- `topics`: Ordered list of topics to learn.
- `mini_project`: Practical project suggestion that could create real CV evidence after completion.
- `estimated_effort`: Human-readable effort estimate, for example `1-2 weekends` or `2-4 weeks`.
- `cv_evidence_to_add_after_learning`: What the user may add only after completing the work.
- `do_not_claim_until_completed`: Required boolean. Must be `true`.

Rules:

- Learning items should not imply the user already has the skill.
- Mini-project suggestions should be realistic and relevant to the JD.
- CV evidence guidance must be future-facing and conditional on completion.

## Full JSON Example

```json
{
  "job_id": "3b8d9a2a-13b8-4c7e-9b53-8a2a6f6f1b4e",
  "overall_fit_score": 76.2,
  "summary": "Good fit with clear Python and FastAPI evidence, but Kubernetes and observability evidence were not found in the parsed CV.",
  "strengths": ["Python", "FastAPI", "PostgreSQL"],
  "missing_skills": ["Kubernetes", "Observability"],
  "recommendations": [
    "If you have actually used Kubernetes, add a truthful project bullet with deployment context."
  ],
  "evidence": [],
  "result": {
    "schema_version": "3.0",
    "job_id": "3b8d9a2a-13b8-4c7e-9b53-8a2a6f6f1b4e",
    "fit_score": 76.2,
    "scores": {
      "fit_score": 76.2,
      "skill_match": 80.0,
      "responsibility_match": 74.0,
      "experience_level": 70.0,
      "project_relevance": 78.0,
      "cv_quality": 82.0
    },
    "overall": {
      "fit_score": 76.2,
      "fit_level": "good",
      "summary": "Good fit with direct backend evidence, but some deployment and monitoring requirements need stronger proof.",
      "confidence": 0.82,
      "guardrail_notice": "This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome."
    },
    "score_breakdown": [
      {
        "key": "skill_match",
        "label": "Skill match",
        "score": 80.0,
        "weight": 0.35,
        "explanation": "Python, FastAPI, and PostgreSQL evidence were found in the parsed CV."
      },
      {
        "key": "responsibility_match",
        "label": "Responsibility match",
        "score": 74.0,
        "weight": 0.3,
        "explanation": "API development responsibilities match, but production monitoring evidence is weaker."
      }
    ],
    "matched_skills": [
      {
        "skill": "FastAPI",
        "requirement_type": "must_have",
        "jd_requirement": "Build backend APIs with Python and FastAPI.",
        "match_type": "direct",
        "confidence": 0.95,
        "cv_evidence_ids": ["ev_cv_001"],
        "jd_evidence_ids": ["ev_jd_001"],
        "notes": "Direct FastAPI evidence was found in the parsed CV."
      }
    ],
    "missing_skills": [
      {
        "skill": "Kubernetes",
        "requirement_type": "nice_to_have",
        "jd_requirement": "Docker and Kubernetes deployment experience is a plus.",
        "severity": "medium",
        "reason": "The JD mentions Kubernetes, but Kubernetes evidence was not found in the parsed CV.",
        "jd_evidence_ids": ["ev_jd_002"],
        "suggestion": "If you have actually used Kubernetes, add a truthful project bullet with cluster, workload, and deployment context. Only add this if it is true."
      }
    ],
    "evidence": [
      {
        "id": "ev_cv_001",
        "source": "cv",
        "kind": "skill",
        "text": "Built backend APIs with Python, FastAPI, PostgreSQL, Redis, and Docker.",
        "normalized_skill": "FastAPI",
        "location": {
          "section": "experience",
          "page": null,
          "line": null
        },
        "confidence": 0.95
      },
      {
        "id": "ev_jd_001",
        "source": "jd",
        "kind": "requirement",
        "text": "Build backend APIs with Python and FastAPI.",
        "normalized_skill": "FastAPI",
        "location": {
          "section": "requirements",
          "line": null
        },
        "confidence": 0.9
      },
      {
        "id": "ev_jd_002",
        "source": "jd",
        "kind": "requirement",
        "text": "Docker and Kubernetes deployment experience is a plus.",
        "normalized_skill": "Kubernetes",
        "location": {
          "section": "nice_to_have",
          "line": null
        },
        "confidence": 0.86
      }
    ],
    "improvement_actions": [
      {
        "id": "act_001",
        "priority": "high",
        "category": "weak_evidence",
        "title": "Strengthen FastAPI impact evidence",
        "status": "open",
        "linked_skill": "FastAPI",
        "linked_evidence": ["ev_cv_001", "ev_jd_001"],
        "reason": "FastAPI evidence exists, but the parsed CV does not show scope, users, latency, reliability, or business impact.",
        "safe_suggestion": "If this reflects your actual work, add one specific FastAPI bullet with endpoint scope, database integration, deployment context, and a real metric you can defend.",
        "do_not_fabricate": true
      },
      {
        "id": "act_002",
        "priority": "medium",
        "category": "missing_skill",
        "title": "Address Kubernetes gap honestly",
        "status": "open",
        "linked_skill": "Kubernetes",
        "linked_evidence": ["ev_jd_002"],
        "reason": "The JD mentions Kubernetes, but Kubernetes evidence was not found in the parsed CV.",
        "safe_suggestion": "If you have actually used Kubernetes, add the cluster, workload, and deployment task you handled. If not, treat this as a learning roadmap item instead of claiming it.",
        "do_not_fabricate": true
      }
    ],
    "safe_rewrite_suggestions": [
      {
        "source_evidence": ["ev_cv_001"],
        "suggested_structure": "Built [type of API] with Python, FastAPI, and PostgreSQL to support [user or business workflow], improving [real metric or outcome].",
        "warning": "Use this only if each bracketed detail is true and can be defended in an interview.",
        "missing_context_to_confirm": ["API purpose", "user or workflow scope", "real metric or outcome"],
        "do_not_fabricate": true
      }
    ],
    "interview_prep": [
      {
        "question": "Can you walk through a FastAPI endpoint you built, including request validation, database access, and error handling?",
        "type": "project_deep_dive",
        "why_this_question": "The JD requires backend API work and the CV contains FastAPI evidence.",
        "related_jd_requirement": "Build backend APIs with Python and FastAPI.",
        "related_cv_evidence": ["ev_cv_001"],
        "suggested_answer_outline": [
          "Describe the endpoint purpose.",
          "Explain request and response models.",
          "Explain database interaction and error handling.",
          "Mention a real deployment or reliability detail if true."
        ],
        "risk_if_user_cannot_answer": "If you cannot explain the implementation, the FastAPI evidence may appear shallow during interview."
      }
    ],
    "learning_roadmap": [
      {
        "skill": "Kubernetes",
        "priority": "medium",
        "why": "The JD lists Kubernetes as a plus, but Kubernetes evidence was not found in the parsed CV.",
        "topics": ["Pods and deployments", "Services", "ConfigMaps and secrets", "Basic rollout and logs"],
        "mini_project": "Deploy a small FastAPI service with PostgreSQL dependency to a local Kubernetes cluster and document the rollout steps.",
        "estimated_effort": "2-4 weeks",
        "cv_evidence_to_add_after_learning": "After completing the project, add a truthful bullet describing the service, deployment steps, and operational issue you solved.",
        "do_not_claim_until_completed": true
      }
    ],
    "limitations": [
      "This analysis is based on parsed CV and JD text and may miss information if parsing was incomplete.",
      "This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome.",
      "Missing evidence means the system did not find support in the parsed CV, not that the candidate definitely lacks the skill."
    ],
    "metadata": {
      "generated_at": "2026-06-06T09:30:00Z",
      "contract_version": "result_json_v3",
      "scorer_version": "phase4.result_json_v3",
      "language": "en",
      "strictness": "balanced",
      "target_role": "Backend Engineer",
      "analysis_group_id": "grp_91d1377b",
      "revision_number": 1,
      "parent_job_id": null,
      "cv": {
        "file_name": "candidate_cv.docx",
        "parsed_confidence": 0.86,
        "skills_detected": ["Docker", "FastAPI", "PostgreSQL", "Python", "Redis"]
      },
      "jd": {
        "role": "Backend Engineer",
        "must_have_skill_groups": [["python"], ["fastapi"], ["postgresql", "mysql"]],
        "nice_to_have_skill_groups": [["kubernetes"]],
        "responsibility_count": 8
      }
    }
  }
}
```

## Frontend Rendering Notes

- Treat v3 sections as optional. Render v2-compatible sections first, then v3 sections when present.
- Use `result.schema_version` to enable v3 sections, but do not hide safe sections only because the marker is missing during transition.
- Preserve the existing score display by reading `overall.fit_score`, `fit_score`, `scores.fit_score`, or API `overall_fit_score` using the established helper order.
- Render `improvement_actions` by priority and status.
- Render `safe_rewrite_suggestions` as templates with warnings, not as one-click CV edits.
- Render `interview_prep` as practice cards grouped by `type`.
- Render `learning_roadmap` as future work. Avoid UI wording that implies the user already has the missing skill.
- Keep guest `access_token` out of visible text, console logs, analytics, and error messages.

## QA And Evaluation Notes

- Add cases where v3 payloads still satisfy v2 consumers.
- Add cases for missing must-have and nice-to-have skills.
- Add cases where a rewrite suggestion must use placeholders instead of invented metrics.
- Add cases where interview prep asks about a real CV skill and a JD gap without inventing experience.
- Add cases where learning roadmap items are future-facing and include `do_not_claim_until_completed`.
- Add privacy checks for sensitive keys and token-like strings.
- Add comparison cases after the comparison endpoint exists.

## Guardrail Notes

- No fabricated experience.
- No fabricated skills.
- No hiring guarantee.
- Evidence-first suggestions.
- Missing evidence must be described as not found in the parsed CV.
- Rewrite suggestions must be conditional and include `do_not_fabricate`.
- Learning roadmap items must not be claimed until completed.
- Interview prep must not invent project details or answer claims.
