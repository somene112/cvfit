from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import (
    AuthResponse,
    GoogleLoginRequest,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    UserPublic,
    normalize_email,
)
from app.services.google_auth import GoogleAuthError, verify_google_id_token


router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter_by(email=email).first()


def _get_user_by_google_sub(db: Session, google_sub: str) -> User | None:
    return db.query(User).filter_by(google_sub=google_sub).first()


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if _get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )
    db.refresh(user)
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _get_user_by_email(db, payload.email)
    # A Google-only account has no password_hash; treat it as invalid credentials
    # rather than letting password verification error on a NULL hash.
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="inactive user",
        )
    return _auth_response(user)


@router.post("/google", response_model=AuthResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not settings.ENABLE_GOOGLE_AUTH or not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google login is not available",
        )

    try:
        claims = verify_google_id_token(payload.credential)
    except GoogleAuthError:
        # Never surface token internals or the expected client ID.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid google credential",
            headers={"WWW-Authenticate": "Bearer"},
        )

    google_sub = claims.get("sub")
    raw_email = claims.get("email")
    if not google_sub or not raw_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid google credential",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Google encodes email_verified as a bool or the string "true".
    if claims.get("email_verified") not in (True, "true"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="google email is not verified",
        )

    email = normalize_email(raw_email)
    full_name = claims.get("name") or None
    picture_url = claims.get("picture") or None

    user = _get_user_by_google_sub(db, google_sub)
    if user is None:
        existing = _get_user_by_email(db, email)
        if existing is not None:
            # Link Google to the existing account without touching its password.
            existing.google_sub = google_sub
            existing.email_verified = True
            if not existing.picture_url and picture_url:
                existing.picture_url = picture_url
            user = existing
        else:
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=None,
                full_name=full_name,
                google_sub=google_sub,
                auth_provider="google",
                email_verified=True,
                picture_url=picture_url,
                is_active=True,
            )
            db.add(user)

    try:
        db.commit()
    except IntegrityError:
        # Concurrent first-login race: another request already created/linked.
        db.rollback()
        user = _get_user_by_google_sub(db, google_sub) or _get_user_by_email(db, email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="could not link google account",
            )
    db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="inactive user",
        )
    return _auth_response(user)


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)):
    return LogoutResponse(ok=True)
