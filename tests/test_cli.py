"""Tests for command-line interface."""

import os
from unittest.mock import patch

import pytest

from confluence_export.cli import (
    create_exporters,
    create_parser,
    get_auth_config,
    main,
    normalize_formats,
)


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "confluence-export"

    def test_default_values(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "12345"])

        assert args.format == ["markdown"]
        assert args.output == "./confluence-exports"
        assert args.flat is False
        assert args.include_children is False
        assert args.skip_errors is True

    def test_multiple_pages(self):
        """Test parsing multiple page IDs."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "111", "222", "333"])

        assert args.pages == ["111", "222", "333"]

    def test_multiple_formats(self):
        """Test parsing multiple export formats."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123", "--format", "markdown", "html", "pdf"])

        assert args.format == ["markdown", "html", "pdf"]

    def test_include_children_flag(self):
        """Test include-children flag."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123", "--include-children"])

        assert args.include_children is True

    def test_flat_flag(self):
        """Test flat structure flag."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123", "--flat"])

        assert args.flat is True

    def test_verbose_flag(self):
        """Test verbose flag."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123", "-v"])

        assert args.verbose is True

    def test_quiet_flag(self):
        """Test quiet flag."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123", "-q"])

        assert args.quiet is True


class TestGetAuthConfig:
    """Tests for authentication configuration."""

    def test_auth_from_args(self):
        """Test getting auth from command line args."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "--base-url",
                "https://example.atlassian.net",
                "--email",
                "test@example.com",
                "--token",
                "secret-token",
                "--pages",
                "123",
            ]
        )

        base_url, email, token = get_auth_config(args)

        assert base_url == "https://example.atlassian.net"
        assert email == "test@example.com"
        assert token == "secret-token"

    def test_auth_from_environment(self, monkeypatch):
        """Test getting auth from environment variables."""
        monkeypatch.setenv("CONFLUENCE_BASE_URL", "https://env.atlassian.net")
        monkeypatch.setenv("CONFLUENCE_EMAIL", "env@example.com")
        monkeypatch.setenv("CONFLUENCE_API_TOKEN", "env-token")

        parser = create_parser()
        args = parser.parse_args(["--pages", "123"])

        base_url, email, token = get_auth_config(args)

        assert base_url == "https://env.atlassian.net"
        assert email == "env@example.com"
        assert token == "env-token"

    def test_args_override_environment(self, monkeypatch):
        """Test that CLI args override environment variables."""
        monkeypatch.setenv("CONFLUENCE_BASE_URL", "https://env.atlassian.net")
        monkeypatch.setenv("CONFLUENCE_EMAIL", "env@example.com")
        monkeypatch.setenv("CONFLUENCE_API_TOKEN", "env-token")

        parser = create_parser()
        args = parser.parse_args(
            [
                "--base-url",
                "https://cli.atlassian.net",
                "--pages",
                "123",
            ]
        )

        base_url, email, token = get_auth_config(args)

        assert base_url == "https://cli.atlassian.net"
        assert email == "env@example.com"  # From env
        assert token == "env-token"  # From env

    def test_missing_auth_exits(self):
        """Test that missing auth parameters cause exit."""
        parser = create_parser()
        args = parser.parse_args(["--pages", "123"])

        # Clear any environment variables
        with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
            get_auth_config(args)


class TestNormalizeFormats:
    """Tests for format normalization."""

    def test_normalize_markdown_variants(self):
        """Test that md and markdown are normalized."""
        result = normalize_formats(["md", "markdown"])
        assert result == ["markdown"]

    def test_normalize_text_variants(self):
        """Test that txt and text are normalized."""
        result = normalize_formats(["txt", "text"])
        assert result == ["txt"]

    def test_preserves_order(self):
        """Test that format order is preserved."""
        result = normalize_formats(["html", "markdown", "pdf"])
        assert result == ["html", "markdown", "pdf"]

    def test_removes_duplicates(self):
        """Test that duplicates are removed."""
        result = normalize_formats(["markdown", "md", "html", "markdown"])
        assert result == ["markdown", "html"]

    def test_case_insensitive(self):
        """Test that format names are case insensitive."""
        result = normalize_formats(["MARKDOWN", "HTML", "PDF"])
        assert result == ["markdown", "html", "pdf"]


class TestCreateExporters:
    """Tests for exporter creation."""

    def test_create_markdown_exporter(self, temp_output_dir):
        """Test creating Markdown exporter."""
        exporters = create_exporters(["markdown"], temp_output_dir, flat=False)

        assert "markdown" in exporters
        assert exporters["markdown"].file_extension == "md"

    def test_create_html_exporter(self, temp_output_dir):
        """Test creating HTML exporter."""
        exporters = create_exporters(["html"], temp_output_dir, flat=False)

        assert "html" in exporters
        assert exporters["html"].file_extension == "html"

    def test_create_txt_exporter(self, temp_output_dir):
        """Test creating text exporter."""
        exporters = create_exporters(["txt"], temp_output_dir, flat=False)

        assert "txt" in exporters
        assert exporters["txt"].file_extension == "txt"

    def test_create_multiple_exporters(self, temp_output_dir):
        """Test creating multiple exporters."""
        exporters = create_exporters(["markdown", "html", "txt"], temp_output_dir, flat=False)

        assert len(exporters) == 3
        assert "markdown" in exporters
        assert "html" in exporters
        assert "txt" in exporters

    def test_flat_flag_passed_to_exporters(self, temp_output_dir):
        """Test that flat flag is passed to exporters."""
        exporters = create_exporters(["markdown"], temp_output_dir, flat=True)

        assert exporters["markdown"].flat is True


class TestMainFunction:
    """Tests for main CLI entry point."""

    def test_no_pages_or_space_returns_error(self, monkeypatch):
        """Test that missing pages/space returns error."""
        monkeypatch.setenv("CONFLUENCE_BASE_URL", "https://test.atlassian.net")
        monkeypatch.setenv("CONFLUENCE_EMAIL", "test@example.com")
        monkeypatch.setenv("CONFLUENCE_API_TOKEN", "token")

        result = main([])

        assert result == 1

    def test_help_flag(self, capsys):
        """Test that --help works."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Export Confluence pages" in captured.out

    def test_version_flag(self, capsys):
        """Test that --version works."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])

        assert exc_info.value.code == 0
