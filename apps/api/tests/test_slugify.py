"""Tests for _slugify with Chinese titles and edge cases (BUG-6)."""

import pytest


class TestSlugify:
    def _slugify(self, title: str) -> str:
        """Import _slugify from projects router."""
        from app.routers.projects import _slugify
        return _slugify(title)

    def test_english_title(self):
        slug = self._slugify("My Novel")
        assert slug == "my-novel"

    def test_english_with_punctuation(self):
        slug = self._slugify("Hello! World?")
        assert slug == "hello-world"

    def test_chinese_title_preserved(self):
        """Chinese-only title should be preserved in slug."""
        slug = self._slugify("验收测试书")
        assert slug == "验收测试书", f"Expected Chinese slug preserved, got: {slug}"

    def test_mixed_cn_en_title(self):
        """Mixed Chinese and ASCII should keep ASCII portion."""
        slug = self._slugify("My 小说 Book")
        assert "my" in slug and "book" in slug

    def test_empty_title_fallback(self):
        slug = self._slugify("")
        assert slug, "Empty title should produce a non-empty slug"

    def test_punctuation_only_fallback(self):
        """Title that becomes empty after stripping punctuation."""
        slug = self._slugify("!@#$%^")
        assert slug.startswith("project-"), f"Expected project-* fallback, got: {slug}"

    def test_deterministic_same_title_same_slug(self):
        """Same Chinese title should produce the same fallback slug."""
        a = self._slugify("验收测试书")
        b = self._slugify("验收测试书")
        assert a == b

    def test_slug_length_limit(self):
        """Slug should be truncated to 50 chars."""
        long_title = "a" * 100
        slug = self._slugify(long_title)
        assert len(slug) <= 50

    def test_strips_leading_trailing_dashes(self):
        """Leading/trailing dashes from spaces should be stripped."""
        slug = self._slugify("  hello world  ")
        assert slug == "hello-world"
        assert not slug.startswith("-")
        assert not slug.endswith("-")
