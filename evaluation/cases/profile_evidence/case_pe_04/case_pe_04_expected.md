# Expected Behavior — Profile Evidence Case 04: Project Evidence with Links

## CV Profile
Web developer with React and JavaScript experience. CV mentions Portfolio Website project.

## JD Profile
Requires JavaScript, React, CSS, HTML5 for frontend developer role.

## Profile Evidence Expected Behavior

### Expected Matches
The profile project "Portfolio Website" should match:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| JavaScript | skills_json, description | ✅ Should match |
| React | skills_json, description | ✅ Should match |
| CSS | skills_json, description | ✅ Should match |
| HTML | skills_json (as HTML5 context) | ✅ Should match |

### has_profile_evidence Expected Values
- `has_profile_evidence.javascript`: **true** (matched via skills_json)
- `has_profile_evidence.react`: **true** (matched via skills_json)
- `has_profile_evidence.css`: **true** (matched via skills_json)

### Link Preservation Expected Behavior
- **source field**: "https://github.com/quocviet-dev/portfolio" should be preserved
- Link should be accessible in output
- Link should NOT be used to fabricate additional content

### Cover Letter Behavior
- Profile evidence can be used for JavaScript and React matching
- Link should be mentioned if relevant to the role
- System should NOT scrape or fetch link content
- System should NOT claim portfolio contains technologies not listed

### Guardrail Checks
- System should NOT read or parse the GitHub URL
- System should NOT claim "portfolio shows X" based on link content
- Link is for reference, not for content generation
- Evidence should come from profile fields, not external URLs
