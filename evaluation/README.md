# AI CV Fit — Evaluation Dataset

## Overview

This folder contains test cases for evaluating the quality and consistency of the AI CV Fit scoring system.

## Structure

```
evaluation/
  README.md              ← this file
  cases/
    easy/                ← 5 cases (high fit, clear alignment)
    medium/              ← 5 cases (partial mismatch, some relevance)
    hard/                ← 5 cases (weak alignment, role mismatch)
    edge/                ← 3 cases (extreme scenarios)
```

## Case Format

Each case has three files:
- `case_XX_cv.txt` — CV text
- `case_XX_jd.txt` — Job description text
- `case_XX_expected.md` — Expected behavior, score range, and guardrail expectations

## Running the Evaluation

```powershell
cd D:\SU26\1_EXE201\Project\Clone\cvfit
python scripts/evaluate_scoring_cases.py
```

## Adding New Cases

1. Create a new folder under `cases/easy/`, `medium/`, `hard/`, or `edge/`
2. Add `case_XX_cv.txt`, `case_XX_jd.txt`, `case_XX_expected.md`
3. Update case numbering sequentially
4. Run the evaluation script to verify

## Case Descriptions

| Case | Category | CV Profile | JD Profile | Expected Score |
|------|----------|-----------|-----------|---------------|
| 01 | Easy | Backend dev with FastAPI, PostgreSQL, Redis, Docker | Backend Engineer with FastAPI, PostgreSQL, Redis, Docker | 70–85 |
| 02 | Easy | Full stack dev with Python, Flask, SQLite | Backend Developer with Python, Flask, SQL | 50–65 |
| 03 | Easy | Data engineer with Python, PostgreSQL, Docker, Kubernetes, GCP | Data Engineer | 68–78 |
| 04 | Easy | Junior dev with Python, Django, SQLite | Backend Developer | 50–65 |
| 05 | Easy | Senior dev with FastAPI, PostgreSQL, Redis, K8s, AWS | Senior Backend Engineer | 68–78 |
| 06 | Medium | Node.js dev, no Python | Backend Engineer (Python) | 50–65 |
| 07 | Medium | Data analyst with Python, pandas, SQL | Backend Engineer (FastAPI) | 48–60 |
| 08 | Medium | Frontend dev with basic Python scripts | Backend Engineer | 42–55 |
| 09 | Medium | DevOps engineer, strong Python, Docker, K8s, no API dev | Backend Engineer | 50–62 |
| 10 | Medium | ML engineer with Python, Flask, Docker | Backend Engineer | 45–58 |
| 11 | Hard | Ultra-vague CV, no specific tech | Senior Backend Engineer | 25–40 |
| 12 | Hard | Vague CV with Java, C++, generic language | Python Backend Engineer | 40–55 |
| 13 | Hard | Overqualified CV, too many irrelevant skills | Mid-Level Backend Engineer | 60–75 |
| 14 | Hard | Brief CV with minimal evidence | Backend Engineer | 50–62 |
| 15 | Hard | Cybersecurity specialist CV | Backend Engineer | 40–52 |
| 16 | Edge | Ultra-short CV (2 sentences) | Senior Backend Engineer | 30–42 |
| 17 | Edge | Ultra-long CV, ultra-short JD | Backend Engineer | 60–72 |
| 18 | Edge | CV listing everything with no evidence | Junior Backend Developer | 50–65 |

## Guardrail Checks

Every case must pass these guardrail checks:

1. **No guarantee language** — output must not contain "guarantee hired", "will be hired", "will get the job", etc.
2. **Missing evidence wording** — missing skills must be phrased as "not found in parsed CV", not "you don't know X"
3. **No fabrication** — no invented skills, companies, years, metrics, certifications
4. **Conditional suggestions** — improvement suggestions must include "Only add this if it is true"
5. **Low-fit cap** — a CV with no relevant skills must not score 70+

## Interpreting Results

The evaluation script compares actual system output against expected ranges. Any case that produces a score outside the expected range, or that fails guardrail checks, is flagged as a **discrepancy** for human review.
