"""Command-line interface for Confluence Export."""

import argparse
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

from . import __version__
from .client import ConfluenceClient, ConfluenceAPIError
from .fetcher import PageFetcher, PageData
from .exporters import MarkdownExporter, HTMLExporter, TextExporter, PDFExporter
from .utils import extract_page_id_from_url, ensure_directory


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="confluence-export",
        description="Export Confluence pages to Markdown, HTML, Text, or PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export a single page as Markdown
  confluence-export --base-url https://mysite.atlassian.net --email user@example.com --pages 12345 --format markdown

  # Export multiple pages as both Markdown and HTML
  confluence-export --pages 12345 67890 --format markdown html --output ./exports

  # Export a page and all its children
  confluence-export --pages 12345 --include-children --format markdown

  # Export with flat file structure
  confluence-export --pages 12345 --include-children --format markdown --flat

  # Use environment variables for authentication
  export CONFLUENCE_BASE_URL=https://mysite.atlassian.net
  export CONFLUENCE_EMAIL=user@example.com
  export CONFLUENCE_API_TOKEN=your-api-token
  confluence-export --pages 12345 --format markdown
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
        help="Atlassian account email. "
             "Can also be set via CONFLUENCE_EMAIL environment variable.",
    )
    auth_group.add_argument(
        "--token",
        metavar="TOKEN",
        help="Atlassian API token. "
             "Can also be set via CONFLUENCE_API_TOKEN environment variable.",
    )
    
    # Page selection
    page_group = parser.add_argument_group("Page Selection")
    page_group.add_argument(
        "--pages",
        nargs="+",
        metavar="PAGE",
        help="Page IDs or URLs to export. Can specify multiple pages.",
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
    
    # Advanced options
    advanced_group = parser.add_argument_group("Advanced Options")
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
        print(f"Error: Missing required authentication parameters:", file=sys.stderr)
        for param in missing:
            print(f"  - {param}", file=sys.stderr)
        print("\nYou can provide these via command-line arguments or environment variables.", file=sys.stderr)
        sys.exit(1)
    
    return base_url, email, api_token


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
    formats: List[str],
    output_dir: str,
    flat: bool,
    client: Optional[ConfluenceClient] = None
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
                print("Warning: PDF export requires API client", file=sys.stderr)
                continue
            exporters[fmt] = PDFExporter(output_dir, flat=flat, client=client)
    
    return exporters


def export_pages(
    pages: List[PageData],
    exporters: dict,
    verbose: bool = False,
    quiet: bool = False
) -> dict:
    """
    Export pages using the provided exporters.
    
    Args:
        pages: List of pages to export
        exporters: Dictionary of exporters
        verbose: Whether to print verbose output
        quiet: Whether to suppress output
        
    Returns:
        Dictionary with export results
    """
    results = {
        "exported": [],
        "failed": [],
    }
    
    total_exports = len(pages) * len(exporters)
    current = 0
    
    for page in pages:
        for fmt, exporter in exporters.items():
            current += 1
            
            try:
                if verbose and not quiet:
                    print(f"[{current}/{total_exports}] Exporting {page.title} to {fmt}...")
                
                output_path = exporter.export(page)
                results["exported"].append({
                    "page_id": page.id,
                    "title": page.title,
                    "format": fmt,
                    "path": output_path,
                })
                
            except Exception as e:
                results["failed"].append({
                    "page_id": page.id,
                    "title": page.title,
                    "format": fmt,
                    "error": str(e),
                })
                if not quiet:
                    print(f"Error exporting {page.title} to {fmt}: {e}", file=sys.stderr)
    
    return results


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
        print(f"Error: Failed to create Confluence client: {e}", file=sys.stderr)
        return 1
    
    # Validate that either --pages or --space is provided
    if not args.pages and not args.space:
        print("Error: You must specify either --pages or --space.", file=sys.stderr)
        return 1
    
    # Parse page IDs
    page_ids = []
    if args.pages:
        for page_input in args.pages:
            page_id = extract_page_id_from_url(page_input)
            if page_id:
                page_ids.append(page_id)
            else:
                # Assume it's already a page ID
                page_ids.append(page_input)
    
    # If space is specified, fetch all pages from the space
    if args.space:
        if not args.quiet:
            print(f"Fetching pages from space '{args.space}'...")
        try:
            space_pages = client.get_space_pages(args.space)
            space_page_ids = [str(p.get("id")) for p in space_pages if p.get("id")]
            if not args.quiet:
                print(f"Found {len(space_page_ids)} pages in space '{args.space}'")
            page_ids.extend(space_page_ids)
        except ConfluenceAPIError as e:
            print(f"Error: Failed to fetch pages from space '{args.space}': {e}", file=sys.stderr)
            return 1
    
    if not page_ids:
        print("Error: No valid page IDs found.", file=sys.stderr)
        return 1
    
    # Normalize formats
    formats = normalize_formats(args.format)
    
    if not args.quiet:
        print(f"Confluence Export v{__version__}")
        print(f"Base URL: {base_url}")
        if args.space:
            print(f"Space: {args.space}")
        print(f"Pages to export: {len(page_ids)}")
        print(f"Formats: {', '.join(formats)}")
        print(f"Include children: {args.include_children}")
        print(f"Output directory: {args.output}")
        print(f"Flat structure: {args.flat}")
        print()
    
    # Ensure output directory exists
    ensure_directory(args.output)
    
    # Fetch pages
    fetcher = PageFetcher(client, verbose=args.verbose)
    
    if not args.quiet:
        print("Fetching pages...")
    
    try:
        pages = fetcher.fetch_pages(
            page_ids=page_ids,
            include_children=args.include_children,
            include_body=True,
            skip_errors=args.skip_errors,
        )
    except ConfluenceAPIError as e:
        print(f"Error: Failed to fetch pages: {e}", file=sys.stderr)
        return 1
    
    if not pages:
        print("No pages found to export.", file=sys.stderr)
        return 1
    
    if not args.quiet:
        print(f"Found {len(pages)} page(s) to export.")
        print()
    
    # Create exporters
    exporters = create_exporters(formats, args.output, args.flat, client)
    
    if not exporters:
        print("Error: No valid export formats specified.", file=sys.stderr)
        return 1
    
    # Export pages
    if not args.quiet:
        print("Exporting pages...")
    
    results = export_pages(pages, exporters, verbose=args.verbose, quiet=args.quiet)
    
    # Print summary
    if not args.quiet:
        print()
        print("=" * 50)
        print("Export Summary")
        print("=" * 50)
        print(f"Successfully exported: {len(results['exported'])}")
        print(f"Failed: {len(results['failed'])}")
        
        if results["exported"] and args.verbose:
            print()
            print("Exported files:")
            for item in results["exported"]:
                print(f"  - {item['path']}")
        
        if results["failed"]:
            print()
            print("Failed exports:")
            for item in results["failed"]:
                print(f"  - {item['title']} ({item['format']}): {item['error']}")
    
    return 0 if not results["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())

