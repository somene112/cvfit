# Payment Production Rollout Checklist

Use this checklist for a controlled Phase 7A rollout. It does not authorize
committing credentials, changing code defaults, or treating a browser return as
payment confirmation. Record results in
[`payment_closeout_report.md`](payment_closeout_report.md).

## 1. Preconditions

- [ ] PRs #76, #78, #80, #81, #82, and #83 are merged.
- [ ] The backend deploy contains checkout, verified webhook, credit grant, and
      credit-gating code.
- [ ] The frontend deploy contains `/pricing`, `/billing`, `/billing/success`,
      and `/billing/cancel`.
- [ ] Production DB is migrated to Alembic head `20260623_0001`.
- [ ] Latest Render backend and frontend deploys are healthy.
- [ ] Email/password and Google Login still work.
- [ ] Phase 6 core flows still work and Share Links remain off.

## 2. Render backend environment

Set secrets only through Render's secret environment controls. Verify names and
public URLs without copying secret values into tickets, chat, logs, or reports.

```text
PAYMENT_PROVIDER=payos
PAYMENT_CURRENCY=VND
PAYMENT_RETURN_URL=https://cvfit-frontend.onrender.com/billing/success
PAYMENT_CANCEL_URL=https://cvfit-frontend.onrender.com/billing/cancel
PAYOS_WEBHOOK_URL=https://cvfit.onrender.com/v1/billing/webhooks/payos
PAYOS_CLIENT_ID=<set-in-render-secret>
PAYOS_API_KEY=<set-in-render-secret>
PAYOS_CHECKSUM_KEY=<set-in-render-secret>

ENABLE_BILLING=false
ENABLE_CREDIT_GATING=false
```

- [ ] Frontend environment contains no payOS credentials.
- [ ] Both rollout flags start as `false`.
- [ ] Return/cancel URLs point to the deployed frontend.
- [ ] Webhook URL points to the deployed backend.

## 3. payOS dashboard

- [ ] Configure the webhook URL to the production backend URL above.
- [ ] Verify the dashboard URL exactly matches `PAYOS_WEBHOOK_URL`.
- [ ] Use real, sandbox, or test credentials consistently with the account mode.
- [ ] Never commit, screenshot, or paste credentials into the QA report.
- [ ] Record only non-sensitive provider identifiers needed for reconciliation.

## 4. Controlled rollout

### Phase A — disabled smoke

- [ ] Keep `ENABLE_BILLING=false` and `ENABLE_CREDIT_GATING=false`.
- [ ] Run `scripts/smoke_payment_production_readiness.py` with
      `EXPECT_BILLING_ENABLED=false`.
- [ ] Confirm `/pricing` can load backend plans for an authenticated test user.
- [ ] Confirm checkout shows the safe unavailable response/message.
- [ ] Confirm `/billing` renders without crashing.

### Phase B — checkout and webhook smoke

- [ ] Set `ENABLE_BILLING=true` through the controlled Render rollout.
- [ ] Keep `ENABLE_CREDIT_GATING=false`.
- [ ] Login as the controlled test user and open `/pricing`.
- [ ] Start checkout and confirm the backend order is `pending`.
- [ ] Confirm the provider redirect opens; do not record the full checkout URL.
- [ ] Exercise cancel and confirm `/billing/cancel` grants no credits.
- [ ] Manually complete one authorized real or sandbox payment.
- [ ] Confirm the verified webhook changes the order to `paid`.
- [ ] Confirm the backend-owned plan credits are granted exactly once.
- [ ] If provider resend is safe, resend the webhook and confirm no double grant.
- [ ] Confirm `/billing/success` stays in verifying/pending state until the
      backend reports `paid`.

### Phase C — credit-gating smoke

- [ ] Set `ENABLE_CREDIT_GATING=true` only for the controlled rollout window.
- [ ] Confirm monthly free allowance is consumed first.
- [ ] Confirm paid credits are consumed after free allowance.
- [ ] Confirm an exhausted credit type returns HTTP `402` with
      `error=insufficient_credits`.
- [ ] Confirm the frontend shows a pricing CTA or a safe error.
- [ ] Confirm read-only endpoints remain accessible.
- [ ] Confirm existing generated content remains viewable/downloadable.

### Phase D — rollback

- [ ] Set `ENABLE_CREDIT_GATING=false` first to stop blocking users.
- [ ] Set `ENABLE_BILLING=false` if new checkout or webhook processing must stop.
- [ ] Do not delete `payment_orders`, `user_entitlements`, `usage_events`, or
      `payment_webhook_events`.
- [ ] Keep already-generated content accessible.
- [ ] Record the reason, time, operator, and observed impact of rollback.

## 5. Exit criteria

- [ ] Checkout created a backend-owned `pending` order.
- [ ] Provider redirect opened.
- [ ] Webhook signature verified and order became `paid`.
- [ ] Credits were granted exactly once.
- [ ] Duplicate webhook caused no second grant.
- [ ] Free and paid credit gating worked in the correct order.
- [ ] Insufficient credits returned HTTP `402`.
- [ ] Read-only actions and existing generated content were unaffected.
- [ ] No secret, sensitive URL, signature, raw webhook, or user content leaked.
- [ ] Usage events contain no raw CV, JD, or interview-answer text.
- [ ] A closeout report was completed and reviewed.
