"""Command-line interface for Confluence Export."""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from . import __version__
from .client import ConfluenceAPIError, ConfluenceClient
from .config import (
    Config,
    get_config_path_for_display,
    load_config,
    merge_config_with_args,
    save_config,
)
from .exporters import HTMLExporter, MarkdownExporter, PDFExporter, TextExporter
from .fetcher import DEFAULT_WORKERS, PageData, PageFetcher
from .manifest import ExportManifest
from .utils import ensure_directory, extract_page_id_from_url

# Global console for rich output
# Use safe_box=True for Windows compatibility with non-Unicode terminals
console = Console(safe_box=True)
error_console = Console(stderr=True, style="bold red", safe_box=True)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="confluence-export",
        description="Export Confluence pages to Markdown, HTML, Text, or PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export using a full Confluence URL
  confluence-export --pages "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123456789/My+Page" --format markdown

  # Export multiple pages (URLs or IDs, space-separated)
  confluence-export --pages "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123/Page+One" "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/456/Page+Two" --format markdown html

  # Export pages from a file (one URL or ID per line)
  confluence-export --pages-file pages.txt --format markdown

  # Export a page and all its children
  confluence-export --pages "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123/Parent+Page" --include-children

  # Export with flat file structure
  confluence-export --pages 123456789 --include-children --format markdown --flat

  # Use environment variables for authentication
  export CONFLUENCE_BASE_URL=https://mysite.atlassian.net
  export CONFLUENCE_EMAIL=user@example.com
  export CONFLUENCE_API_TOKEN=your-api-token
  confluence-export --pages 123456789 --format markdown

Page Selection:
  You can specify pages in multiple ways:
  - Full URL: https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123456789/Page+Title
  - Page ID: 123456789 (the numeric ID from the URL)
  - From a file: --pages-file pages.txt (one URL or ID per line)
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Authentication options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument(
        "--base-url",
        metavar="URL",
        help="Confluence site URL (e.g., https://yoursite.atlassian.net). "
        "Can also be set via CONFLUENCE_BASE_URL environment variable.",
    )
    auth_group.add_argument(
        "--email",
        metavar="EMAIL",
        help="Atlassian account email. Can also be set via CONFLUENCE_EMAIL environment variable.",
    )
    auth_group.add_argument(
        "--token",
        metavar="TOKEN",
        help="Atlassian API token. Can also be set via CONFLUENCE_API_TOKEN environment variable.",
    )

    # Page selection
    page_group = parser.add_argument_group("Page Selection")
    page_group.add_argument(
        "--pages",
        nargs="+",
        metavar="PAGE",
        help="Page IDs or URLs to export. Accepts full Confluence URLs "
        "(e.g., https://site.atlassian.net/wiki/spaces/DOCS/pages/123/Title) "
        "or numeric page IDs. Can specify multiple pages separated by spaces.",
    )
    page_group.add_argument(
        "--pages-file",
        metavar="FILE",
        help="Path to a file containing page IDs or URLs (one per line). "
        "Lines starting with # are treated as comments. "
        "Can be combined with --pages.",
    )
    page_group.add_argument(
        "--space",
        metavar="SPACE_KEY",
        help="Export all pages from a space (e.g., 'MYSPACE').",
    )
    page_group.add_argument(
        "--include-children",
        action="store_true",
        help="Recursively export all child pages of the specified pages.",
    )

    # Export options
    export_group = parser.add_argument_group("Export Options")
    export_group.add_argument(
        "--format",
        nargs="+",
        choices=["markdown", "md", "html", "txt", "text", "pdf"],
        default=["markdown"],
        metavar="FORMAT",
        help="Export format(s): markdown/md, html, txt/text, pdf. "
        "Can specify multiple formats. Default: markdown",
    )
    export_group.add_argument(
        "--output",
        "-o",
        metavar="DIR",
        default="./confluence-exports",
        help="Output directory for exported files. Default: ./confluence-exports",
    )
    export_group.add_argument(
        "--flat",
        action="store_true",
        help="Use flat file structure instead of preserving page hierarchy.",
    )
    export_group.add_argument(
        "--manifest",
        action="store_true",
        help="Generate a manifest file (INDEX.md and manifest.json) listing all exported pages.",
    )

    # Advanced options
    advanced_group = parser.add_argument_group("Advanced Options")
    advanced_group.add_argument(
        "--workers",
        "-w",
        type=int,
        default=DEFAULT_WORKERS,
        metavar="N",
        help=f"Number of parallel workers for fetching pages. Default: {DEFAULT_WORKERS}",
    )
    advanced_group.add_argument(
        "--skip-errors",
        action="store_true",
        default=True,
        help="Skip pages that fail to export and continue with others. Default: True",
    )
    advanced_group.add_argument(
        "--no-skip-errors",
        action="store_false",
        dest="skip_errors",
        help="Stop on first error instead of skipping.",
    )
    advanced_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    advanced_group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors.",
    )

    # Configuration options
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        "-c",
        metavar="FILE",
        help="Path to configuration file. Auto-detected if not specified.",
    )
    config_group.add_argument(
        "--save-config",
        metavar="FILE",
        nargs="?",
        const=True,
        help="Save current settings to config file and exit. "
        "Optionally specify output path (default: .confluence-export.toml).",
    )
    config_group.add_argument(
        "--no-config",
        action="store_true",
        help="Ignore configuration files.",
    )

    return parser


