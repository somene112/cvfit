# Payment Real/Sandbox Payment QA

This is a manual operator script. Use only an authorized controlled test user and
the payOS account mode approved for the test. Never include real customer data,
credentials, signatures, full checkout URLs, or provider payloads in evidence.

## Evidence to capture

For each test, record only:

- UTC/ICT timestamp and deployed commit IDs;
- plan code and expected backend-owned amount;
- app payment order UUID (not a provider secret);
- status transitions and relevant HTTP status codes;
- before/after credit counts by type;
- webhook result as `applied`, `duplicate`, `manual_review`, or `rejected`;
- redacted screenshot or note proving the expected frontend state;
- issue reference, if any.

Do not capture the full `checkout_url`, real user email, QR contents, bank
details, provider credentials, payment signature, or raw webhook body.

## Expected states and pages

Backend order states:

- `pending`: checkout exists; payment is not confirmed.
- `paid`: verified webhook applied and credits were granted exactly once.
- `manual_review`: order/provider data did not safely match; no automatic grant.
- `failed`, `cancelled`, or `expired`: no verified successful payment/grant.

Frontend pages:

- `/pricing`: plans and backend-provided VND amounts.
- `/billing`: usage and owned order history.
- `/billing/success`: verifies by polling; return URL alone is not success.
- `/billing/cancel`: states that no credits were added.

## Starter Pack manual test

1. Record starting credit balances for the controlled test user.
2. Open `/pricing`; verify `starter_pack`, 20,000 VND, and displayed credits.
3. Start checkout; record the app order UUID and confirm `pending`.
4. Confirm the hosted provider page opens without recording its full URL.
5. Complete the explicitly authorized real or sandbox payment manually.
6. Return to `/billing/success`; observe verifying until backend confirmation.
7. Confirm order becomes `paid` only after the verified webhook.
8. Confirm credits increase by analysis 10, interview 20, cover letter 5, and
   package 5 exactly once.
9. Confirm `/billing` shows the paid order without exposing provider secrets.

## Pro Demo Pack manual test

Repeat the Starter procedure for `pro_demo_pack` and verify:

- backend-owned amount is 49,000 VND;
- order transitions `pending` to `paid` only through the webhook;
- credits increase by analysis 30, interview 60, cover letter 15, and package 15;
- no Starter order or entitlement is modified.

## Cancel and non-success states

- Cancel one checkout and confirm `/billing/cancel` adds no credits.
- Allow an approved test link to expire, if practical, and confirm no grant.
- Record provider failures only as safe status/error categories.
- Exercise `manual_review` only with an approved non-production fixture or
  provider test facility; never alter a production order manually.

## Duplicate webhook/idempotency

If the provider dashboard supports safe resend:

1. Record the paid order's credit balances.
2. Resend the same verified event through the provider facility.
3. Confirm HTTP handling succeeds and the audit event is duplicate/idempotent.
4. Confirm order remains `paid` and all credit balances are unchanged.

If resend is unavailable, mark this manual case not run and cite automated
webhook idempotency tests; do not construct or sign a production webhook locally.

## Credit-gating observations

- Free monthly allowance is spent before purchased credits.
- Purchased usage does not reset at a month boundary.
- Exhausted credit type returns HTTP `402` and safe pricing guidance.
- Read-only history/results/downloads remain accessible.
- Usage events contain identifiers, type, source, quantity, and timestamps only.

## Controlled test-user cleanup

Do not delete payment audit records or entitlements. Sign out the controlled test
user, remove locally stored test artifacts/tokens, revoke temporary operator
access if granted, and document any retained test balances for reconciliation.
