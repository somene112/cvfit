# Billing API Contract (Phase 7A)

Contract for the Payment MVP / Billing & Credits feature. **No code in this PR** —
this defines the routes, payloads, order state machine, and proposed DB schema so
later PRs implement them safely and consistently.

Conventions:

- All amounts are integer **VND** (no decimals). Currency is always `VND` in MVP.
- All `*_id` values are UUIDs (matching the existing app convention).
- Auth is the existing bearer JWT (`Authorization: Bearer <token>`); the billing
  feature does **not** change auth.
- The backend is the single source of truth for amounts, paid state, and credits.

## Feature flags (backend env)

| Flag | Default | Meaning |
| --- | --- | --- |
| `ENABLE_BILLING` | `false` | Master switch for all `/v1/billing/*` routes. When off, routes return `503`. |
| `ENABLE_CREDIT_GATING` | `false` | When off, consuming actions run without checking/spending credits (used for staged rollout). |

These are **new** flags. Do not reuse or change any Phase 6 flag. Share Links stay OFF.

---

## Routes

### `GET /v1/billing/plans`

- Auth required.
- Returns the available one-time credit packs (Starter Pack, Pro Demo Pack).
- Amounts come from backend config. **The frontend must not override the amount.**

Response `200`:

```json
{
  "currency": "VND",
  "plans": [
    {
      "plan_code": "starter_pack",
      "name": "Starter Pack",
      "amount": 20000,
      "currency": "VND",
      "credits": {
        "analysis": 10,
        "interview": 20,
        "cover_letter": 5,
        "package": 5
      }
    },
    {
      "plan_code": "pro_demo_pack",
      "name": "Pro Demo Pack",
      "amount": 49000,
      "currency": "VND",
      "credits": {
        "analysis": 30,
        "interview": 60,
        "cover_letter": 15,
        "package": 15
      }
    }
  ]
}
```

### `GET /v1/billing/usage`

- Auth required.
- Returns the caller's free allowance, remaining credits, and this-month usage.
- Monthly window computed in **Asia/Ho_Chi_Minh**.

Response `200`:

```json
{
  "month": "2026-06",
  "timezone": "Asia/Ho_Chi_Minh",
  "free_allowance": {
    "analysis": 3,
    "interview": 10,
    "cover_letter": 2,
    "package": 2
  },
  "used_this_month": {
    "analysis": 1,
    "interview": 4,
    "cover_letter": 0,
    "package": 0
  },
  "free_remaining": {
    "analysis": 2,
    "interview": 6,
    "cover_letter": 2,
    "package": 2
  },
  "remaining_credits": {
    "analysis": 12,
    "interview": 23,
    "cover_letter": 5,
    "package": 5
  }
}
```

> `remaining_credits` = purchased credits only. `free_remaining` = free allowance
> left this ICT month. Effective availability for an action = the sum of the two
> for that credit type.

### `POST /v1/billing/checkout`

- Auth required.
- Request:

```json
{
  "plan_code": "starter_pack"
}
```

- Backend behavior:
  - Validates `plan_code` against backend plan config (unknown → `400`/`422`).
  - Determines `amount` **server-side** from config (never from the request).
  - Creates a `payment_orders` row with `status = "pending"` and a unique
    `provider_order_code`.
  - Creates a payOS payment link using backend-only secrets.
  - Returns the order id, provider, checkout URL, and status.
- Frontend redirects the browser to `checkout_url`. The frontend does **not**
  compute the amount or treat the redirect as payment success.

Response `201` (or `200`):

```json
{
  "payment_order_id": "8f1c2b6e-1d4a-4c33-9b77-0a1b2c3d4e5f",
  "provider": "payos",
  "plan_code": "starter_pack",
  "amount": 20000,
  "currency": "VND",
  "status": "pending",
  "checkout_url": "https://pay.payos.vn/web/<opaque>",
  "expires_at": "2026-06-22T10:15:00+07:00"
}
```

> `checkout_url` is returned to the browser for redirect but is treated as
> sensitive: it is **not** logged and **not** sent to analytics.

### `GET /v1/billing/orders`

- Auth required.
- Returns the caller's own orders only (scoped by `user_id`). Never another user's.

