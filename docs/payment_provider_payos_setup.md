# payOS / VietQR Provider Setup (Phase 7A)

Operator guide for configuring payOS for the Payment MVP. **Placeholders only —
never commit real values.** All secrets live in backend env exclusively.

## Render env vars

Backend service (server-side only):

```bash
ENABLE_BILLING=false
ENABLE_CREDIT_GATING=false
PAYMENT_PROVIDER=payos
PAYOS_CLIENT_ID=<payos-client-id>
PAYOS_API_KEY=<payos-api-key>
PAYOS_CHECKSUM_KEY=<payos-checksum-key>
PAYMENT_RETURN_URL=https://<frontend>/billing/success
PAYMENT_CANCEL_URL=https://<frontend>/billing/cancel
PAYOS_WEBHOOK_URL=https://<backend>/v1/billing/webhooks/payos
PAYMENT_CURRENCY=VND
```

Notes:

- PR 4 implements signed webhook verification and transactional credit grants.
  Keep billing and credit gating disabled in production until the frontend and
  real-payment QA are complete; enable them only through the rollout checklist.
- `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY` are **secrets** — backend
  only, never on the frontend, never in logs, never in this repo as real values.
- `PAYMENT_RETURN_URL` / `PAYMENT_CANCEL_URL` are public frontend routes. The return
  page only **verifies/polls**; it does not grant credits.
- `PAYOS_WEBHOOK_URL` must be the **backend** URL (the provider calls it directly).
- The frontend gets **no** payOS env vars beyond knowing its own success/cancel
  routes.

## Webhook setup checklist

- [ ] In the payOS dashboard, set the webhook URL to `PAYOS_WEBHOOK_URL`
      (`https://<backend>/v1/billing/webhooks/payos`).
- [ ] Confirm the checksum/signature scheme matches what the backend verifies with
      `PAYOS_CHECKSUM_KEY`.
- [ ] Send a provider test webhook; confirm the backend verifies the signature and
      records an audit event.
- [ ] Confirm a duplicate delivery is deduped (no double credit grant) and returns
      `200`.
- [ ] Confirm an invalid-signature delivery is rejected and grants nothing.

## Local / dev behavior

- With `ENABLE_BILLING=false` (default), checkout and webhook processing return
  `503`; read-only plan, usage, and order routes cannot create or apply payments.
- For local development, use payOS **sandbox/test** credentials only — never
  production keys on a dev machine.
- Webhooks cannot reach `localhost` directly; use a tunnel (e.g. an HTTPS forwarding
  tool) and point the sandbox webhook at the tunnel URL. Do not expose real keys.
- Never paste real keys into terminals, commits, or chat logs.

## Production deploy checklist

- [ ] Set all backend env vars above with **production** payOS values.
- [ ] Apply DB migrations; confirm `EXPECTED_ALEMBIC_HEAD` advanced (models PR).
- [ ] Verify the payOS dashboard webhook points at the production backend URL.
- [ ] Verify `PAYMENT_RETURN_URL` / `PAYMENT_CANCEL_URL` resolve on the production
      frontend domain.
- [ ] Confirm the frontend build contains **no** provider secrets.
- [ ] Smoke `GET /v1/billing/plans` (auth) returns the two packs with correct VND
      amounts.

## Real payment test checklist

- [ ] Log in on production; open Pricing → choose Starter Pack.
- [ ] Get redirected to a real payOS `checkout_url`.
- [ ] Pay a real small VND amount via VietQR.
- [ ] Return to the success page → it shows "verifying", then "confirmed" after the
      webhook.
- [ ] Billing credits increase by the Starter Pack grant exactly once.
- [ ] Run one CV analysis → analysis credit decrements by 1.
- [ ] Re-deliver the webhook from the dashboard → no second credit grant.
- [ ] Review logs/analytics → no secrets, tokens, signatures, raw payloads, or
      `checkout_url` leaked.
