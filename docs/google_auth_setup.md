# Google Sign-In Setup

Adds "Continue with Google" alongside the existing email/password login. Uses the
Google Identity Services **ID-token flow**: the browser obtains a Google ID token
(credential) and posts it to the backend, which verifies it server-side and
returns the **same** app JWT auth response as a normal login.

There is **no OAuth client secret** in this flow, and no Google scopes beyond the
basic profile/email contained in the verified ID token (`sub`, `email`,
`email_verified`, `name`, `picture`).

## How it works

1. Frontend loads `https://accounts.google.com/gsi/client` and renders the Google
   button using `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.
2. On sign-in, Google returns a `credential` (an ID token). The frontend posts it
   to `POST /v1/auth/google` as `{ "credential": "<id_token>" }`.
3. The backend verifies the token signature, audience (`GOOGLE_CLIENT_ID`),
   expiry, and issuer with the `google-auth` library, and requires
   `email_verified == true`.
4. Account resolution:
   - Match by Google `sub` → log in.
   - Else match by verified `email` → link `google_sub` to that user (password is
     never overwritten).
   - Else create a new user (no password hash; `auth_provider = "google"`).
5. The backend returns the existing `AuthResponse` (`access_token`, `token_type`,
   `user`). The frontend stores it exactly like a normal login and redirects to
   `/dashboard`.

If `GOOGLE_CLIENT_ID` is unset (or `ENABLE_GOOGLE_AUTH=false`), the endpoint
returns `503` and the frontend hides the button / shows
"Google login is not configured." Email/password login is unaffected.

## Backend env (Render)

| Variable | Value | Notes |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth **Web** client ID | Verification audience. Endpoint returns 503 until set. Public ID, not a secret. |
| `ENABLE_GOOGLE_AUTH` | `true` | Optional kill-switch; defaults to `true`. Set `false` to force the endpoint off. |

## Frontend env (Render)

| Variable | Value | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Same Google OAuth Web client ID | Public by design. Empty → Google button hidden. |

Use the **same** Web client ID on both sides so the token audience matches.

## Google Cloud Console

1. APIs & Services → Credentials → Create Credentials → **OAuth client ID**.
2. Application type: **Web application**.
3. **Authorized JavaScript origins** (no path, no trailing slash):
   - `http://localhost:3000`
   - `https://<your-frontend-domain>` (e.g. your Render frontend URL)
4. No redirect URI and **no client secret** are required for the GSI ID-token flow.
5. Copy the generated **Client ID** into the env vars above.

## Deploy steps

1. Set `GOOGLE_CLIENT_ID` (and optionally `ENABLE_GOOGLE_AUTH=true`) on the backend
   service, then run `alembic upgrade head` (adds nullable Google columns;
   `EXPECTED_ALEMBIC_HEAD = 20260622_0001`).
2. Set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` on the frontend service and redeploy (it is
   inlined at build time).
3. Add the production frontend origin to Authorized JavaScript origins.

## Security notes

- Never commit the client secret (there isn't one for this flow) or any real env
  values.
- The backend never logs the Google ID token, the issued JWT, or password hashes.
  The frontend never prints the credential or JWT to the console.
- Only basic profile/email from the verified ID token is used — no Drive, Gmail,
  Calendar, or additional scopes.
- Existing email/password login remains fully available. Share Links and all
  Phase 5/6 feature flags are unchanged.
