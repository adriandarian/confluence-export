"""Tests for configuration file handling."""

import argparse
from pathlib import Path

from confluence_export.config import (
    Config,
    find_config_file,
    load_config,
    merge_config_with_args,
    save_config,
)


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.base_url is None
        assert config.email is None
        assert config.output == "./confluence-exports"
        assert config.formats == ["markdown"]
        assert config.flat is False
        assert config.include_children is False
        assert config.manifest is False
        assert config.workers == 4
        assert config.skip_errors is True
        assert config.verbose is False
        assert config.quiet is False

    def test_config_from_dict_flat(self):
        """Test creating Config from flat dictionary."""
        data = {
            "base_url": "https://example.atlassian.net",
            "email": "test@example.com",
            "output": "./exports",
            "formats": ["markdown", "html"],
            "flat": True,
            "workers": 8,
        }

        config = Config.from_dict(data)

        assert config.base_url == "https://example.atlassian.net"
        assert config.email == "test@example.com"
        assert config.output == "./exports"
        assert config.formats == ["markdown", "html"]
        assert config.flat is True
        assert config.workers == 8

    def test_config_from_dict_nested(self):
        """Test creating Config from nested dictionary (TOML style)."""
        data = {
            "auth": {
                "base_url": "https://nested.atlassian.net",
                "email": "nested@example.com",
            },
            "export": {
                "output": "./nested-exports",
                "formats": ["pdf"],
                "include_children": True,
            },
            "advanced": {
                "workers": 2,
                "verbose": True,
            },
        }

        config = Config.from_dict(data)

        assert config.base_url == "https://nested.atlassian.net"
        assert config.email == "nested@example.com"
        assert config.output == "./nested-exports"
        assert config.formats == ["pdf"]
        assert config.include_children is True
        assert config.workers == 2
        assert config.verbose is True

    def test_config_to_dict(self):
        """Test converting Config to dictionary."""
        config = Config(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            output="./exports",
            formats=["markdown", "html"],
            flat=True,
            manifest=True,
            workers=8,
        )

        data = config.to_dict()

        assert "auth" in data
        assert data["auth"]["base_url"] == "https://example.atlassian.net"
        assert data["auth"]["email"] == "test@example.com"
        assert "export" in data
        assert data["export"]["output"] == "./exports"
        assert data["export"]["formats"] == ["markdown", "html"]
        assert data["export"]["flat"] is True
        assert data["export"]["manifest"] is True
        assert "advanced" in data
        assert data["advanced"]["workers"] == 8

    def test_config_to_dict_removes_empty_sections(self):
        """Test that empty sections are not included."""
        config = Config()  # All defaults
        data = config.to_dict()

        # Only export section should exist with defaults
        assert "export" in data
        # Auth and advanced should not exist (empty or all defaults)
        assert "auth" not in data

    def test_config_to_toml(self):
        """Test converting Config to TOML string."""
        config = Config(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            output="./exports",
            formats=["markdown"],
        )

        toml = config.to_toml()

        assert "[auth]" in toml
        assert 'base_url = "https://example.atlassian.net"' in toml
        assert 'email = "test@example.com"' in toml
        assert "[export]" in toml
        assert 'output = "./exports"' in toml
        # Should have security note about token
        assert "API token" in toml


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_config_in_directory(self, tmp_path):
        """Test finding config file in specified directory."""
        config_path = tmp_path / ".confluence-export.toml"
        config_path.write_text("[auth]\n", encoding="utf-8")

        found = find_config_file(str(tmp_path))

        assert found == config_path

    def test_find_config_priority(self, tmp_path):
        """Test that .confluence-export.toml takes priority."""
        # Create multiple config files
        (tmp_path / ".confluence-export.toml").write_text("[auth]\n", encoding="utf-8")
        (tmp_path / "confluence-export.toml").write_text("[other]\n", encoding="utf-8")

        found = find_config_file(str(tmp_path))

        assert found.name == ".confluence-export.toml"

    def test_no_config_found(self, tmp_path):
        """Test when no config file exists."""
        found = find_config_file(str(tmp_path))

        assert found is None


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid TOML config file."""
        config_content = """
[auth]
base_url = "https://test.atlassian.net"
email = "test@example.com"

