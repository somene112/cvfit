# Expected Behavior — Profile Evidence Case 12: Verified Certification

## CV Profile
DevOps engineer with AWS and Kubernetes experience. CV mentions AWS.

## JD Profile
Requires AWS, Docker, Kubernetes for senior DevOps engineer role.

## Profile Evidence Expected Behavior

### Expected Matches
The certification should match multiple JD requirements:

| JD Requirement | Match Source | Expected Result |
|----------------|--------------|-----------------|
| AWS | Certification skills_json | ✅ Strong match |
| Cloud | Certification skills_json | ✅ Related match |
| Docker | CV context | ✅ From CV |
| Kubernetes | CV context | ✅ From CV |

### has_profile_evidence Expected Values
- `has_profile_evidence.aws`: **true** (verified certification)
- `has_profile_evidence.cloud`: **true** (verified certification)
- `has_profile_evidence.ec2`: **true** (in skills_json)
- `has_profile_evidence.s3`: **true** (in skills_json)
- `has_profile_evidence.docker`: **true** (from CV)
- `has_profile_evidence.kubernetes`: **true** (from CV)

### Source Field Preservation
The certification source field should be preserved:
- `"source": "AWS Certification - Certificate ID: AWS-SAA-2024-12345"`
- Source should be accessible in output
- Source provides verification context

### Evidence Strength Assessment
- **AWS**: **Very Strong** — verified certification with specific services
- **EC2, S3, RDS**: **Strong** — explicit in skills_json
- **IAM, VPC**: **Strong** — explicit in skills_json
- **Docker, Kubernetes**: **Strong** — from CV context

### Cover Letter Behavior
- Can reference AWS certification
- Can mention specific services (EC2, S3) from certification
- Should attribute knowledge to certification where applicable
- Can combine certification and CV evidence

### Guardrail Checks
- System should preserve certification source
- System should use specific AWS services from skills_json
- Certification provides verified evidence, should be leveraged
- No fabrication of additional certifications
