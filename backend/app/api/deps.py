from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenValidationError, validate_access_token
from app.db.models import User
from app.db.session import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()

    return _load_user_from_credentials(credentials, db)


def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise _auth_error()
    return _load_user_from_credentials(credentials, db)


def _load_user_from_credentials(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> User:
    try:
        subject = validate_access_token(credentials.credentials)
        user_id = uuid.UUID(subject)
    except (TokenValidationError, ValueError):
        raise _auth_error()

    user = db.get(User, user_id)
    if not user:
        raise _auth_error()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="inactive user",
        )
    return user


def admin_emails() -> set[str]:
    """Normalized (lower-cased) admin allow-list from ADMIN_EMAILS env."""
    return {
        item.strip().lower()
        for item in (settings.ADMIN_EMAILS or "").split(",")
        if item.strip()
    }


def require_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Admin authorization for read-only monitoring routes.

    Reuses ``get_current_user`` so unauthenticated/inactive requests already
    fail with 401/403 before this check. Authenticated non-admin users get a
    403. Admin membership is decided solely by email presence in ADMIN_EMAILS;
    no admin flag is persisted and no migration is required.
    """
    if (current_user.email or "").strip().lower() not in admin_emails():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin access required",
        )
    return current_user
