# Phase 5 Demo Checklist

> **Created:** 2026-06-10
> **Last Updated:** 2026-06-16
> **Phase:** Phase 5 — Application Readiness Suite
> **Owner:** Đạt (QA/Evaluation/Guardrails)

---

## Overview

This checklist covers everything needed to run a successful Phase 5 demo. Complete each section **before the demo day** and verify **on demo day** before presenting.

---

## Pre-Demo — 1 Day Before

### Environment Setup
- [ ] Backend smoke test passes locally
- [x] Frontend builds successfully (`cd frontend && npm run build`) — confirmed PASS 2026-06-16
- [ ] All Phase 5 API endpoints respond correctly (test with curl or Postman)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] No errors in backend logs on startup

### Demo Data Setup
- [ ] Demo user account created and credentials ready
- [ ] Sample CV uploaded to demo account
- [ ] Sample JD pasted in a test application
- [ ] At least 1 completed analysis attached to an application
- [ ] At least 1 career profile item (skill, project, or achievement)
- [ ] Sample interview questions generated
- [ ] Sample cover letter generated

### Demo Script
- [ ] Demo script written and rehearsed at least 2 times
- [ ] Demo flow is linear (no unexpected navigation required)
- [ ] All steps have backup screenshots if live demo fails
- [ ] Timer set — demo should be under 15 minutes

### Code Hygiene
- [ ] No JWT tokens or API keys in code
- [ ] No real CV/report data committed to repo
- [ ] No `console.log` statements leaking tokens in frontend
- [ ] Backend logs do not contain CV raw text
- [ ] All error messages are user-friendly (not stack traces)

---

## Demo Flow Checklist

### 1. Authentication
- [ ] Navigate to login page
- [ ] Login with demo user credentials
- [ ] Dashboard loads after login
- [ ] Logout works correctly
- [ ] Unauthenticated access redirects to login

### 2. Application Workspace (Pillar 1)
- [ ] Click "New Application" or similar button
- [ ] Enter job title (e.g., "Backend Engineer")
- [ ] Enter company name (optional)
- [ ] Paste job description text
- [ ] Submit and see application appear in list
- [ ] Application shows correct job title and company
- [ ] Application status is "draft" initially

### 3. Analysis Attachment
- [ ] Open application detail
- [ ] Attach an existing analysis job to this application
- [ ] Best analysis is highlighted or selected
- [ ] Application status updates after attachment

### 4. Cover Letter (Pillar 3)
- [ ] Click "Generate Cover Letter" in application detail
- [ ] Cover letter generates without error
- [ ] Cover letter displays with all sections:
  - [ ] Opening paragraph
  - [ ] Why this role/company
  - [ ] Relevant evidence
  - [ ] Contribution fit
  - [ ] Closing
- [ ] Disclaimer is visible
- [ ] Review notes are visible
- [ ] No fabricated company names (unless company_name was provided)
- [ ] No fabricated skills not in CV
- [ ] No fabricated metrics not in CV or profile

### 5. Interview Practice (Pillar 4)
- [ ] Navigate to interview practice section within application
- [ ] View interview questions (at least 3 shown)
- [ ] Each question shows:
  - [ ] Question text
  - [ ] Question type (technical, behavioral, etc.)
  - [ ] Why this question
  - [ ] Related JD requirement
  - [ ] Suggested answer outline
- [ ] Submit a sample answer
- [ ] Feedback displays after submission
- [ ] Feedback references the JD requirement
- [ ] Feedback references CV or profile evidence
- [ ] Feedback does NOT fabricate evidence

### 6. Career Profile / Evidence Vault (Pillar 5)
- [ ] Navigate to Profile page
- [ ] Add a new skill item (e.g., "Docker")
- [ ] Add a new project item (e.g., "E-Commerce API")
- [ ] Add a new achievement item (e.g., "Reduced load time by 40%")
- [ ] All items appear in the profile list
- [ ] Edit an existing item — changes save correctly
- [ ] Delete an item — item is removed
- [ ] Ownership check: user cannot see another user's profile items

