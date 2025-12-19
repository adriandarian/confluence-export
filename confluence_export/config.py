"""Configuration file handling for Confluence Export."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import tomllib (Python 3.11+) or fall back to tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

# Config file names to search for (in order of priority)
CONFIG_FILE_NAMES = [
    ".confluence-export.toml",
    "confluence-export.toml",
    ".confluence-exportrc",
]

# Default config file name for saving
DEFAULT_CONFIG_FILE = ".confluence-export.toml"


@dataclass
class Config:
    """Configuration for Confluence Export."""

    # Authentication
    base_url: Optional[str] = None
    email: Optional[str] = None
    # Note: token should NOT be saved to config file for security

    # Page selection
    pages: Optional[List[str]] = None
    pages_file: Optional[str] = None

    # Export settings
    output: str = "./confluence-exports"
    formats: List[str] = field(default_factory=lambda: ["markdown"])
    flat: bool = False
    include_children: bool = False
    manifest: bool = False

    # Advanced settings
    workers: int = 4
    skip_errors: bool = True
    verbose: bool = False
    quiet: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Create a Config from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        # Handle nested sections
        auth = data.get("auth", {})
        pages_section = data.get("pages", {})
        export = data.get("export", {})
        advanced = data.get("advanced", {})

        return cls(
            # Auth section
            base_url=auth.get("base_url") or data.get("base_url"),
            email=auth.get("email") or data.get("email"),
            # Pages section
            pages=pages_section.get("ids") or data.get("pages"),
            pages_file=pages_section.get("file") or data.get("pages_file"),
            # Export section
            output=export.get("output") or data.get("output", "./confluence-exports"),
            formats=export.get("formats") or data.get("formats", ["markdown"]),
            flat=export.get("flat", data.get("flat", False)),
            include_children=export.get("include_children", data.get("include_children", False)),
            manifest=export.get("manifest", data.get("manifest", False)),
            # Advanced section
            workers=advanced.get("workers") or data.get("workers", 4),
            skip_errors=advanced.get("skip_errors", data.get("skip_errors", True)),
            verbose=advanced.get("verbose", data.get("verbose", False)),
            quiet=advanced.get("quiet", data.get("quiet", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Config to a dictionary suitable for saving.

        Returns:
            Configuration dictionary with nested sections
        """
        config: Dict[str, Any] = {
            "auth": {},
            "pages": {},
            "export": {},
            "advanced": {},
        }

        # Auth section (don't include token for security)
        if self.base_url:
            config["auth"]["base_url"] = self.base_url
        if self.email:
            config["auth"]["email"] = self.email

        # Pages section
        if self.pages:
            config["pages"]["ids"] = self.pages
        if self.pages_file:
            config["pages"]["file"] = self.pages_file

        # Export section
        config["export"]["output"] = self.output
        config["export"]["formats"] = self.formats
        if self.flat:
            config["export"]["flat"] = self.flat
        if self.include_children:
            config["export"]["include_children"] = self.include_children
        if self.manifest:
            config["export"]["manifest"] = self.manifest

        # Advanced section (only include non-defaults)
        if self.workers != 4:
            config["advanced"]["workers"] = self.workers
        if not self.skip_errors:
            config["advanced"]["skip_errors"] = self.skip_errors
        if self.verbose:
            config["advanced"]["verbose"] = self.verbose
        if self.quiet:
            config["advanced"]["quiet"] = self.quiet

        # Remove empty sections
        config = {k: v for k, v in config.items() if v}

        return config

    def to_toml(self) -> str:
        """
        Convert Config to TOML string.

        Returns:
            TOML formatted configuration string
        """
        lines = [
            "# Confluence Export Configuration",
            "# See: https://github.com/adriandarian/confluence-export",
            "",
        ]

        data = self.to_dict()

        if "auth" in data:
            lines.append("[auth]")
            if "base_url" in data["auth"]:
                lines.append(f'base_url = "{data["auth"]["base_url"]}"')
            if "email" in data["auth"]:
                lines.append(f'email = "{data["auth"]["email"]}"')
            lines.append(
                "# Note: API token should be set via environment variable CONFLUENCE_API_TOKEN"
            )
            lines.append("")

        if "pages" in data:
            lines.append("[pages]")
            lines.append("# Page IDs or full Confluence URLs")
            if "ids" in data["pages"]:
                ids_str = ", ".join(f'"{p}"' for p in data["pages"]["ids"])
                lines.append(f"ids = [{ids_str}]")
            if "file" in data["pages"]:
                lines.append(f'file = "{data["pages"]["file"]}"')
            lines.append("")

        if "export" in data:
            lines.append("[export]")
            if "output" in data["export"]:
                lines.append(f'output = "{data["export"]["output"]}"')
            if "formats" in data["export"]:
                formats_str = ", ".join(f'"{f}"' for f in data["export"]["formats"])
                lines.append(f"formats = [{formats_str}]")
            if data["export"].get("flat"):
                lines.append("flat = true")
            if data["export"].get("include_children"):
                lines.append("include_children = true")
            if data["export"].get("manifest"):
                lines.append("manifest = true")
            lines.append("")

        if "advanced" in data:
            lines.append("[advanced]")
            if "workers" in data["advanced"]:
                lines.append(f"workers = {data['advanced']['workers']}")
            if "skip_errors" in data["advanced"]:
                lines.append(f"skip_errors = {str(data['advanced']['skip_errors']).lower()}")
            if data["advanced"].get("verbose"):
                lines.append("verbose = true")
            if data["advanced"].get("quiet"):
                lines.append("quiet = true")
            lines.append("")

        return "\n".join(lines)