def get_auth_config(args: argparse.Namespace) -> tuple:
    """
    Get authentication configuration from args or environment variables.

    Returns:
        Tuple of (base_url, email, api_token)

    Raises:
        SystemExit: If required authentication parameters are missing
    """
    base_url = args.base_url or os.environ.get("CONFLUENCE_BASE_URL")
    email = args.email or os.environ.get("CONFLUENCE_EMAIL")
    api_token = args.token or os.environ.get("CONFLUENCE_API_TOKEN")

    missing = []
    if not base_url:
        missing.append("--base-url or CONFLUENCE_BASE_URL")
    if not email:
        missing.append("--email or CONFLUENCE_EMAIL")
    if not api_token:
        missing.append("--token or CONFLUENCE_API_TOKEN")

    if missing:
        error_console.print("Error: Missing required authentication parameters:")
        for param in missing:
            error_console.print(f"  - {param}")
        error_console.print(
            "\n[dim]You can provide these via command-line arguments or environment variables.[/dim]"
        )
        sys.exit(1)

    return base_url, email, api_token


def read_pages_from_file(filepath: str) -> List[str]:
    """
    Read page IDs or URLs from a file.

    Expects one page ID or URL per line. Lines starting with # are treated as comments.
    Empty lines are ignored.

    Args:
        filepath: Path to the file containing page IDs/URLs

    Returns:
        List of page identifiers (IDs or URLs)

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    pages = []
    with Path(filepath).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Handle comma-separated values on a single line
            if "," in line:
                for part in line.split(","):
                    part = part.strip()
                    if part:
                        pages.append(part)
            else:
                pages.append(line)
    return pages


def normalize_formats(formats: List[str]) -> List[str]:
    """
    Normalize format names to standard format.

    Args:
        formats: List of format names from user input

    Returns:
        Normalized list of unique format names
    """
    format_map = {
        "markdown": "markdown",
        "md": "markdown",
        "html": "html",
        "txt": "txt",
        "text": "txt",
        "pdf": "pdf",
    }

    normalized = []
    seen = set()
    for fmt in formats:
        norm_fmt = format_map.get(fmt.lower(), fmt.lower())
        if norm_fmt not in seen:
            normalized.append(norm_fmt)
            seen.add(norm_fmt)

    return normalized


def create_exporters(
    formats: List[str], output_dir: str, flat: bool, client: Optional[ConfluenceClient] = None
) -> dict:
    """
    Create exporter instances for the specified formats.

    Args:
        formats: List of format names
        output_dir: Output directory
        flat: Whether to use flat structure
        client: Confluence client (required for PDF export)

    Returns:
        Dictionary mapping format names to exporter instances
    """
    exporters = {}

    for fmt in formats:
        if fmt == "markdown":
            exporters[fmt] = MarkdownExporter(output_dir, flat=flat)
        elif fmt == "html":
            exporters[fmt] = HTMLExporter(output_dir, flat=flat)
        elif fmt == "txt":
            exporters[fmt] = TextExporter(output_dir, flat=flat)
        elif fmt == "pdf":
            if client is None:
                error_console.print("Warning: PDF export requires API client")
                continue
            exporters[fmt] = PDFExporter(output_dir, flat=flat, client=client)

    return exporters


def export_pages(
    pages: List[PageData],
    exporters: dict,
    verbose: bool = False,
    quiet: bool = False,
    manifest: Optional[ExportManifest] = None,
) -> dict:
    """
    Export pages using the provided exporters with progress display.

    Args:
        pages: List of pages to export
        exporters: Dictionary of exporters
        verbose: Whether to print verbose output
        quiet: Whether to suppress output
        manifest: Optional manifest to record export results

    Returns:
        Dictionary with export results
    """
    results = {
        "exported": [],
        "failed": [],
    }

    total_exports = len(pages) * len(exporters)

    if quiet:
        # No progress display in quiet mode
        for page in pages:
            for fmt, exporter in exporters.items():
                try:
                    output_path = exporter.export(page)
                    results["exported"].append(
                        {
                            "page_id": page.id,
                            "title": page.title,
                            "format": fmt,
                            "path": str(output_path),
                        }
                    )
                    if manifest:
                        manifest.add_export_result(page.id, page.title, fmt, str(output_path))
                except Exception as e:
                    results["failed"].append(
                        {
                            "page_id": page.id,
                            "title": page.title,
                            "format": fmt,
                            "error": str(e),
                        }
                    )
                    if manifest:
                        manifest.add_export_failure(page.id, page.title, fmt, str(e))
        return results

    # Rich progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=not verbose,
    ) as progress:
        export_task = progress.add_task(
            "[cyan]Exporting pages...",
            total=total_exports,
        )

        for page in pages:
            for fmt, exporter in exporters.items():
                # Update description with current page
                progress.update(
                    export_task,
                    description=f"[cyan]Exporting [bold]{page.title[:30]}{'...' if len(page.title) > 30 else ''}[/bold] → {fmt}",
                )

                try:
                    output_path = exporter.export(page)
                    results["exported"].append(
                        {
                            "page_id": page.id,
                            "title": page.title,
                            "format": fmt,
                            "path": str(output_path),
                        }
                    )
                    if manifest:
                        manifest.add_export_result(page.id, page.title, fmt, str(output_path))

                except Exception as e:
                    results["failed"].append(
                        {
                            "page_id": page.id,
                            "title": page.title,
                            "format": fmt,
                            "error": str(e),
                        }
                    )
                    if manifest:
                        manifest.add_export_failure(page.id, page.title, fmt, str(e))
                    if not quiet:
                        progress.console.print(f"  [red]x[/red] Failed: {page.title} ({fmt}): {e}")

                progress.advance(export_task)

    return results


def print_summary(results: dict, verbose: bool = False) -> None:
    """Print export summary using rich formatting."""
    console.print()

    # Create summary table
    table = Table(title="Export Summary", show_header=True, header_style="bold cyan")
    table.add_column("Status", style="dim", width=12)
    table.add_column("Count", justify="right")

    exported_count = len(results["exported"])
    failed_count = len(results["failed"])

    table.add_row(
        "[green]+ Exported[/green]",
        f"[green]{exported_count}[/green]",
    )
    if failed_count > 0:
        table.add_row(
            "[red]x Failed[/red]",
            f"[red]{failed_count}[/red]",
        )

    console.print(table)

    # Show exported files in verbose mode
    if verbose and results["exported"]:
        console.print()
        console.print("[bold]Exported files:[/bold]")
        for item in results["exported"]:
            console.print(f"  [green]-[/green] {item['path']}")

    # Always show failures
    if results["failed"]:
        console.print()
        console.print("[bold red]Failed exports:[/bold red]")
        for item in results["failed"]:
            console.print(f"  [red]-[/red] {item['title']} ({item['format']}): {item['error']}")


def print_header(
    base_url: str,
    args: argparse.Namespace,
    page_count: int,
    formats: List[str],
    config_file: Optional[str] = None,
) -> None:
    """Print the startup header with configuration info."""
    info_lines = [
        f"[bold]Base URL:[/bold] {base_url}",
    ]
    if args.space:
        info_lines.append(f"[bold]Space:[/bold] {args.space}")
    info_lines.extend(
        [
            f"[bold]Pages:[/bold] {page_count}",
            f"[bold]Formats:[/bold] {', '.join(formats)}",
            f"[bold]Children:[/bold] {'Yes' if args.include_children else 'No'}",
            f"[bold]Output:[/bold] {args.output}",
            f"[bold]Structure:[/bold] {'Flat' if args.flat else 'Hierarchical'}",
            f"[bold]Workers:[/bold] {args.workers}",
            f"[bold]Manifest:[/bold] {'Yes' if args.manifest else 'No'}",
        ]
    )
    if config_file:
        info_lines.append(f"[bold]Config:[/bold] {config_file}")

    panel = Panel(
        "\n".join(info_lines),
        title=f"[bold cyan]Confluence Export v{__version__}[/bold cyan]",
        border_style="cyan",
    )
    console.print(panel)
    console.print()


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Load environment variables from .env file if present
    load_dotenv()

    parser = create_parser()
    args = parser.parse_args(argv)

    # Load and merge configuration file (unless --no-config)
    config_file_used = None
    if not args.no_config:
        config = load_config(args.config)
        if config:
            config_file_used = get_config_path_for_display(args.config)
            merge_config_with_args(config, args)

    # Handle --save-config: save current settings and exit
    if args.save_config:
        save_path = args.save_config if isinstance(args.save_config, str) else None
        current_config = Config(
            base_url=args.base_url,
            email=args.email,
            pages=args.pages,
            pages_file=getattr(args, "pages_file", None),
            output=args.output,
            formats=args.format,
            flat=args.flat,
            include_children=args.include_children,
            manifest=args.manifest,
            workers=args.workers,
            skip_errors=args.skip_errors,
            verbose=args.verbose,
            quiet=args.quiet,
        )
        saved_path = save_config(current_config, save_path)
        console.print(f"[green]+[/green] Configuration saved to: [bold]{saved_path}[/bold]")
        console.print()
        console.print("[dim]Note: API token is not saved for security. Set it via:[/dim]")
        console.print("[dim]  export CONFLUENCE_API_TOKEN=your-token[/dim]")
        return 0

    # Get authentication configuration
    base_url, email, api_token = get_auth_config(args)

    # Create client
    try:
        client = ConfluenceClient(
            base_url=base_url,
            email=email,
            api_token=api_token,
        )
    except Exception as e:
        error_console.print(f"Error: Failed to create Confluence client: {e}")
        return 1

    # Validate that either --pages, --pages-file, or --space is provided
    if not args.pages and not args.pages_file and not args.space:
        error_console.print("Error: You must specify --pages, --pages-file, or --space.")
        return 1

    # Collect all page inputs from --pages and --pages-file
    page_inputs = []
    if args.pages:
        page_inputs.extend(args.pages)

    if args.pages_file:
        try:
            file_pages = read_pages_from_file(args.pages_file)
            if not args.quiet:
                console.print(
                    f"[green]+[/green] Loaded [bold]{len(file_pages)}[/bold] page(s) from {args.pages_file}"
                )
            page_inputs.extend(file_pages)
        except FileNotFoundError:
            error_console.print(f"Error: Pages file not found: {args.pages_file}")
            return 1
        except Exception as e:
            error_console.print(f"Error: Failed to read pages file: {e}")
            return 1

    # Parse page IDs from all inputs
    page_ids = []
    for page_input in page_inputs:
        page_id = extract_page_id_from_url(page_input)
        if page_id:
            page_ids.append(page_id)
        else:
            # Assume it's already a page ID
            page_ids.append(page_input)

    # If space is specified, fetch all pages from the space
    if args.space:
        if not args.quiet:
            with console.status(f"[bold cyan]Fetching pages from space '{args.space}'..."):
                try:
                    space_pages = client.get_space_pages(args.space)
                    space_page_ids = [str(p.get("id")) for p in space_pages if p.get("id")]
                    console.print(
                        f"[green]+[/green] Found [bold]{len(space_page_ids)}[/bold] pages in space '{args.space}'"
                    )
                    page_ids.extend(space_page_ids)
                except ConfluenceAPIError as e:
                    error_console.print(
                        f"Error: Failed to fetch pages from space '{args.space}': {e}"
                    )
                    return 1
        else:
            try:
                space_pages = client.get_space_pages(args.space)
                space_page_ids = [str(p.get("id")) for p in space_pages if p.get("id")]
                page_ids.extend(space_page_ids)
            except ConfluenceAPIError as e:
                error_console.print(f"Error: Failed to fetch pages from space '{args.space}': {e}")
                return 1

    if not page_ids:
        error_console.print("Error: No valid page IDs found.")
        return 1

    # Normalize formats
    formats = normalize_formats(args.format)

    # Print header
    if not args.quiet:
        print_header(base_url, args, len(page_ids), formats, config_file_used)

    # Ensure output directory exists
    ensure_directory(args.output)

    # Fetch pages with progress
    fetcher = PageFetcher(client, verbose=args.verbose, quiet=args.quiet, max_workers=args.workers)

    if not args.quiet:
        console.print("[bold]Fetching pages...[/bold]")

    try:
        pages = fetcher.fetch_pages(
            page_ids=page_ids,
            include_children=args.include_children,
            include_body=True,
            skip_errors=args.skip_errors,
        )
    except ConfluenceAPIError as e:
        error_console.print(f"Error: Failed to fetch pages: {e}")
        return 1

    if not pages:
        error_console.print("No pages found to export.")
        return 1

    if not args.quiet:
        console.print(f"[green]+[/green] Found [bold]{len(pages)}[/bold] page(s) to export.")
        console.print()

    # Create exporters
    exporters = create_exporters(formats, args.output, args.flat, client)

    if not exporters:
        error_console.print("Error: No valid export formats specified.")
        return 1

    # Create manifest if requested
    manifest = None
    if args.manifest:
        manifest = ExportManifest(
            output_dir=args.output,
            base_url=base_url,
            formats=formats,
            include_children=args.include_children,
            flat=args.flat,
        )
        manifest.add_pages(pages)

    # Export pages
    results = export_pages(
        pages, exporters, verbose=args.verbose, quiet=args.quiet, manifest=manifest
    )

    # Save manifest if requested
    if manifest:
        manifest_files = manifest.save()
        if not args.quiet:
            console.print()
            console.print("[bold]Manifest files created:[/bold]")
            console.print(f"  [green]-[/green] {manifest_files['markdown']}")
            console.print(f"  [green]-[/green] {manifest_files['json']}")

    # Print summary
    if not args.quiet:
        print_summary(results, verbose=args.verbose)

    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
