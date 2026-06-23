# Payment Security Checklist (Phase 7A)

Payment is security-sensitive. This checklist is the gate every later payment PR
must satisfy. It applies to backend, frontend, logging, analytics, and deployment.

Guiding rule: **the backend is the only authority on amount, paid state, and
credits. The frontend can start and observe a payment, never decide it.**

## Provider secret handling

- [ ] `PAYOS_CLIENT_ID` exists **only** in backend env.
- [ ] `PAYOS_API_KEY` exists **only** in backend env.
- [ ] `PAYOS_CHECKSUM_KEY` exists **only** in backend env.
- [ ] No provider secret is ever sent to the frontend or stored in the browser.
- [ ] No provider secret appears in the repo (docs use **placeholder names only**,
      never real values).
- [ ] No provider secret appears in logs, error messages, or analytics.

## Webhook verification

- [ ] Verify the provider signature on every webhook using `PAYOS_CHECKSUM_KEY`.
- [ ] Reject (do not process) any webhook with an invalid/missing signature.
- [ ] Store a `payload_hash` for each verified event.
- [ ] Dedupe duplicate webhooks via the unique `payload_hash`.
- [ ] Do **not** grant credits twice for the same payment.
- [ ] The webhook amount **and** currency must match the backend order.
- [ ] An unknown order code is handled safely (store event, route to
      `manual_review`); never auto-grant credits for it.
- [ ] Never trust the browser success/return URL as proof of payment.

## Amount validation

- [ ] Amount is determined server-side from plan config at checkout creation.
- [ ] The checkout request body's amount (if any) is ignored.
- [ ] The webhook amount is compared to the stored order amount; mismatch →
      `manual_review`, no credits.

## Currency validation

- [ ] Currency is `VND` on the order and in the webhook.
- [ ] Any non-`VND` currency → `manual_review`, no credits.

## Idempotency

- [ ] `payment_orders.provider_order_code` is unique.
- [ ] `payment_webhook_events.payload_hash` is unique / dedupe-safe.
- [ ] A repeated `paid` webhook is a no-op (returns `200`, grants nothing new).
- [ ] Credit grant and the `pending -> paid` transition happen in **one**
      transaction so a retry cannot partially apply.

## Double-grant prevention

- [ ] Credits are granted exactly once per order, keyed on order state + webhook
      dedupe.
- [ ] `paid -> paid` with a second credit grant is impossible (disallowed transition).
- [ ] Spending credits never drops a balance below zero.

## Ownership checks

- [ ] `GET /v1/billing/orders` returns only the caller's orders.
- [ ] `GET /v1/billing/orders/{id}` enforces ownership.
- [ ] An unknown id or another user's order returns `404` (no existence leak).
- [ ] Usage and entitlements are always scoped to the authenticated user.

## Frontend limitations

- [ ] No provider API key in the frontend.
- [ ] No checksum key in the frontend.
- [ ] No payment amount calculation in the frontend (amounts come from the API).
- [ ] The frontend never marks an order paid.
- [ ] The frontend never grants credits.
- [ ] The frontend may redirect to `checkout_url` and poll backend order status.
- [ ] The success page shows a "verifying" state and waits for backend-confirmed
      `paid`; it shows no credits until the backend confirms.
- [ ] No raw payment details are placed in analytics.

## Logging rules

Never log:

- [ ] JWTs / app access tokens
- [ ] Provider API key / checksum key / client secret
- [ ] Payment signatures
- [ ] Raw webhook payloads (store a hash + minimal audit fields instead)
- [ ] `checkout_url` when it embeds sensitive tokens
- [ ] `DATABASE_URL` or any connection string
- [ ] Passwords or password hashes

Safe to log: order id (UUID), order status, plan_code, a boolean
`signature_valid`, and coarse timing — nothing that identifies the payer or
contains a secret.

## Privacy / analytics rules

Allowed analytics events:

- `pricing_viewed`
- `billing_viewed`
- `checkout_started`
- `checkout_redirected`
- `payment_return_success_viewed`
- `payment_cancel_viewed`
- `payment_confirmed`
- `payment_failed`
- `credits_added`
- `credits_consumed`
- `insufficient_credits_shown`

Safe analytics payload **only**:

- `plan_code`
- `amount_bucket` (e.g. `20k_vnd`, `49k_vnd`) — bucketed, not exact per-user financial data
- `provider` (e.g. `payos`)

Do **not** send in analytics:

- email or any PII
- raw payment order code
- `checkout_url`
- JWT / access token
- webhook payload
- CV / JD text

## Deployment / env checklist

- [ ] Backend env has `ENABLE_BILLING`, `ENABLE_CREDIT_GATING`,
      `PAYMENT_PROVIDER`, `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY`,
      `PAYMENT_RETURN_URL`, `PAYMENT_CANCEL_URL`, `PAYOS_WEBHOOK_URL`,
      `PAYMENT_CURRENCY=VND`.
- [ ] Frontend env has **no** provider secrets (only public return/cancel routes
      live on the frontend domain).
- [ ] The payOS dashboard webhook points at `PAYOS_WEBHOOK_URL` on the backend.
- [ ] Migrations applied; `EXPECTED_ALEMBIC_HEAD` advanced (in the models PR).
- [ ] `ENABLE_BILLING` can be toggled off to disable the feature without a deploy
      rollback.

## Manual real-payment test checklist

- [ ] Create a Starter Pack checkout; confirm a `pending` order and a real
      `checkout_url`.
- [ ] Complete a real small VND VietQR payment.
- [ ] Confirm the webhook arrives, signature verifies, and the order becomes `paid`.
- [ ] Confirm credits are added exactly once (re-deliver the webhook; verify no
      double grant).
- [ ] Confirm one CV analysis decrements an analysis credit.
- [ ] Confirm an amount-mismatch test routes to `manual_review` with no credits.
- [ ] Confirm logs/analytics contain no secrets, tokens, or raw payloads.

## Rollback strategy

- [ ] Set `ENABLE_BILLING=false` to immediately hide all `/v1/billing/*` routes
      (returns `503`) without code rollback.
- [ ] Set `ENABLE_CREDIT_GATING=false` to stop spending/blocking on credits while
      keeping content accessible.
- [ ] Because grants are idempotent and order-keyed, replaying or pausing the
      webhook is safe; no partial/duplicate state results.
- [ ] DB tables are additive — disabling the feature leaves existing rows intact and
      does not affect auth, Phase 6, or already-generated content.