def find_config_file(start_dir: Optional[str] = None) -> Optional[Path]:
    """
    Find a configuration file by searching in standard locations.

    Search order:
    1. Current directory
    2. User's home directory

    Args:
        start_dir: Directory to start searching from (defaults to cwd)

    Returns:
        Path to config file if found, None otherwise
    """
    search_dirs = []

    # Start directory (current working directory)
    if start_dir:
        search_dirs.append(Path(start_dir))
    else:
        search_dirs.append(Path.cwd())

    # Home directory
    home = Path.home()
    if home not in search_dirs:
        search_dirs.append(home)

    # Search for config files
    for directory in search_dirs:
        for filename in CONFIG_FILE_NAMES:
            config_path = directory / filename
            if config_path.exists():
                return config_path

    return None


def load_config(config_path: Optional[str] = None) -> Optional[Config]:
    """
    Load configuration from a file.

    Args:
        config_path: Path to config file (auto-detected if None)

    Returns:
        Config instance if loaded, None if no config found
    """
    if tomllib is None:
        # TOML parsing not available
        return None

    # Find config file
    if config_path:
        path = Path(config_path)
        if not path.exists():
            return None
    else:
        path = find_config_file()
        if path is None:
            return None

    # Load and parse config
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return Config.from_dict(data)
    except Exception:
        return None


def save_config(config: Config, config_path: Optional[str] = None) -> str:
    """
    Save configuration to a file.

    Args:
        config: Config instance to save
        config_path: Path to save to (defaults to .confluence-export.toml in cwd)

    Returns:
        Path to saved config file
    """
    path = Path(config_path) if config_path else Path.cwd() / DEFAULT_CONFIG_FILE

    toml_content = config.to_toml()
    path.write_text(toml_content, encoding="utf-8")

    return str(path)


def merge_config_with_args(config: Optional[Config], args: Any) -> None:
    """
    Merge configuration file values with command-line arguments.

    Command-line arguments take precedence over config file values.
    This modifies the args namespace in place.

    Args:
        config: Config instance (can be None)
        args: argparse.Namespace to update
    """
    if config is None:
        return

    # Only apply config values if the arg wasn't explicitly set
    # We detect this by checking against defaults

    # Auth settings
    if not args.base_url and config.base_url:
        args.base_url = config.base_url
    if not args.email and config.email:
        args.email = config.email

    # Page selection (only apply if no CLI pages specified)
    if not getattr(args, "pages", None) and config.pages:
        args.pages = config.pages
    if not getattr(args, "pages_file", None) and config.pages_file:
        args.pages_file = config.pages_file

    # Export settings
    if args.output == "./confluence-exports" and config.output != "./confluence-exports":
        args.output = config.output
    if args.format == ["markdown"] and config.formats != ["markdown"]:
        args.format = config.formats
    if not args.flat and config.flat:
        args.flat = config.flat
    if not args.include_children and config.include_children:
        args.include_children = config.include_children
    if not args.manifest and config.manifest:
        args.manifest = config.manifest

    # Advanced settings
    if args.workers == 4 and config.workers != 4:
        args.workers = config.workers
    # skip_errors is True by default, so only override if config says False
    if args.skip_errors and not config.skip_errors:
        args.skip_errors = config.skip_errors
    if not args.verbose and config.verbose:
        args.verbose = config.verbose
    if not args.quiet and config.quiet:
        args.quiet = config.quiet


def get_config_path_for_display(config_path: Optional[str] = None) -> Optional[str]:
    """
    Get the path to config file for display purposes.

    Args:
        config_path: Explicit config path, or None for auto-detection

    Returns:
        Path to config file if found, None otherwise
    """
    if config_path:
        path = Path(config_path)
        return str(path) if path.exists() else None

    found = find_config_file()
    return str(found) if found else None
