"""
Tests for backend/app/services/parsing/text_normalization.py

Verifies:
- NFC Unicode normalization
- Vietnamese PDF extraction artifact repair
- English/code term preservation
- Whitespace normalization
- Evidence snippet deduplication
"""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.services.parsing.text_normalization import (
    dedupe_snippets,
    normalize_evidence_snippet,
    normalize_extracted_text,
)


# ---------------------------------------------------------------------------
# normalize_extracted_text / normalize_evidence_snippet — Vietnamese repair
# ---------------------------------------------------------------------------

class TestRepairSpacedVietnamese:
    def test_mo_rong_hieu_biet(self):
        raw = "m ở r ộ ng h i ể u b i ế t"
        result = normalize_extracted_text(raw)
        assert "mở" in result
        assert "rộng" in result
        assert "hiểu" in result
        assert "biết" in result

    def test_tac_dong_xa_hoi(self):
        raw = "có tác đ ộ ng xã h ộ i rõ nét"
        result = normalize_extracted_text(raw)
        assert "động" in result
        assert "hội" in result

    def test_vietnamese_name(self):
        raw = "Nguy ễ n Đ ứ c Hoàng Phúc"
        result = normalize_extracted_text(raw)
        assert "Nguyễn" in result
        assert "Đức" in result
        assert "Hoàng" in result
        assert "Phúc" in result

    def test_snippet_mo_rong(self):
        raw = "m ở r ộ ng h i ể u b i ế t"
        result = normalize_evidence_snippet(raw)
        assert "mở" in result
        assert "rộng" in result

    def test_snippet_tac_dong(self):
        raw = "có tác đ ộ ng xã h ộ i rõ nét"
        result = normalize_evidence_snippet(raw)
        assert "động" in result
        assert "hội" in result


# ---------------------------------------------------------------------------
# English and code term preservation
# ---------------------------------------------------------------------------

class TestPreserveCodeTerms:
    def test_fastapi_unchanged(self):
        text = "FastAPI PostgreSQL Docker"
        assert normalize_extracted_text(text) == "FastAPI PostgreSQL Docker"

    def test_cpp_sql_yolo(self):
        text = "C++ SQL YOLOv8"
        assert normalize_extracted_text(text) == "C++ SQL YOLOv8"

    def test_kubernetes_tensorflow(self):
        text = "Kubernetes TensorFlow"
        assert normalize_extracted_text(text) == "Kubernetes TensorFlow"

    def test_mixed_english_and_vietnamese(self):
        raw = "m ở r ộ ng FastAPI Docker"
        result = normalize_extracted_text(raw)
        assert "FastAPI" in result
        assert "Docker" in result
        assert "mở" in result

    def test_pure_ascii_short_words_not_merged(self):
        # "a b c d e" is all ASCII — should NOT be merged
        text = "a b c d e"
        result = normalize_extracted_text(text)
        # Tokens are all ASCII so merge guard prevents joining them
        assert result == "a b c d e"


# ---------------------------------------------------------------------------
# Whitespace normalization
# ---------------------------------------------------------------------------

class TestWhitespaceNormalization:
    def test_collapses_multiple_spaces(self):
        assert normalize_extracted_text("hello   world") == "hello world"

    def test_collapses_multiple_newlines(self):
        text = "line1\n\n\n\nline2"
        result = normalize_extracted_text(text)
        assert "\n\n\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_extracted_text("  hello  ") == "hello"

    def test_empty_string_returns_empty(self):
        assert normalize_extracted_text("") == ""
        assert normalize_evidence_snippet("") == ""

    def test_none_not_passed(self):
        # The function expects str; just confirm empty str works
        assert normalize_extracted_text("") == ""


# ---------------------------------------------------------------------------
# NFC normalization
# ---------------------------------------------------------------------------

class TestNFCNormalization:
    def test_nfc_normalization_applied(self):
        # NFD form of "ộ": o + combining below + combining above
        nfd_char = "ộ"  # o + combining dot below + combining circumflex
        text = f"tr{nfd_char}ng"
        result = normalize_extracted_text(text)
        # After NFC, should be composed form
        import unicodedata
        assert unicodedata.is_normalized("NFC", result)


# ---------------------------------------------------------------------------
# dedupe_snippets
# ---------------------------------------------------------------------------

class TestDedupeSnippets:
    def test_removes_exact_duplicates(self):
        snippets = ["FastAPI experience", "FastAPI experience", "Docker skills"]
        assert dedupe_snippets(snippets) == ["FastAPI experience", "Docker skills"]

    def test_removes_case_insensitive_duplicates(self):
        snippets = ["FastAPI Experience", "fastapi experience", "Docker skills"]
        assert dedupe_snippets(snippets) == ["FastAPI Experience", "Docker skills"]

    def test_preserves_order(self):
        snippets = ["C", "A", "B", "A"]
        result = dedupe_snippets(snippets)
        assert result == ["C", "A", "B"]

    def test_empty_strings_skipped(self):
        snippets = ["hello", "", "  ", "world"]
        result = dedupe_snippets(snippets)
        assert "" not in result
        assert "hello" in result
        assert "world" in result

    def test_empty_list(self):
        assert dedupe_snippets([]) == []

    def test_all_unique_preserved(self):
        snippets = ["alpha", "beta", "gamma"]
        assert dedupe_snippets(snippets) == ["alpha", "beta", "gamma"]

    def test_normalized_vietnamese_deduped(self):
        # After normalization, two snippets that look the same should dedup
        s1 = normalize_evidence_snippet("m ở r ộ ng")
        s2 = normalize_evidence_snippet("m ở r ộ ng")
        assert dedupe_snippets([s1, s2, "other"]) == [s1, "other"]
