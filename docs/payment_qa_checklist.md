# Payment QA Checklist (Phase 7A)

Test matrix for the Payment MVP. Used by the implementation PRs and the closeout.
Mock the provider where possible; only the final real-payment test uses live payOS.

Production execution references:

- [Production rollout checklist](payment_production_rollout_checklist.md)
- [Real/sandbox payment QA](payment_real_payment_qa.md)
- [Closeout report template](payment_closeout_report.md)
- `scripts/smoke_payment_production_readiness.py` for safe deployed readiness checks

## Backend — billing API

| # | Case | Expected |
| --- | --- | --- |
| 1 | `GET /v1/billing/plans` (auth) | Returns Starter + Pro Demo packs with VND amounts from backend config |
| 2 | Checkout without auth | `401` |
| 3 | Checkout with unknown `plan_code` | `400`/`422`, no order created |
| 4 | Checkout with a client-supplied amount | Amount ignored; server amount used |
| 5 | Valid checkout | `pending` order created with unique `provider_order_code` + `checkout_url` |
| 6 | `GET /v1/billing/orders` | Returns only the caller's orders |
| 7 | Read another user's order by id | `404` (no existence leak) |

## Backend — webhook & credits

| # | Case | Expected |
| --- | --- | --- |
| 8 | Webhook with invalid signature | Rejected; no credits granted |
| 9 | Valid webhook for a `pending` order | Order `paid`; credits granted once |
| 10 | Valid webhook grants the correct credit amounts | Entitlements match plan |
| 11 | Duplicate webhook (same `payload_hash`) | `200`; **no** double grant |
| 12 | Amount mismatch | `manual_review`; no credits |
| 13 | Currency mismatch (non-VND) | `manual_review`; no credits |
| 14 | Webhook for unknown order code | Stored + `manual_review`; no credits |
| 15 | Cancelled order then late webhook | No credits without manual review |
| 16 | Re-deliver webhook after `paid` | Idempotent no-op, `200` |

## Backend — usage & gating

| # | Case | Expected |
| --- | --- | --- |
| 17 | `GET /v1/billing/usage` | Returns free allowance + remaining credits + used-this-month |
| 18 | Usage reflects free + paid credits | Effective availability = free_remaining + remaining_credits |
| 19 | CV analysis | Consumes 1 `analysis` credit (free first, then paid) |
| 20 | Interview answer feedback | Consumes 1 `interview` credit |
| 21 | Cover letter generation | Consumes 1 `cover_letter` credit |
| 22 | Package generation | Consumes 1 `package` credit |
| 23 | Consuming action with zero free + zero paid | Blocked with `insufficient_credits` (`402`/`403`) |
| 24 | Monthly window | Free allowance resets per Asia/Ho_Chi_Minh month |
| 25 | Non-consuming actions (login, view history, view result, download existing report, view profile/evidence, view existing package, view billing, view pricing) | **Never** consume a credit |
| 26 | Existing generated content | Remains accessible regardless of credit balance |

## Frontend

| # | Case | Expected |
| --- | --- | --- |
| 27 | Pricing page renders | Shows both packs with API-provided amounts |
| 28 | Billing page renders | Shows usage + order history for the user |
| 29 | Checkout button | Redirects to `checkout_url` (no amount computed client-side) |
| 30 | Success page | Shows "verifying", polls backend, shows "confirmed" only after `paid` |
| 31 | Cancel page | Adds no credits; offers retry |
| 32 | Insufficient credits | Shows `insufficient_credits_shown` UI linking to `/pricing` |

## Security / privacy

| # | Case | Expected |
| --- | --- | --- |
| 33 | Frontend bundle / storage | No provider API key, checksum key, or client secret |
| 34 | Logs | No JWT, access token, signature, raw webhook payload, `checkout_url`, `DATABASE_URL`, or secret |
| 35 | Analytics | Only `plan_code`, `amount_bucket`, `provider`; no PII/order-code/URL/payload |
| 36 | Ownership | A user can never read another user's orders/usage/entitlements |

## Real payment (final, live payOS)

| # | Case | Expected |
| --- | --- | --- |
| 37 | End-to-end Starter Pack purchase | Real VND paid via VietQR; order `paid`; credits +once |
| 38 | Spend after purchase | One CV analysis decrements an analysis credit |
| 39 | Webhook re-delivery | No second grant |
| 40 | Post-test log/analytics review | No secrets or sensitive payment data leaked |

## Regression (must remain unchanged)

| # | Case | Expected |
| --- | --- | --- |
| 41 | Email/password login | Unchanged |
| 42 | Google login | Unchanged |
| 43 | Phase 6 feature flags | Unchanged |
| 44 | Share Links | Remain OFF |
