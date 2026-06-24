"""Tiny language resolver for backend-generated content.

The product is Vietnamese-first, but the backend defaults to English so existing
API contracts and tests are unaffected. Callers (routes) pass an explicit
``language`` that the Vietnamese-only frontend sets to ``"vi"``. Anything that
is not recognizably Vietnamese resolves to ``"en"``.

Only app-generated scaffolding/prose is localized. User-provided content (CV
text, JD text, company names, job titles, skill/tech names, proper nouns) is
never translated — those values flow through unchanged.
"""

from __future__ import annotations

from typing import Optional

SUPPORTED = ("en", "vi")
DEFAULT = "en"

_VI_ALIASES = {"vi", "vie", "vi-vn", "vi_vn", "vietnamese", "tieng-viet", "tiếng việt"}


def resolve_language(value: Optional[str]) -> str:
    """Return ``"vi"`` only for explicit Vietnamese, otherwise ``"en"``."""
    if not value:
        return DEFAULT
    normalized = str(value).strip().lower()
    if normalized in _VI_ALIASES or normalized.startswith("vi"):
        return "vi"
    return DEFAULT