[export]
output = "./test-exports"
formats = ["markdown", "html"]
flat = true

[advanced]
workers = 8
"""
        config_path = tmp_path / ".confluence-export.toml"
        config_path.write_text(config_content, encoding="utf-8")

        config = load_config(str(config_path))

        assert config is not None
        assert config.base_url == "https://test.atlassian.net"
        assert config.email == "test@example.com"
        assert config.output == "./test-exports"
        assert config.formats == ["markdown", "html"]
        assert config.flat is True
        assert config.workers == 8

    def test_load_nonexistent_config(self):
        """Test loading non-existent config returns None."""
        config = load_config("/nonexistent/path/config.toml")

        assert config is None

    def test_load_auto_detect(self, tmp_path, monkeypatch):
        """Test auto-detecting config file."""
        config_content = "[auth]\nbase_url = 'https://auto.atlassian.net'\n"
        (tmp_path / ".confluence-export.toml").write_text(config_content, encoding="utf-8")

        # Change to tmp_path
        monkeypatch.chdir(tmp_path)

        config = load_config()

        assert config is not None
        assert config.base_url == "https://auto.atlassian.net"


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config = Config(
            base_url="https://save.atlassian.net",
            email="save@example.com",
            output="./saved-exports",
            formats=["markdown", "pdf"],
        )

        saved_path = save_config(config, str(tmp_path / "test-config.toml"))

        assert Path(saved_path).exists()
        content = Path(saved_path).read_text(encoding="utf-8")
        assert "https://save.atlassian.net" in content
        assert "save@example.com" in content

    def test_save_config_default_path(self, tmp_path, monkeypatch):
        """Test saving to default path in current directory."""
        monkeypatch.chdir(tmp_path)
        config = Config(base_url="https://default.atlassian.net")

        saved_path = save_config(config)

        assert Path(saved_path).name == ".confluence-export.toml"
        assert Path(saved_path).exists()


class TestMergeConfigWithArgs:
    """Tests for merge_config_with_args function."""

    def create_args(self, **kwargs):
        """Helper to create an args namespace with defaults."""
        defaults = {
            "base_url": None,
            "email": None,
            "token": None,
            "output": "./confluence-exports",
            "format": ["markdown"],
            "flat": False,
            "include_children": False,
            "manifest": False,
            "workers": 4,
            "skip_errors": True,
            "verbose": False,
            "quiet": False,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_merge_applies_config_values(self):
        """Test that config values are applied to args."""
        config = Config(
            base_url="https://config.atlassian.net",
            email="config@example.com",
            output="./config-exports",
        )
        args = self.create_args()

        merge_config_with_args(config, args)

        assert args.base_url == "https://config.atlassian.net"
        assert args.email == "config@example.com"
        assert args.output == "./config-exports"

    def test_merge_cli_takes_precedence(self):
        """Test that CLI args override config values."""
        config = Config(
            base_url="https://config.atlassian.net",
            email="config@example.com",
            output="./config-exports",
        )
        args = self.create_args(
            base_url="https://cli.atlassian.net",
            output="./cli-exports",
        )

        merge_config_with_args(config, args)

        # CLI values should win
        assert args.base_url == "https://cli.atlassian.net"
        assert args.output == "./cli-exports"
        # Config value should be applied where CLI didn't set
        assert args.email == "config@example.com"

    def test_merge_with_none_config(self):
        """Test that None config doesn't cause errors."""
        args = self.create_args()
        original_base_url = args.base_url

        merge_config_with_args(None, args)

        assert args.base_url == original_base_url

    def test_merge_formats(self):
        """Test merging format list."""
        config = Config(formats=["html", "pdf"])
        args = self.create_args()

        merge_config_with_args(config, args)

        assert args.format == ["html", "pdf"]

    def test_merge_boolean_flags(self):
        """Test merging boolean flags."""
        config = Config(
            flat=True,
            include_children=True,
            manifest=True,
            verbose=True,
        )
        args = self.create_args()

        merge_config_with_args(config, args)

        assert args.flat is True
        assert args.include_children is True
        assert args.manifest is True
        assert args.verbose is True

    def test_merge_workers(self):
        """Test merging workers setting."""
        config = Config(workers=16)
        args = self.create_args()

        merge_config_with_args(config, args)

        assert args.workers == 16