Response `200`:

```json
{
  "orders": [
    {
      "payment_order_id": "8f1c2b6e-1d4a-4c33-9b77-0a1b2c3d4e5f",
      "plan_code": "starter_pack",
      "amount": 20000,
      "currency": "VND",
      "status": "paid",
      "created_at": "2026-06-22T10:00:00+07:00",
      "paid_at": "2026-06-22T10:03:12+07:00"
    },
    {
      "payment_order_id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
      "plan_code": "pro_demo_pack",
      "amount": 49000,
      "currency": "VND",
      "status": "pending",
      "created_at": "2026-06-22T11:20:00+07:00",
      "paid_at": null
    }
  ]
}
```

### `GET /v1/billing/orders/{payment_order_id}`

- Auth required.
- Ownership enforced. An unknown id **or** another user's order returns `404`
  (do not reveal that the order exists for someone else).

Response `200`:

```json
{
  "payment_order_id": "8f1c2b6e-1d4a-4c33-9b77-0a1b2c3d4e5f",
  "plan_code": "starter_pack",
  "amount": 20000,
  "currency": "VND",
  "status": "paid",
  "created_at": "2026-06-22T10:00:00+07:00",
  "paid_at": "2026-06-22T10:03:12+07:00",
  "credits_granted": {
    "analysis": 10,
    "interview": 20,
    "cover_letter": 5,
    "package": 5
  }
}
```

Not found / not owned `404`:

```json
{ "error": "not_found", "message": "Order not found." }
```

### `POST /v1/billing/webhooks/payos`

- **Public** endpoint (called by payOS, not the browser). No app JWT.
- Required handling, in order:
  1. **Verify the provider signature** using `PAYOS_CHECKSUM_KEY`. Invalid → reject
     (`400`/`401`) and grant nothing.
  2. Compute a `payload_hash` and check `payment_webhook_events` for a prior event;
     if seen, treat as duplicate and return `200` quickly **without** re-granting.
  3. Extract the provider **order code**; look up the matching `payment_orders` row.
     Unknown order → store the event and route to `manual_review`; grant nothing.
  4. Validate **amount** matches the backend order. Mismatch → `manual_review`; no credits.
  5. Validate **currency** = `VND`. Mismatch → `manual_review`; no credits.
  6. If the order is already `paid`, return `200` (idempotent) without re-granting.
  7. Otherwise transition `pending -> paid`, grant the plan's credits **once**,
     and store the webhook audit record — all in a single transaction.
- Always returns `200` for handled duplicates so the provider stops retrying.
- **Never** trusts the browser success URL for any of the above.

Webhook outcome (internal/audit, not user-facing) — conceptual `200`:

```json
{ "received": true, "order_status": "paid", "duplicate": false }
```

### Insufficient credits (returned by consuming actions, not a billing route)

When a credit-consuming action is attempted with no free allowance and no purchased
credit of the required type, the action endpoint returns a machine-readable error.

Preferred status: **`402 Payment Required`**.
Fallback: **`403`** with the same body if `402` is undesirable for a client.

```json
{
  "error": "insufficient_credits",
  "message": "You do not have enough credits for this action.",
  "required_credit": "analysis",
  "pricing_url": "/pricing"
}
```

Credit gating is implemented behind `ENABLE_CREDIT_GATING` and remains disabled
by default. Free allowance is consumed first and resets on the
`Asia/Ho_Chi_Minh` calendar month; paid credit consumption does not reset.

---

## Order status values

| Status | Meaning |
| --- | --- |
| `created` | Order row initialized before a provider link exists. |
| `pending` | Provider payment link created; awaiting confirmation. |
| `paid` | Verified webhook confirmed payment; credits granted exactly once. |
| `cancelled` | User cancelled (e.g. cancel URL / provider cancel). |
| `expired` | Payment link expired without payment. |
| `failed` | Provider reported a failed payment. |
| `manual_review` | Anomaly (unknown order, amount/currency mismatch) needing a human. |
| `refunded` | Refunded out of band (no refund UI in MVP; recorded for completeness). |

## Allowed transitions

