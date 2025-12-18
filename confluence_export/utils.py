"""Utility functions for Confluence Export CLI."""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """
    Sanitize a string to be used as a filename.

    Args:
        name: The original name to sanitize
        max_length: Maximum length of the filename

    Returns:
        A sanitized filename safe for all operating systems
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r"[\s_]+", "_", sanitized)
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip("_ ")
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    # Ensure we have something
    if not sanitized:
        sanitized = "untitled"
    return sanitized


def extract_page_id_from_url(url: str) -> Optional[str]:
    """
    Extract page ID from a Confluence URL.

    Supports formats like:
    - https://site.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title
    - https://site.atlassian.net/wiki/pages/viewpage.action?pageId=123456

    Args:
        url: The Confluence page URL

    Returns:
        The page ID as a string, or None if not found
    """
    # Check if it's a URL or just an ID
    if url.isdigit():
        return url

    try:
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query

        # Check for pageId in query string
        if "pageId=" in query:
            match = re.search(r"pageId=(\d+)", query)
            if match:
                return match.group(1)

        # Check for /pages/ID/ pattern
        match = re.search(r"/pages/(\d+)", path)
        if match:
            return match.group(1)

        return None
    except Exception:
        return None


def ensure_directory(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path to ensure exists
    """
    if path:
        Path(path).mkdir(parents=True, exist_ok=True)


def build_file_path(
    output_dir: str,
    page_title: str,
    page_id: str,
    extension: str,
    hierarchy_path: Optional[list] = None,
    flat: bool = False,
) -> str:
    """
    Build the output file path for an exported page.

    Args:
        output_dir: Base output directory
        page_title: Title of the page
        page_id: ID of the page
        extension: File extension (e.g., 'md', 'html')
        hierarchy_path: List of parent page titles for hierarchy
        flat: If True, ignore hierarchy and put all files in output_dir

    Returns:
        Full path to the output file
    """
    # Sanitize the filename
    safe_title = sanitize_filename(page_title)
    filename = f"{safe_title}-{page_id}.{extension}"

    if flat or not hierarchy_path:
        # Flat structure
        return str(Path(output_dir) / filename)
    else:
        # Hierarchical structure
        path_parts = [sanitize_filename(p) for p in hierarchy_path]
        dir_path = Path(output_dir).joinpath(*path_parts)
        return str(dir_path / filename)


def get_extension_for_format(format_name: str) -> str:
    """
    Get the file extension for a given export format.

    Args:
        format_name: The format name (markdown, html, txt, pdf)

    Returns:
        The file extension without the dot
    """
    format_map = {
        "markdown": "md",
        "md": "md",
        "html": "html",
        "txt": "txt",
        "text": "txt",
        "pdf": "pdf",
    }
    return format_map.get(format_name.lower(), format_name.lower())
