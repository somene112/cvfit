# Guardrails v2 Draft

## Purpose

Guardrails v2 is the planned Phase 4 safety contract for the Career Readiness Operating System. It extends Phase 3 guardrails to cover improvement actions, safe rewrite suggestions, interview prep, learning roadmap, re-analysis, comparison, keyword stuffing detection, and privacy.

This document is a draft contract only. It does not implement backend logic, frontend logic, tests, or scripts.

## Core Rules

### No Fabricated Experience

The system must never invent:

- Employers.
- Job titles.
- Dates.
- Years of experience.
- Project ownership.
- Production usage.
- User counts.
- Revenue, cost, latency, uptime, or other metrics.
- Certifications.
- Awards.

Safe wording:

```text
If this reflects your actual work, add the deployment context and a real metric you can defend.
```

Unsafe wording:

```text
Add that you improved latency by 40%.
```

### No Fabricated Skill

The system must not tell the user to claim a skill that was not found in the parsed CV.

Safe wording:

```text
Kubernetes evidence was not found in the parsed CV. If you have actually used Kubernetes, add a truthful project bullet. If not, treat it as a learning gap.
```

Unsafe wording:

```text
Add Kubernetes to your skills section so the JD matches better.
```

### No Hiring Guarantee

The system must never guarantee an interview, selection, offer, or hiring outcome.

Required concept:

```text
This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome.
```

Unsafe wording:

```text
After these changes, you will get selected.
```

## Evidence-First Action Generation

Every improvement action should be tied to at least one of:

- JD requirement evidence.
- CV evidence.
- Missing evidence from the parsed CV.
- Deterministic parser/scorer metadata.

Action reasons should explain:

- What the JD asks for.
- What the parsed CV supports.
- What evidence was not found.
- What the user can safely do next.

Safe action:

```text
JD requires FastAPI. FastAPI evidence was found, but scope and impact were not found in the parsed CV. If this reflects your actual work, add endpoint scope, database context, and a real outcome.
```

Unsafe action:

```text
Say you built high-scale FastAPI services.
```

## Safe Rewrite Rules

Safe rewrite suggestions must:

- Use only facts already present in the parsed CV, or use placeholders for facts the user must confirm.
- Show the source evidence or source evidence IDs.
- Include a warning that unconfirmed details must not be used.
- Include `do_not_fabricate: true` in structured output.
- Avoid making weak evidence sound stronger than it is.

Safe structure:

```text
Built [type of API] with Python and FastAPI for [workflow], improving [real metric]. Only use bracketed details that are true.
```

Unsafe rewrite:

```text
Built a production FastAPI platform serving 1M users with 99.9% uptime.
```

## Interview Prep Caveats

Interview prep should:

- Ask job-relevant questions tied to JD requirements and CV evidence.
- Include why the question matters.
- Include related JD requirement and CV evidence.
- Provide an answer outline, not a fabricated answer.
- Warn when the user may be weak on a topic.

Interview prep must not:

- Invent projects or achievements for the user.
- Encourage memorized false answers.
- Ask about protected or irrelevant personal information.
- Treat inability to answer as a hiring guarantee or rejection guarantee.

Safe wording:

```text
If you cannot explain this project in detail, prepare by reviewing the actual implementation and be honest about your role.
```

Unsafe wording:

```text
Tell the interviewer you owned the whole system.
```

## Learning Roadmap Caveats

Learning roadmap items should:

- Clearly mark skills as future learning when evidence was not found.
- Include topics, a mini-project, estimated effort, and what CV evidence can be added after completion.
- Include `do_not_claim_until_completed: true` in structured output.

Learning roadmap items must not:

- Imply the user already has the missing skill.
- Tell the user to add the skill before doing the work.
- Present learning completion as a hiring guarantee.

Safe wording:

```text
After completing the Kubernetes mini-project, add a truthful bullet describing the deployment steps and issue you solved.
```

Unsafe wording:

```text
Add Kubernetes now and learn it before the interview.
```

## Keyword Stuffing Warning Rules

Keyword stuffing detection should warn when the revised CV appears to add JD keywords without meaningful evidence.

Warning signals:

- Repeated exact JD keywords in a skills list with no project, work, or education context.
- Large CV length increase without new evidence snippets.
- New matched skills that appear only as comma-separated keywords.
- Repeated technology names without action verbs, responsibilities, or outcomes.
- Skills added in the revised CV that the user cannot support in interview prep.

Warnings should not automatically accuse the user of dishonesty. Phrase as evidence quality risk.

Safe warning:

```text
The revised CV mentions Kubernetes several times, but no project or responsibility evidence was found. Add truthful context if you have it; otherwise keep it as a learning goal.
```

Unsafe warning:

```text
You are lying about Kubernetes.
```

## Re-analysis And Comparison Guardrails

Re-analysis:

- Original jobs remain immutable.
- Revised jobs are linked by `parent_job_id`, `analysis_group_id`, and `revision_number`.
- New results must not mutate old results.
- Guest re-analysis requires a valid parent access token.
- Logged-in re-analysis requires ownership or allowed access.

Comparison:

- Score delta must be explained with evidence delta.
- Resolved gaps require real evidence, not repeated keywords.
- New evidence must come from parsed revised CV text.
- If the JD changed, the comparison must say the before/after is not a pure CV-only comparison.
- Comparison must not fabricate claims or infer work the user did not state.

## Token, Privacy, And Logging Rules

Never expose these values in API responses, reports, logs, docs, browser console, analytics, or error messages:

```text
access_token
access_token_hash
Authorization
Bearer
JWT
password
password_hash
raw_cv_text
cv_text
storage_path
report_docx_path
local_path
file_path
s3_key
object_key
bucket
secret
```

Rules:

- Do not log full URLs containing `access_token`.
- Redact query strings before printing request URLs.
- Prefer passing guest tokens in safer request fields for new multipart endpoints, while preserving compatibility only when needed.
- Do not include raw full CV text in result JSON, comparison output, or DOCX report.
- Evidence snippets should be short and relevant.
- Do not include internal paths, S3 keys, or report paths in evidence or metadata.

## Safe Vs Unsafe Wording Reference

| Scenario | Safe | Unsafe |
| --- | --- | --- |
| Missing skill | `Docker evidence was not found in the parsed CV.` | `You do not know Docker.` |
| Add skill | `If you have actually used Docker, add a truthful project bullet.` | `Add Docker so your CV matches the JD.` |
| Rewrite | `Use this structure only with facts you can confirm.` | `Say you improved performance by 50%.` |
| Interview | `Prepare to explain the actual project and your role.` | `Tell them you led the project.` |
| Learning | `Do not claim this skill until you complete the project.` | `Add it now and learn it later.` |
| Comparison | `The new CV mentions Kubernetes, but project evidence was not found.` | `The gap is resolved because Kubernetes appears five times.` |
| Hiring outcome | `The score is an estimate and does not guarantee any hiring outcome.` | `This will guarantee an interview.` |

## Evaluation Expectations

Guardrails v2 should be backed by tests and evaluation cases in later PRs:

- No guarantee language.
- Missing skill wording uses `not found in the parsed CV`.
- Improvement actions include conditional wording.
- Rewrite suggestions do not invent metrics or employers.
- Interview prep answer outlines do not fabricate claims.
- Learning roadmap items include future-facing caveats.
- Keyword stuffing warnings detect repeated unsupported keywords.
- Comparison requires evidence quality for resolved gaps.
- Sensitive keys and token-like strings are scrubbed.