### 7. Application Package (Pillar 2)
- [ ] Navigate to application detail
- [ ] Click "Generate Package"
- [ ] Package generates without error
- [ ] Package displays all 7 sections:
  - [ ] Readiness summary (level + score)
  - [ ] Best CV analysis
  - [ ] Cover letter draft (if generated)
  - [ ] Interview prep pack (questions)
  - [ ] Learning roadmap (items)
  - [ ] Evidence checklist (skills with evidence status)
  - [ ] Disclaimer
- [ ] Readiness level is correct based on fit score
- [ ] Evidence checklist shows has_profile_evidence status

### 8. Readiness Dashboard (Pillar 6)
- [ ] Dashboard shows all created applications
- [ ] Each application shows readiness level
- [ ] Fit scores are visible
- [ ] Application status is visible
- [ ] User can see which applications are "ready_to_apply"

---

## Guardrail Verification (During Demo)

### Cover Letter Guardrails
- [ ] Cover letter does NOT say "I guarantee I will get hired"
- [ ] Cover letter does NOT fabricate company names (unless provided)
- [ ] Cover letter does NOT fabricate skills not in CV
- [ ] Cover letter does NOT fabricate metrics not in evidence
- [ ] Disclaimer is present and visible
- [ ] Review notes are present

### Interview Practice Guardrails
- [ ] Feedback does NOT fabricate evidence not in CV
- [ ] Feedback does NOT say "you will definitely get hired"
- [ ] Feedback references the JD requirement
- [ ] Feedback references actual CV/profile evidence
- [ ] Feedback is specific to the user's answer

### Career Profile Guardrails
- [ ] Profile items are owned by the user who created them
- [ ] User cannot see another user's profile items
- [ ] Profile items validate item_type is a valid enum value

### Application Package Guardrails
- [ ] Package disclaimer is present
- [ ] Package does not fabricate skills
- [ ] Readiness score is derived from analysis (not new scoring)

---

## Ownership / Security Checks

- [ ] User A cannot see User B's applications
- [ ] User A cannot see User B's profile items
- [ ] User A cannot see User B's interview answers
- [ ] User A cannot modify User B's application package
- [ ] Wrong JWT token returns 401
- [ ] Missing JWT token returns 401
- [ ] Application access without attachment returns appropriate error

---

## Post-Demo

- [ ] No JWT leaked in demo screenshots
- [ ] No real user data in demo screenshots
- [ ] All errors encountered during demo are documented
- [ ] Critical bugs found during demo are filed as issues
- [ ] Demo script updated with any fixes needed
- [ ] Render smoke test passes after demo

---

## Smoke Test Commands

Run these commands before demo day:

```bash
# Backend local smoke
cd D:/SU26/1_EXE201/Project/Clone/cvfit
python scripts/smoke_test_local.py

# Backend tests
cd backend && python -m pytest --basetemp pytest-cache-files-local -p no:cacheprovider -q

# Frontend build
cd frontend && npm install && npm run build

# Cover letter evaluation
python scripts/evaluate_cover_letter_cases.py

# Application package evaluation
python scripts/evaluate_application_package.py
```

---

## Demo Data Template

Use this template for demo user data:

```
Email: demo@cvfit.app
Password: Demo123!

Sample CV:
- Name: Nguyen Van A
- Skills: Python, FastAPI, PostgreSQL, Redis, Docker
- Project: E-Commerce Product API (FastAPI, PostgreSQL, Redis)

Sample JD:
- Backend Engineer
- FastAPI, PostgreSQL, Redis, Docker required
- 2+ years Python
```

---

## Known Issues (Update before demo)

> Fill in any known issues here before the demo:

| Issue | Severity | Workaround |
|-------|---------|-----------|
| Analysis-backed package/cover-letter smoke not yet recorded | MEDIUM | Requires succeeded analysis job; do before demo |
| `evaluate_interview_practice.py` blocked locally (sentence_transformers) | LOW | CI evidence required; does not block demo |
| GA4 analytics not implemented | INFO | Explicitly deferred; not required for Phase 5 |
| Demo checklist not yet executed | HIGH | Team must execute this checklist before demo day |

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Backend | Phúc | — | — |
| Frontend | Quân | — | — |
| QA | Đạt | — | — |
