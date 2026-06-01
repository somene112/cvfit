from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def add_cors_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=csv_setting(settings.CORS_ALLOWED_ORIGINS),
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=csv_setting(settings.CORS_ALLOWED_METHODS),
        allow_headers=csv_setting(settings.CORS_ALLOWED_HEADERS),
    )
