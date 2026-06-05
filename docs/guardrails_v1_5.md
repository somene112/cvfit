# Guardrails v1.5 — AI CV Fit Phase 3

**Version:** 1.5
**Date:** 2026-06-05
**Owner:** Đạt
**Status:** Active — Phase 3

## Purpose

This document extends the Phase 1 and Phase 2 guardrails with Phase 3-specific rules for Result JSON v2, evidence-based feedback, improvement actions, and CV rewrite. It is the authoritative guardrail reference for Phase 3 development and evaluation.

---

## Guardrail Philosophy

> The system must **never fabricate** a skill, experience, company, metric, or certification. The system must **always distinguish** between evidence found in the CV and inference from context. All suggestions must be **conditional**.

---

## 1. Score and Fit Level Guardrails

### 1.1 — No Guarantee Language

The system must **never** produce output containing:

```
"you are guaranteed to be hired"
"you will definitely get the job"
"you are guaranteed an interview"
"this will result in hiring"
"you will definitely be selected"
"guaranteed to pass"
"100% sure to be hired"
```

The system must always say:

```
"fit score is an estimate"
"does not guarantee any hiring outcome"
"the score is based on CV and JD text provided"
"this analysis estimates CV-to-JD fit"
```

Required guardrail notice in every result:

```
"This analysis estimates CV-to-JD fit only and does not guarantee any hiring outcome."
```

### 1.2 — Fit Level Thresholds

Use these thresholds consistently across backend, frontend, report, and evaluation:

| Fit Score | Fit Level | Meaning |
|-----------|-----------|---------|
| `>= 85` | `excellent` | Strong coverage, good evidence |
| `70 – 84.9` | `good` | Good fit, some gaps |
| `50 – 69.9` | `partial` | Some overlap, important gaps |
| `< 50` | `weak` | Limited evidence |

Fit level should **not override** numeric score. If a numeric score is high but critical must-have skills are missing, the `overall.summary` must acknowledge this limitation.

### 1.3 — Low-Fit Cap Rule

A CV with 3 or more missing must-have skills must not produce a fit score >= 70.

```
IF missing must-have skills count >= 3
THEN fit_score MUST be < 70
```

Rationale: A candidate missing most core requirements should not appear competitive.

---

## 2. Missing Skill Guardrails

### 2.1 — Mandatory Wording

When a skill is not found in the parsed CV, the system must say:

```
"not found in the parsed CV"
"evidence was not found in the parsed CV"
```

The system must **NOT** say:

```
"you don't know FastAPI"
"you do not have PostgreSQL experience"
"you lack the skill"
"the candidate doesn't know X"
"you have no experience with X"
```

### 2.2 — Reason Structure

Every missing skill entry must have a `reason` field that:
- Starts from the JD requirement
- States that evidence was not found
- Does not make absolute claims about the candidate's knowledge

Example good reason:
```
"JD requires FastAPI, but FastAPI evidence was not found in the parsed CV."
```

Example bad reason:
```
"The candidate doesn't know FastAPI."
```

### 2.3 — Severity Mapping

| Requirement Type | Severity |
|-----------------|----------|
| `must_have` | `high` or `medium` |
| `nice_to_have` | `medium` or `low` |

---

## 3. Improvement Action Guardrails

### 3.1 — Conditional Wording

Every improvement action suggestion must use conditional wording:

```
"If you have actually used X, add a project bullet describing your experience."
"Only add this if it is true."
"If this reflects your actual work, rewrite the bullet to be more specific."
```

### 3.2 — No Fabrication Instruction

Improvement actions must **never** instruct the user to fabricate:

```
✗  "Add 3 years of FastAPI experience."
✗  "Claim you built a production API for 10M users."
✗  "Say you worked at a big tech company."
✓  "If you have FastAPI experience, describe the API endpoints you built."
✓  "Only add this if it is true."
```

### 3.3 — Guardrail Field

Every improvement action must include a `guardrail` field with at minimum:

```
"Only add this if it is true. Do not invent skills or experience."
```

### 3.4 — Priority Mapping

| Missing Skill Type | Action Priority |
|-------------------|----------------|
| `must_have` | `high` |
| `nice_to_have` | `medium` |
| CV quality issues | `medium` or `low` |

---

## 4. Evidence Guardrails

### 4.1 — Source of Truth

Evidence text must come **only** from:
- Parsed CV text
- Parsed JD text
- Deterministically derived from parser/scorer metadata

Evidence must **never** include:
- Internal file paths
- S3 object keys
- Storage paths
- Access tokens
- Raw full CV text
- Internal system notes

### 4.2 — Evidence IDs

Evidence IDs must follow the naming convention:

```
ev_cv_skill_XXX  — CV skill evidence
ev_cv_resp_XXX   — CV responsibility evidence
ev_jd_skill_XXX — JD skill requirement evidence
ev_jd_resp_XXX  — JD responsibility evidence
legacy_XXX       — Fallback for legacy evidence shapes
```

### 4.3 — Evidence and Match Confidence

When evidence is weak (short snippet, partial match), the evidence `confidence` field must reflect this.

```
Low confidence (0.5–0.65): Short snippet or fuzzy match
Medium confidence (0.65–0.80): Clear match with some uncertainty
High confidence (0.80–1.0): Explicit, specific match
```

---

## 5. CV Rewrite Guardrails (Phase 3.5+)

*These rules apply when CV rewrite is implemented.*

