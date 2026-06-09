from __future__ import annotations

import re
import unicodedata


# Matches a single character from the Latin/Vietnamese Unicode blocks.
# Used to validate individual characters in candidate token runs.
_LATIN_VIET_CHAR_RE = re.compile(r"[a-zA-ZÀ-ɏḀ-ỿ]")

# Matches a run of 3+ tokens where:
#   - the FIRST token is 1-5 chars (handles "Nguy", "tác", etc.)
#   - each SUBSEQUENT token is 1-2 chars (single accented char or digraph like "ng")
#   - tokens are separated by a single space
# Left/right edges require whitespace or string boundary (not another non-space char).
_SPACED_TOKENS_RE = re.compile(
    r"(?<!\S)"                          # left edge
    r"(\S{1,5}(?: \S{1,2}){2,})"       # first ≤5 chars, then 2+ tokens of ≤2 chars
    r"(?!\S)"                           # right edge
)


def normalize_extracted_text(text: str) -> str:
    """Apply NFC normalization and repair common PDF extraction artifacts."""
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = _repair_spaced_vietnamese(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_evidence_snippet(text: str) -> str:
    """Normalize a single evidence snippet for display."""
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = _repair_spaced_vietnamese(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def dedupe_snippets(snippets: list[str]) -> list[str]:
    """Remove exact and case-insensitive duplicate snippets, preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for s in snippets:
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _repair_spaced_vietnamese(text: str) -> str:
    """
    Collapse runs like 'm ở r ộ ng' or 'Nguy ễ n' that PDF extractors produce
    when they write each glyph position as a separate character.

    Merge only when ALL characters across all tokens are Latin/Vietnamese letters
    AND at least one character is non-ASCII (confirming Vietnamese diacritics are
    present, so we never merge pure ASCII runs like "a b c d").
    """
    def _try_merge(match: re.Match) -> str:
        run = match.group(0)
        tokens = run.split(" ")
        if len(tokens) < 3:
            return run
        # Every individual character in every token must be a Latin/Vietnamese letter
        if not all(_LATIN_VIET_CHAR_RE.fullmatch(c) for t in tokens for c in t):
            return run
        # Require at least one non-ASCII character (actual Vietnamese diacritic)
        if not any(ord(c) > 127 for c in run):
            return run
        return unicodedata.normalize("NFC", "".join(tokens))

    return _SPACED_TOKENS_RE.sub(_try_merge, text)
