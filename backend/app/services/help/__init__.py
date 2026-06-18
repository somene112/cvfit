"""Phase 6 Help Assistant / Career Coach v1 service layer.

Guided, scoped, deterministic. Answers are built only from the authenticated
user's own product data passed in by the route (which performs ownership
checks). No LLM, no network, no free-form generation.
"""

from app.services.help.assistant import (
    FALLBACK_ANSWER,
    HelpContext,
    SUPPORTED_INTENTS,
    build_assistant_response,
    build_suggestions,
)

__all__ = [
    "HelpContext",
    "build_assistant_response",
    "build_suggestions",
    "SUPPORTED_INTENTS",
    "FALLBACK_ANSWER",
]