### 5.1 — Source Constraint

Rewrite must **only** use facts already present in the CV. The system must not:
- Invent a company name
- Invent a job title
- Invent years of experience
- Invent metrics or numbers
- Invent a certification
- Invent a technology not present in the CV

### 5.2 — Before/After Mode

Every rewrite must present:
1. The original CV bullet
2. The suggested rewrite
3. A note explaining the change

### 5.3 — Rewrite Prompt Constraint

All rewrite prompts must include:

```
Rewrite only from provided CV facts.
Do not invent skills, employers, metrics, certifications, dates, or experience.
If the CV does not contain evidence for a claim, do not include it.
```

---

## 6. Interview Feature Guardrails (Phase 3.5+)

*These rules apply when interview question generation is implemented.*

### 6.1 — Question Scope

Questions must relate to:
- Skills mentioned in the CV
- Skills mentioned in the JD
- Projects described in the CV
- JD responsibilities

Questions must **never** ask about:
- Gender, age, religion, ethnicity
- Family status
- Political views
- Medical information
- Information not relevant to the job

### 6.2 — Answer Grading

Grading must be based on:
- Clarity of response
- Relevance to question
- Evidence provided
- Confidence level

Grading must **never** consider:
- Age, gender, ethnicity
- Accent or language style
- Non-relevant personal information

---

## 7. Recruiter Feature Guardrails (Phase 4+)

*These rules apply when recruiter-facing features are built.*

### 7.1 — Transparency

Every recruiter-facing page must display:

```
"AI-assisted screening — not a replacement for human evaluation"
```

### 7.2 — No Automated Rejection

The system must not:
- Automatically reject candidates based on score alone
- Use AI score as the sole screening criterion
- Hide the AI-assisted nature of the screening

### 7.3 — Score Interpretation

Recruiter score displays must include context:

```
"Fit score estimates CV-to-JD match based on text analysis.
Does not account for unlisted skills, cultural fit, or interview performance.
Use as one input among many in your hiring process."
```

---

## 8. Privacy and Security Guardrails

*(Carried forward from Phase 1 and Phase 2)*

### 8.1 — Sensitive Key Scrubbing

These keys must never appear in any output (API, report, logs):

```
access_token | access_token_hash | bucket | cv_text | file_path
local_path | object_key | raw_cv_text | report_docx_path
s3_key | secret | storage_path | user_password
```

### 8.2 — Token Handling

- `access_token` must not appear in browser console
- `access_token` must not appear in logs
- `access_token` must not appear in error messages
- JWT must not appear in console.log

### 8.3 — CV/Report Storage

- Raw CV files have TTL (30 days for Phase 1, configurable per lifecycle policy)
- Generated reports have TTL (30 days)
- S3 lifecycle policy must be applied

---

## 9. Guardrail Test Cases

Every guardrail must have a test case verifying compliance:

| Test | Input | Expected Behavior |
|------|-------|-----------------|
| Guarantee language | System output | No match for guarantee patterns |
| Missing skill wording | CV without FastAPI, JD requires FastAPI | Reason contains "not found in parsed CV" |
| Missing skill fabrication | CV without skill | No "you don't know X" phrasing |
| Low-fit cap | CV missing 3+ must-have skills | fit_score < 70 |
| Improvement conditional | Missing skill suggestion | Contains "If you have actually used" |
| Evidence no fabrication | Any result | Evidence from parsed text only |
| Sensitive keys scrubbed | Result with access_token | access_token not in output |
| Conditional rewrite | CV rewrite prompt | Only facts from CV used |

---

## 10. Guardrail Violation Handling

### 10.1 — Detection

Guardrail violations are detected by:
- Automated tests (`test_phase3_scoring_quality.py`)
- Evaluation script pattern checks (`evaluate_scoring_cases.py`)
- Manual QA review (`phase2_manual_qa_checklist.md`)

### 10.2 — Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| Blocker | Could cause user harm or legal risk | Must fix before merge |
| High | Could mislead users about their readiness | Must fix before merge |
| Medium | Could cause confusion | Fix in next sprint |
| Low | Minor wording issue | Fix when convenient |

### 10.3 — Known Blocker Violations

These patterns are **always blockers** and must never appear in any output:

```
"guarantee" + "hired" / "selected" / "interview" in same output
"you don't know" / "you don't have" + skill name
Invented years of experience
Invented company names
Invented metrics or numbers
```

---

## 11. Wording Reference Card

### DO SAY

```
"FastAPI evidence was not found in the parsed CV."
"JD requires PostgreSQL, but evidence was not found."
"If you have actually used Kubernetes, add a bullet describing your cluster experience."
"Only add this if it is true."
"Fit score is an estimate and does not guarantee any hiring outcome."
"Missing evidence means the system did not find support in the parsed CV."
"This analysis estimates CV-to-JD fit."
```

### NEVER SAY

```
"You don't know FastAPI."
"You have no PostgreSQL experience."
"You are guaranteed to be hired."
"Add 3 years of FastAPI experience."
"You worked at Google before."
"Your CV proves you built something for 10M users."
"You should claim this certification."
```

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05 | Initial guardrails (Phase 1/2) |
| 1.5 | 2026-06-05 | Added Phase 3 guardrails: missing skill wording, improvement actions, low-fit cap, evidence IDs, rewrite constraints |

---

*This document is the source of truth for AI CV Fit guardrails. Update before merging Phase 3 features that affect output wording.*
