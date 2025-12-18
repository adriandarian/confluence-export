"""Tests for utility functions."""

import pytest

from confluence_export.utils import (
    build_file_path,
    ensure_directory,
    extract_page_id_from_url,
    get_extension_for_format,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_name(self):
        """Test that simple names pass through unchanged."""
        assert sanitize_filename("simple_name") == "simple_name"

    def test_removes_invalid_characters(self):
        """Test that invalid characters are replaced with underscores."""
        assert sanitize_filename('file<>:"/\\|?*name') == "file_name"

    def test_replaces_spaces(self):
        """Test that spaces are replaced with underscores."""
        assert sanitize_filename("file with spaces") == "file_with_spaces"

    def test_collapses_multiple_underscores(self):
        """Test that multiple underscores are collapsed."""
        assert sanitize_filename("file___name") == "file_name"

    def test_strips_leading_trailing_underscores(self):
        """Test that leading/trailing underscores are removed."""
        assert sanitize_filename("__filename__") == "filename"

    def test_truncates_long_names(self):
        """Test that long names are truncated."""
        long_name = "a" * 300
        result = sanitize_filename(long_name, max_length=200)
        assert len(result) == 200

    def test_empty_name_returns_untitled(self):
        """Test that empty names return 'untitled'."""
        assert sanitize_filename("") == "untitled"
        assert sanitize_filename("   ") == "untitled"
        assert sanitize_filename("___") == "untitled"

    def test_unicode_characters(self):
        """Test that unicode characters are preserved."""
        assert sanitize_filename("文档名称") == "文档名称"
        assert sanitize_filename("Ñoño") == "Ñoño"


class TestExtractPageIdFromUrl:
    """Tests for extract_page_id_from_url function."""

    def test_numeric_id(self):
        """Test that numeric IDs are returned as-is."""
        assert extract_page_id_from_url("12345") == "12345"

    def test_standard_page_url(self):
        """Test extraction from standard page URL."""
        url = "https://mysite.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title"
        assert extract_page_id_from_url(url) == "123456"

    def test_viewpage_url(self):
        """Test extraction from viewpage.action URL."""
        url = "https://mysite.atlassian.net/wiki/pages/viewpage.action?pageId=123456"
        assert extract_page_id_from_url(url) == "123456"

    def test_viewpage_url_with_other_params(self):
        """Test extraction when URL has other query parameters."""
        url = "https://mysite.atlassian.net/wiki/pages/viewpage.action?spaceKey=TEST&pageId=123456&extra=value"
        assert extract_page_id_from_url(url) == "123456"

    def test_url_without_page_id(self):
        """Test that URLs without page ID return None."""
        url = "https://mysite.atlassian.net/wiki/spaces/SPACE"
        assert extract_page_id_from_url(url) is None

    def test_invalid_url(self):
        """Test that invalid URLs return None."""
        assert extract_page_id_from_url("not a url at all") is None


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_directory(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_directory"
        ensure_directory(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        ensure_directory(str(nested_dir))
        assert nested_dir.exists()

    def test_existing_directory_no_error(self, tmp_path):
        """Test that existing directories don't cause errors."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(str(existing_dir))  # Should not raise
        assert existing_dir.exists()

    def test_empty_path_no_error(self):
        """Test that empty path doesn't cause error."""
        ensure_directory("")  # Should not raise


class TestBuildFilePath:
    """Tests for build_file_path function."""

    def test_flat_structure(self, tmp_path):
        """Test flat file path generation."""
        result = build_file_path(
            output_dir=str(tmp_path),
            page_title="Test Page",
            page_id="12345",
            extension="md",
            flat=True,
        )
        assert result.endswith("Test_Page-12345.md")
        assert str(tmp_path) in result

    def test_hierarchical_structure(self, tmp_path):
        """Test hierarchical file path generation."""
        result = build_file_path(
            output_dir=str(tmp_path),
            page_title="Child Page",
            page_id="12345",
            extension="md",
            hierarchy_path=["Parent", "SubParent"],
            flat=False,
        )
        assert "Parent" in result
        assert "SubParent" in result
        assert result.endswith("Child_Page-12345.md")

    def test_sanitizes_path_components(self, tmp_path):
        """Test that path components are sanitized."""
        result = build_file_path(
            output_dir=str(tmp_path),
            page_title='Page: With "Special" Chars',
            page_id="12345",
            extension="html",
            hierarchy_path=["Parent/Path", "Child:Name"],
            flat=False,
        )
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result or result[1] == ":"  # Allow drive letter on Windows

    def test_no_hierarchy_uses_flat(self, tmp_path):
        """Test that empty hierarchy uses flat structure."""
        result = build_file_path(
            output_dir=str(tmp_path),
            page_title="Page",
            page_id="12345",
            extension="txt",
            hierarchy_path=[],
            flat=False,
        )
        # Should be directly in output_dir, not in subdirectory
        assert result.endswith("Page-12345.txt")


class TestGetExtensionForFormat:
    """Tests for get_extension_for_format function."""

    @pytest.mark.parametrize(
        "format_name,expected",
        [
            ("markdown", "md"),
            ("md", "md"),
            ("html", "html"),
            ("txt", "txt"),
            ("text", "txt"),
            ("pdf", "pdf"),
            ("MARKDOWN", "md"),  # Case insensitive
            ("HTML", "html"),
        ],
    )
    def test_known_formats(self, format_name, expected):
        """Test extension mapping for known formats."""
        assert get_extension_for_format(format_name) == expected

    def test_unknown_format_returns_lowercase(self):
        """Test that unknown formats return lowercase name."""
        assert get_extension_for_format("UNKNOWN") == "unknown"
