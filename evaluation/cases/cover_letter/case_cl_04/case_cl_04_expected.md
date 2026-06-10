# Cover Letter Case 04: Good Evidence — Certification and Education Mentioned

## CV Profile
- **Name:** Pham Thi D
- **Email:** phamthid@email.com
- **Skills:** Python, Django, PostgreSQL, AWS
- **Education:** Bachelor of Computer Science
- **Certifications:** AWS Solutions Architect

## JD Profile
- **Required Skills:** Python, Django, AWS
- **Experience Level:** Mid-level
- **Focus Areas:** Backend development, cloud infrastructure

## Profile Items
- Certification: "AWS Solutions Architect" with skills [AWS, Cloud]

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
- Reference to AWS Solutions Architect certification from profile in `relevant_evidence`
- Education can be mentioned in the cover letter content
- `relevant_evidence` should include evidence from the certification
- `contribution_fit` should mention Python, Django, and AWS experience
- `review_notes` should confirm certification and education evidence
- `disclaimer` must be present

### Must NOT Include
- NO fabricated company names
- NO fabricated certifications not in CV
- NO fabricated skills not in CV
- NO claims about other cloud platforms if not in CV

## Guardrail Validation
- All skills referenced must be present in CV
- Certification referenced must be in CV
- `disclaimer` field must be non-empty
- `review_notes` field must be non-empty
