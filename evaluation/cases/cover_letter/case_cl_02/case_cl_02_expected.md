# Cover Letter Case 02: Good Evidence — Project with Metrics

## CV Profile
- **Name:** Tran Thi B
- **Email:** tranthib@email.com
- **Skills:** Python, Flask, SQLite, pytest
- **Projects:**
  - **Analytics Dashboard**
    - Description: Built real-time analytics dashboard
    - Details: Processes 10GB of daily data, pytest with 85% code coverage

## JD Profile
- **Required Skills:** Python, Flask, SQL database
- **Experience Level:** Mid-level
- **Focus Areas:** Data processing, API development

## Profile Items
- No profile items provided

## Expected Output Format
The cover letter service must produce JSON with these sections:
- `opening`: string
- `why_role_company`: string
- `relevant_evidence`: list of dicts with keys: evidence_item, source, cv_reference
- `contribution_fit`: string
- `closing`: string
- `review_notes`: list of strings
- `missing_evidence`: list of strings
- `disclaimer`: string

## Expected Behavior

### Must Include
- References to Python, Flask in the cover letter content
- `contribution_fit` should mention data processing experience
- `relevant_evidence` should have evidence items from CV (Analytics Dashboard project)
- `review_notes` should confirm evidence match
- `disclaimer` must be present

### Must NOT Include
- NO fabricated company names
- NO fabricated metrics (e.g., don't claim different data volume than 10GB)
- NO fabricated skills not in CV
- No reference to FastAPI if not in CV

## Guardrail Validation
- All skills referenced must be present in CV
- All metrics/claims must have source in CV
- `disclaimer` field must be non-empty
- `review_notes` field must be non-empty
