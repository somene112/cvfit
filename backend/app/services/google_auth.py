"""Server-side verification of Google Identity Services ID tokens.

Uses the official ``google-auth`` library to validate the token signature,
audience (``GOOGLE_CLIENT_ID``), expiry, and issuer. The library is imported
lazily so the rest of the app (and tests that mock this function) do not require
``google-auth`` to be installed at import time.

Security: the raw ID token is never logged or returned to the client. Only the
non-sensitive verified claims (sub/email/email_verified/name/picture) are used.
"""

from __future__ import annotations

from app.core.config import settings


# Google may issue tokens from either issuer host.
_ALLOWED_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleAuthError(Exception):
    """Raised when a Google ID token cannot be verified."""


def verify_google_id_token(credential: str) -> dict:
    """Verify a Google ID token and return its claims.

    Raises ``GoogleAuthError`` for any verification failure. The error message is
    intentionally generic and never echoes the token or the expected client ID.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleAuthError("google auth is not configured")

    # Lazy import keeps google-auth optional for code paths that mock verification.
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    try:
        claims = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:  # invalid signature, audience, expiry, or malformed token
        raise GoogleAuthError("invalid google credential") from exc

    if claims.get("iss") not in _ALLOWED_ISSUERS:
        raise GoogleAuthError("invalid google credential")

    return claims
