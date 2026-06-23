# Payment MVP / Billing & Credits — Plan (Phase 7A)

| Field | Value |
| --- | --- |
| Feature | Payment MVP / Billing & Credits |
| Phase | 7A |
| Owner | Phúc |
| Provider | payOS / VietQR |
| Model | One-time credit packs (no subscription) |
| Status | Contract/docs only — no payment code in this PR |

> This document is a **plan and contract**. It does not add backend code,
> frontend UI, migrations, provider SDKs, or env secrets. Implementation happens
> in later PRs (see [Recommended implementation order](#recommended-implementation-order)).

## Provider choice — why payOS / VietQR

- **Vietnam-first MVP.** payOS exposes VietQR bank-transfer checkout, which is the
  most familiar and lowest-friction payment method for VN users. No card needed.
- **Simple integration surface.** payOS uses a hosted `checkout_url` plus a signed
  webhook — a good fit for a small team and a security-sensitive first launch.
- **Server-verifiable.** Payment confirmation arrives via a signed webhook that the
  backend verifies with a checksum key; the frontend never decides payment state.
- **Deferred alternatives.** Stripe / MoMo / VNPAY are explicitly out of scope for
  the MVP and can be added later behind the same internal billing contract.

## MVP principle

- **Real payment** — actual VND charged via payOS/VietQR. No simulated "paid" state.
- **Safe webhook confirmation** — credits are granted **only** after a verified
  webhook. Never from the browser success URL.
- **No fake paid state** — the success/return page shows a "verifying" state and
  polls backend order status; it never marks an order paid.
- **No subscription** — one-time credit packs only.
- **Secrets backend-only** — provider client ID / API key / checksum key live in
  backend env exclusively, never shipped to or stored by the frontend.
- **Existing generated content stays accessible** — gating applies to *new*
  credit-consuming generations only. Already-generated analyses, reports, packages,
  and cover letters remain viewable/downloadable regardless of credit balance.

## Scope

In scope for Phase 7A:

- Pricing page
- Billing page
- Payment orders
- Payment webhook (payOS)
- Credit grants
- Credit usage / gating
- QA closeout

## Out of scope

- Subscriptions / recurring billing
- Refund UI
- Manual reconciliation UI (a docs/checklist process only)
- Stripe / MoMo / VNPAY providers
- Admin billing dashboard
- Automatic tax / invoice system

## Plans

Amounts are authoritative on the **backend** (`plan config`). The frontend only
displays values returned by `GET /v1/billing/plans` and must never compute or send
an amount.

### Starter Pack — `starter_pack`

- Price: **20,000 VND**
- Grants:
  - +10 analysis credits
  - +20 interview credits
  - +5 cover_letter credits
  - +5 package credits

### Pro Demo Pack — `pro_demo_pack`

- Price: **49,000 VND**
- Grants:
  - +30 analysis credits
  - +60 interview credits
  - +15 cover_letter credits
  - +15 package credits

## Free allowance

Resets monthly per the **Asia/Ho_Chi_Minh** timezone (month window is computed in
ICT, not UTC).

| Action | Free per month |
| --- | --- |
| CV analysis | 3 |
| Interview answer feedback | 10 |
| Cover letter | 2 |
| Application package | 2 |

Effective allowance for a credit type = remaining free allowance for the current
ICT month **plus** any purchased credits of that type.

## Credit-consuming actions

| Action | Credit type | Cost |
| --- | --- | --- |
| 1 CV analysis | `analysis` | 1 |
| 1 interview answer feedback | `interview` | 1 |
| 1 cover letter generation | `cover_letter` | 1 |
| 1 application package generation | `package` | 1 |

## Non-consuming actions (must never charge a credit)

- login / register
- view dashboard
- view history
- view an existing result
- download an already-generated report
- view learning tasks
- view profile / evidence vault
- view an existing application package
- view billing
- view pricing

## Critical payment rules

- Do **not** trust a frontend-supplied amount.
- Do **not** grant credits from the success/return URL.
- Grant credits **only** from a verified webhook / payment confirmation.
- Verify the webhook signature.
- Validate the order code (must match a known backend order).
- Validate the amount (must match the backend order amount).
- Validate the currency = `VND`.
- Avoid double credit grant on duplicate webhook (idempotency).
- A user cannot view another user's billing orders.
- Provider secrets exist only in backend env.
- The frontend never stores the provider API key / checksum key.
- The frontend never calculates the amount, marks an order paid, or grants credits.
- The frontend may redirect to `checkout_url` and poll backend order status.

## Recommended implementation order

1. Docs / API contract (this PR).
2. Backend plan config + DB models (`payment_orders`, `user_entitlements`,
   `usage_events`, `payment_webhook_events`).
3. Checkout creation API (`POST /v1/billing/checkout`).
4. Webhook verification + idempotency (`POST /v1/billing/webhooks/payos`).
5. Credit granting (applied transactionally inside webhook handling).
6. Usage endpoint (`GET /v1/billing/usage`) + credit gating helpers.
7. Frontend pricing / billing pages.
8. Credit gating wired into the four consuming actions.
9. Real payment test (small live VND payment end to end).
10. Payment closeout (QA report + ops checklist).

## Minimal demo script

1. Login.
2. Open billing.
3. Open pricing.
4. Choose Starter Pack.
5. Redirect to payOS checkout.
6. Complete VietQR payment.
7. Return to success page.
8. Success page shows "verifying" state (polls backend order status).
9. Order status becomes `paid` (after verified webhook); page shows "payment confirmed".
10. Billing credits increase.
11. Run one CV analysis.
12. Analysis credit decreases by 1.
13. Payment history shows the completed order.

## Definition of Done (Phase 7A overall, across PRs)

- All five docs merged and reviewed.
- `payment_orders`, `user_entitlements`, `usage_events`, `payment_webhook_events`
  implemented with the constraints in [billing_api_contract.md](billing_api_contract.md).
- Checkout creates a `pending` order with a server-determined amount.
- Webhook verifies signature, validates amount + currency + order code, is
  idempotent, and grants credits exactly once.
- Usage endpoint returns free allowance + remaining credits + used-this-month.
- The four consuming actions enforce gating; non-consuming actions never charge.
- Existing generated content remains accessible regardless of credit balance.
- One real VND payment completed end to end (see
  [payment_qa_checklist.md](payment_qa_checklist.md)).
- Security checklist in [payment_security_checklist.md](payment_security_checklist.md)
  fully satisfied; no secrets in frontend, logs, or docs.
- Existing email/password + Google login, and all Phase 6 flags, unchanged.
  Share Links remain OFF.