- `created -> pending`
- `pending -> paid`
- `pending -> cancelled`
- `pending -> expired`
- `pending -> failed`
- `pending -> manual_review`
- `manual_review -> paid` (only after a human verifies the payment)

## Disallowed transitions

- `paid -> pending`
- `paid -> paid` **with a second credit grant** (a duplicate `paid` webhook must be
  a no-op; credits are granted exactly once)
- `cancelled -> paid` without manual review
- `failed -> paid` without manual review

Any transition not listed under "Allowed" is rejected and, where it indicates a
provider/data anomaly, routed to `manual_review` rather than silently applied.

---

## Proposed DB tables

All tables are additive and follow the existing UUID + `created_at` conventions.
Schema is finalized in the models PR (PR 2); columns below are the contract.

### `payment_orders`

Purpose: one row per checkout attempt; the source of truth for amount and paid state.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | owner; **indexed** |
| `plan_code` | string | e.g. `starter_pack` |
| `amount` | integer | VND, server-determined |
| `currency` | string | always `VND` in MVP |
| `status` | string | one of the status values above |
| `provider` | string | e.g. `payos` |
| `provider_order_code` | string | provider/order reference; **unique** |
| `checkout_url` | text (nullable) | sensitive; never logged |
| `credits_snapshot_json` | JSON | the plan's credit grant, frozen at creation |
| `paid_at` | datetime (nullable) | set on transition to `paid` |
| `expires_at` | datetime (nullable) | link expiry |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Indexes / constraints:

- **`provider_order_code` UNIQUE** (prevents duplicate orders & anchors webhook lookup).
- `user_id` indexed (list/own-orders queries).
- optional index on `status` for ops queries.

### `user_entitlements`

Purpose: per-user purchased credit balances by type (separate from free allowance,
which is derived from `usage_events`).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | **indexed**; consider UNIQUE for a single-row-per-user design |
| `analysis_credits` | integer | default 0 |
| `interview_credits` | integer | default 0 |
| `cover_letter_credits` | integer | default 0 |
| `package_credits` | integer | default 0 |
| `created_at` | datetime | |
| `updated_at` | datetime | |

Indexes / constraints:

- `user_id` indexed (UNIQUE if modeling exactly one entitlements row per user).
- Credit balances must never go negative (enforced in the spend transaction).

### `usage_events`

Purpose: append-only ledger of credit-consuming actions; powers `used_this_month`
and free-allowance math (ICT month windows).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID PK | |
| `user_id` | UUID FK → users.id | **indexed** |
| `action` | string | `analysis` / `interview` / `cover_letter` / `package` |
| `credit_type` | string | matches `action` credit type |
| `source` | string | `free` or `paid` (which bucket was spent) |
| `ref_id` | UUID (nullable) | e.g. the analysis job / artifact produced |
| `created_at` | datetime | **indexed with user_id** |

Indexes / constraints:

- Composite index on **(`user_id`, `created_at`)** for monthly usage windows.
- Append-only (no updates/deletes in normal operation).

### `payment_webhook_events`

Purpose: audit + idempotency for incoming provider webhooks.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | UUID PK | |
| `provider` | string | `payos` |
| `provider_order_code` | string | **indexed**; links to `payment_orders` |
| `payload_hash` | string | hash of the verified payload; **unique / dedupe-safe** |
| `signature_valid` | boolean | result of signature verification |
| `event_status` | string | e.g. `applied`, `duplicate`, `manual_review`, `rejected` |
| `received_at` | datetime | |

Indexes / constraints:

- **`payload_hash` UNIQUE** (or otherwise dedupe-safe) — the idempotency anchor.
- `provider_order_code` indexed (reconciliation / lookup).
- Raw payloads are **not** stored in plaintext logs; only the hash + minimal audit
  fields are persisted here.

---

## Summary of recommended constraints

- `payment_orders.provider_order_code` **unique**
- `payment_orders.user_id` **indexed**
- `payment_webhook_events.payload_hash` **unique / dedupe-safe**
- `payment_webhook_events.provider_order_code` **indexed**
- `user_entitlements.user_id` **indexed** (unique for single-row-per-user)
- `usage_events.(user_id, created_at)` **composite index**
