# Expected Behavior — Profile Evidence Case 16: Profile with Links Preserved

## CV Profile
Frontend developer with React, JavaScript, TypeScript experience. CV is detailed and complete.

## JD Profile
Requires JavaScript, React, TypeScript, CSS for senior frontend developer role.

## Profile Evidence Expected Behavior

### Link Item Analysis
Profile has a link item with empty skills_json:

| Field | Value | Expected |
|-------|-------|----------|
| item_type | "link" | ✅ Should be recognized |
| title | "GitHub Profile" | ✅ Should be preserved |
| source | "https://github.com/..." | ✅ Should be preserved |
| skills_json | [] | Empty — no direct matches |

### has_profile_evidence Expected Values
Based on link with empty skills_json:
- `has_profile_evidence.javascript`: **false** (no skills_json match)
- `has_profile_evidence.react`: **false** (no skills_json match)
- `has_profile_evidence.typescript`: **false** (no skills_json match)

Evidence comes from CV, not link profile item.

### Link Preservation Expected Behavior
The link should be preserved in output:

**SHOULD:**
- ✅ Preserve the GitHub URL in output
- ✅ Keep the link item in profile evidence
- ✅ Reference the link for portfolio context
- ✅ Use link title "GitHub Profile" where appropriate

**SHOULD NOT:**
- ❌ Fetch or scrape the GitHub URL
- ❌ Parse GitHub projects from URL
- ❌ Claim specific projects from link content
- ❌ Fabricate additional projects

### No Content Fabrication from Links
Critical rule for link items:

**MUST NOT:**
- ❌ Say "your 10 React projects show..."
- ❌ Reference specific projects from GitHub
- ❌ Parse or read link content
- ❌ Claim link contains specific technologies

**MUST:**
- ✅ Keep link as reference/portfolio mention
- ✅ Use only description text, not link content
- ✅ Be transparent that link is for reference
- ✅ Not fabricate content from external URLs

### Cover Letter Behavior
- Can mention "portfolio available on GitHub"
- Should NOT claim to know specific projects from link
- Link is for recruiter to explore, not system to use
- System should not fabricate link content

### Guardrail Checks — Link Content
- System should NOT fetch or parse external URLs
- Link is metadata, not evidence source
- Description text can be used, link content cannot
- Evidence must come from profile fields, not link scraping
