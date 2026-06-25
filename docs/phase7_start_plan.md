# Phase 7 Start Plan — Controlled Payment Rollout & Go-To-Market Readiness

> This is a plan only. Do **not** begin until
> `docs/phase7_preflight_closeout.md` is marked `READY_TO_START_PHASE_7`. Do not
> enable credit gating before the payment webhook has been verified. Never paste
> secret values into chat or docs — only set them in the Render backend env.

## 1. Phase 7 goal

- **Controlled payment rollout** of the existing payOS credit-pack MVP.
- **Go-to-market readiness** (verified checkout → webhook → credit grant).
- **Not** a broad feature expansion, redesign, subscriptions, or admin billing UI.

## 2. Preconditions (all must hold)

- PR #87 / #88 / #89 merged to `main`.
- Phase 7 preflight **local validation passed** (compile, targeted tests, lint,
  build, privacy audit).
- Latest backend **and** frontend `main` **deployed** to Render.
- **Manual production QA passed** (the section 6 checklist in the preflight doc).
- `ADMIN_EMAILS` configured for the admin demo account.
- Before rollout: `ENABLE_BILLING=false` and `ENABLE_CREDIT_GATING=false`.

## 3. Phase 7A — payOS environment readiness

Set in **Render backend env only** (never in chat/docs/frontend; values are secrets):

- `PAYOS_CLIENT_ID` = (secret — set in Render only)
- `PAYOS_API_KEY` = (secret — set in Render only)
- `PAYOS_CHECKSUM_KEY` = (secret — set in Render only)

Non-secret config (safe to set as shown):

- `PAYMENT_PROVIDER=payos`
- `PAYMENT_CURRENCY=VND`
- `PAYMENT_RETURN_URL=https://cvfit-frontend.onrender.com/billing/success`
- `PAYMENT_CANCEL_URL=https://cvfit-frontend.onrender.com/billing/cancel`
- `PAYOS_WEBHOOK_URL=https://cvfit.onrender.com/v1/billing/webhooks/payos`

payOS dashboard:

- Configure the provider webhook to
  `https://cvfit.onrender.com/v1/billing/webhooks/payos`.
- Do not paste provider secrets into chat or docs.

## 4. Phase 7B — enabled smoke

- Set `ENABLE_BILLING=true`.
- Keep `ENABLE_CREDIT_GATING=false`.
- Redeploy backend.
- Run the enabled smoke with an `AUTH_TOKEN` — **do not print the token**.
- Expected: checkout creates a **pending** order and reports a redacted
  `checkout_url_present=true` (the URL itself is never logged/printed).
- No real payment is performed by the smoke.

## 5. Phase 7C — manual checkout / cancel QA

- Open `/pricing`.
- Start a checkout for a pack.
- Confirm the payOS provider page opens.
- Use the cancel flow.
- Confirm **no credits** were added.
- Confirm the order remains in a safe state (created/cancelled), no double charge.

## 6. Phase 7D — one authorized controlled payment

- **Only with explicit operator authorization.**
- Complete exactly **one** Starter Pack payment.
- Verify the success page **waits for backend `paid` status** (does not assume
  paid from the redirect alone).
- Verify the **webhook marks the order paid**.
- Verify credits are added **exactly once**.
- Verify a **duplicate webhook does not double-grant** (idempotency holds).

## 7. Phase 7E — credit gating controlled window

- Only **after** webhook + credit grant are confirmed.
- Set `ENABLE_CREDIT_GATING=true`.
- Verify free monthly allowance is honored.
- Verify paid credits are consumed correctly.
- Verify insufficient credits returns **402** (machine-readable body).
- Verify existing/previously generated content remains accessible.
- **Rollback** immediately if any issue (see section 8).

## 8. Rollback

- Set `ENABLE_CREDIT_GATING=false` **first**.
- Then set `ENABLE_BILLING=false` if needed.
- Do **not** delete payment audit tables (`payment_orders`,
  `payment_webhook_events`, `user_entitlements`, `usage_events`).
- Keep all generated content accessible.

## 9. Out of scope

- Subscriptions.
- Refund / admin billing UI.
- Manual credit grant.
- Fake payment states or fake metrics.
- GA4 historical reconstruction.
- Broad redesign / new product features.

## 10. Exit criteria

- Billing enabled smoke passes.
- Checkout / cancel QA passes.
- One controlled payment passes.
- Webhook verified (order marked paid).
- Credits granted exactly once.
- Duplicate / idempotency verified.
- Credit gating verified (only if enabled in 7E).
- A **payment closeout report** is written.
