"""Page fetcher for retrieving Confluence pages."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .client import ConfluenceAPIError, ConfluenceClient

# Console for output (legacy_windows=False to avoid encoding issues)
console = Console(legacy_windows=False)

# Default number of parallel workers
DEFAULT_WORKERS = 4


@dataclass
class PageData:
    """Represents a Confluence page with its content and hierarchy info."""

    id: str
    title: str
    space_key: Optional[str] = None
    body_storage: str = ""
    hierarchy_path: List[str] = field(default_factory=list)
    hierarchy_depth: int = 0
    parent_id: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any], body: str = "") -> "PageData":
        """
        Create a PageData instance from an API response.

        Args:
            data: The API response dictionary
            body: The page body content

        Returns:
            A PageData instance
        """
        space_key = None
        if "spaceId" in data:
            space_key = data.get("spaceId")
        elif "space" in data:
            space_key = data["space"].get("key")

        return cls(
            id=str(data.get("id", "")),
            title=data.get("title", "Untitled"),
            space_key=space_key,
            body_storage=body,
            hierarchy_path=data.get("_hierarchy_path", []),
            hierarchy_depth=data.get("_hierarchy_depth", 0),
            parent_id=data.get("parentId"),
        )


class PageFetcher:
    """
    Fetches Confluence pages with support for single, bulk, and recursive fetching.
    Supports parallel fetching for improved performance.
    """

    def __init__(
        self,
        client: ConfluenceClient,
        verbose: bool = False,
        quiet: bool = False,
        max_workers: int = DEFAULT_WORKERS,
    ):
        """
        Initialize the page fetcher.

        Args:
            client: The Confluence API client
            verbose: Whether to print progress messages
            quiet: Whether to suppress all output
            max_workers: Maximum number of parallel workers for fetching
        """
        self.client = client
        self.verbose = verbose
        self.quiet = quiet
        self.max_workers = max_workers

    def _log(self, message: str) -> None:
        """Print a message if verbose mode is enabled and not quiet."""
        if self.verbose and not self.quiet:
            console.print(f"  [dim]{message}[/dim]")

    def _fetch_page_content(self, page_id: str, include_body: bool = True) -> PageData:
        """
        Fetch a single page's content (thread-safe).

        Args:
            page_id: The page ID to fetch
            include_body: Whether to fetch the page body content

        Returns:
            PageData instance with the page information
        """
        page_data = self.client.get_page(page_id, include_body=False)

        body = ""
        if include_body:
            body = self.client.get_page_body(page_id, body_format="storage")

        return PageData.from_api_response(page_data, body)

    def fetch_single_page(self, page_id: str, include_body: bool = True) -> PageData:
        """
        Fetch a single page by its ID.

        Args:
            page_id: The page ID to fetch
            include_body: Whether to fetch the page body content

        Returns:
            PageData instance with the page information

        Raises:
            ConfluenceAPIError: If the page cannot be fetched
        """
        self._log(f"Fetching page {page_id}...")
        return self._fetch_page_content(page_id, include_body)

    def fetch_multiple_pages(
        self, page_ids: List[str], include_body: bool = True, skip_errors: bool = True
    ) -> List[PageData]:
        """
        Fetch multiple pages by their IDs in parallel with progress display.

        Args:
            page_ids: List of page IDs to fetch
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch; otherwise raise

        Returns:
            List of PageData instances
        """
        if not page_ids:
            return []

        # For single page, don't use parallelism
        if len(page_ids) == 1:
            try:
                return [self._fetch_page_content(page_ids[0], include_body)]
            except ConfluenceAPIError:
                if skip_errors:
                    return []
                raise

        pages = []
        errors = []

        if self.quiet:
            # No progress display in quiet mode
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_id = {
                    executor.submit(self._fetch_page_content, pid, include_body): pid
                    for pid in page_ids
                }

                for future in as_completed(future_to_id):
                    page_id = future_to_id[future]
                    try:
                        page = future.result()
                        pages.append(page)
                    except ConfluenceAPIError as e:
                        if skip_errors:
                            errors.append((page_id, e))
                        else:
                            raise

            return pages

        # Rich progress display with parallel fetching
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=not self.verbose,
        ) as progress:
            fetch_task = progress.add_task(
                f"[cyan]Fetching pages ({self.max_workers} workers)...",
                total=len(page_ids),
            )

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_id = {
                    executor.submit(self._fetch_page_content, pid, include_body): pid
                    for pid in page_ids
                }

                for future in as_completed(future_to_id):
                    page_id = future_to_id[future]
                    try:
                        page = future.result()
                        pages.append(page)

                        # Update with current page title
                        progress.update(
                            fetch_task,
                            description=f"[cyan]Fetched [bold]{page.title[:30]}{'...' if len(page.title) > 30 else ''}[/bold]",
                        )
                    except ConfluenceAPIError as e:
                        if skip_errors:
                            errors.append((page_id, e))
                            progress.console.print(
                                f"  [yellow]![/yellow] Skipped page {page_id}: {e}"
                            )
                        else:
                            raise

                    progress.advance(fetch_task)

        return pages

    def fetch_with_children(
        self,
        page_id: str,
        include_root: bool = True,
        include_body: bool = True,
        skip_errors: bool = True,
    ) -> List[PageData]:
        """
        Fetch a page/folder and all its descendant pages with parallel fetching.

        Args:
            page_id: The root page or folder ID
            include_root: Whether to include the root page itself
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch; otherwise raise

        Returns:
            List of PageData instances (root first if included, then descendants)
        """
        pages = []
        is_folder = False

        # Check if it's a folder
        if not self.quiet:
            console.print("  [dim]Checking content type...[/dim]")
        
        try:
            content_info = self.client.get_content_info(page_id)
            is_folder = content_info.get("type") == "folder"
        except ConfluenceAPIError:
            pass

        # Fetch root page if requested (folders don't have body content)
        if include_root and not is_folder:
            self._log(f"Fetching root page {page_id}...")
            try:
                root_page = self._fetch_page_content(page_id, include_body=include_body)
                pages.append(root_page)
            except ConfluenceAPIError as e:
                if skip_errors:
                    if not self.quiet:
                        console.print(f"  [yellow]![/yellow] Skipped root page {page_id}: {e}")
                else:
                    raise

        # Fetch all descendants
        if not self.quiet:
            console.print("  [dim]Discovering child pages...[/dim]")

        # Get root page title for hierarchy path
        root_title = ""
        if pages:
            root_title = pages[0].title
        else:
            try:
                root_data = self.client.get_content_info(page_id)
                root_title = root_data.get("title", "")
            except ConfluenceAPIError:
                pass

        # First, discover all descendants (quick operation)
        descendant_info = self._discover_descendants(page_id, skip_errors=skip_errors, is_folder=is_folder)

        if not self.quiet and descendant_info:
            console.print(f"  [dim]Found {len(descendant_info)} child pages[/dim]")

        # Then fetch them in parallel with progress
        if descendant_info:
            descendants = self._fetch_discovered_pages_parallel(
                descendant_info,
                root_title=root_title,
                include_body=include_body,
                skip_errors=skip_errors,
            )
            pages.extend(descendants)

        return pages

    def _discover_descendants(
        self,
        page_id: str,
        parent_path: Optional[List[str]] = None,
        depth: int = 0,
        skip_errors: bool = True,
        is_folder: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Recursively discover all descendants of a page/folder (metadata only).

        Args:
            page_id: The parent page or folder ID
            parent_path: List of parent page titles for hierarchy
            depth: Current depth in the hierarchy
            skip_errors: If True, skip pages that fail to fetch
            is_folder: Whether the root is a folder (uses ancestor search)

        Returns:
            List of dictionaries with descendant info
        """
        if parent_path is None:
            parent_path = []

        descendants = []

        try:
            # For folders, get all descendants at once using ancestor search
            if is_folder and depth == 0:
                all_descendants = self.client.get_folder_contents_by_ancestor(page_id)
                # Build hierarchy information and filter to only pages (not folders)
                for item in all_descendants:
                    # Skip folders - only include pages
                    if item.get("type") == "folder":
                        continue
                    
                    item_id = str(item.get("id", ""))
                    item_title = item.get("title", "Untitled")
                    ancestors = item.get("ancestors", [])
                    
                    # Build the hierarchy path from ancestors
                    hier_path = []
                    for ancestor in ancestors:
                        ancestor_id = str(ancestor.get("id", ""))
                        ancestor_title = ancestor.get("title", "Untitled")
                        # Skip the root folder itself in the path
                        if ancestor_id != page_id:
                            hier_path.append(ancestor_title)
                    
                    descendants.append({
                        "id": item_id,
                        "title": item_title,
                        "parent_path": hier_path,
                        "depth": len(hier_path),
                        "parent_id": ancestors[-1].get("id") if ancestors else page_id,
                    })
            else:
                # For regular pages, use standard children endpoint
                children = self.client.get_page_children(page_id)
                
                for child_data in children:
                    child_id = str(child_data.get("id", ""))
                    child_title = child_data.get("title", "Untitled")

                    # Store info for later fetching
                    descendants.append(
                        {
                            "id": child_id,
                            "title": child_title,
                            "parent_path": parent_path.copy(),
                            "depth": depth + 1,
                            "parent_id": page_id,
                        }
                    )

                    # Recursively discover this child's descendants
                    child_descendants = self._discover_descendants(
                        child_id,
                        parent_path=[*parent_path, child_title],
                        depth=depth + 1,
                        skip_errors=skip_errors,
                        is_folder=False,
                    )
                    descendants.extend(child_descendants)

        except ConfluenceAPIError as e:
            if skip_errors:
                self._log(f"Warning: Failed to get children of page {page_id}: {e}")
                return []
            raise

        return descendants

    def _fetch_page_with_hierarchy(
        self,
        info: Dict[str, Any],
        root_title: str,
        include_body: bool = True,
    ) -> PageData:
        """
        Fetch a single page with its hierarchy info (thread-safe).

        Args:
            info: Page info dictionary with id, title, parent_path, etc.
            root_title: Title of the root page for hierarchy
            include_body: Whether to fetch the page body content

        Returns:
            PageData instance
        """
        body = ""
        if include_body:
            body = self.client.get_page_body(info["id"], body_format="storage")

        parent_path = [root_title] + info["parent_path"] if root_title else info["parent_path"]
        return PageData(
            id=info["id"],
            title=info["title"],
            body_storage=body,
            hierarchy_path=parent_path,
            hierarchy_depth=info["depth"],
            parent_id=info["parent_id"],
        )

    def _fetch_discovered_pages_parallel(
        self,
        pages_info: List[Dict[str, Any]],
        root_title: str,
        include_body: bool = True,
        skip_errors: bool = True,
    ) -> List[PageData]:
        """
        Fetch pages from discovered info in parallel with progress display.

        Args:
            pages_info: List of page info dictionaries
            root_title: Title of the root page for hierarchy
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch

        Returns:
            List of PageData instances
        """
        if not pages_info:
            return []

        pages = []
        errors = []

        if self.quiet:
            # No progress display in quiet mode
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_info = {
                    executor.submit(
                        self._fetch_page_with_hierarchy, info, root_title, include_body
                    ): info
                    for info in pages_info
                }

                for future in as_completed(future_to_info):
                    info = future_to_info[future]
                    try:
                        page = future.result()
                        pages.append(page)
                    except ConfluenceAPIError as e:
                        if skip_errors:
                            errors.append((info["id"], e))
                        else:
                            raise

            # Sort by depth to maintain hierarchy order
            pages.sort(key=lambda p: (p.hierarchy_depth, p.title))
            return pages

        # Rich progress display with parallel fetching
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=not self.verbose,
        ) as progress:
            fetch_task = progress.add_task(
                f"[cyan]Fetching child pages ({self.max_workers} workers)...",
                total=len(pages_info),
            )

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_info = {
                    executor.submit(
                        self._fetch_page_with_hierarchy, info, root_title, include_body
                    ): info
                    for info in pages_info
                }

                for future in as_completed(future_to_info):
                    info = future_to_info[future]
                    try:
                        page = future.result()
                        pages.append(page)

                        progress.update(
                            fetch_task,
                            description=f"[cyan]Fetched [bold]{page.title[:30]}{'...' if len(page.title) > 30 else ''}[/bold]",
                        )
                    except ConfluenceAPIError as e:
                        if skip_errors:
                            errors.append((info["id"], e))
                            progress.console.print(
                                f"  [yellow]![/yellow] Skipped {info['title']}: {e}"
                            )
                        else:
                            raise

                    progress.advance(fetch_task)

        # Sort by depth to maintain hierarchy order
        pages.sort(key=lambda p: (p.hierarchy_depth, p.title))
        return pages

    def _fetch_descendants_recursive(
        self,
        page_id: str,
        parent_path: List[str],
        include_body: bool = True,
        skip_errors: bool = True,
        depth: int = 0,
    ) -> List[PageData]:
        """
        Recursively fetch all descendants of a page (legacy sequential method).

        Args:
            page_id: The parent page ID
            parent_path: List of parent page titles for hierarchy
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch
            depth: Current depth in the hierarchy

        Returns:
            List of PageData instances
        """
        descendants = []

        try:
            children = self.client.get_page_children(page_id)
        except ConfluenceAPIError as e:
            if skip_errors:
                self._log(f"Warning: Failed to get children of page {page_id}: {e}")
                return []
            raise

        for child_data in children:
            child_id = str(child_data.get("id", ""))
            child_title = child_data.get("title", "Untitled")

            self._log(f"{'  ' * depth}Fetching: {child_title}")

            try:
                body = ""
                if include_body:
                    body = self.client.get_page_body(child_id, body_format="storage")

                page = PageData(
                    id=child_id,
                    title=child_title,
                    body_storage=body,
                    hierarchy_path=parent_path.copy(),
                    hierarchy_depth=depth + 1,
                    parent_id=page_id,
                )
                descendants.append(page)

                # Recursively fetch this child's descendants
                child_descendants = self._fetch_descendants_recursive(
                    child_id,
                    parent_path=[*parent_path, child_title],
                    include_body=include_body,
                    skip_errors=skip_errors,
                    depth=depth + 1,
                )
                descendants.extend(child_descendants)

            except ConfluenceAPIError as e:
                if skip_errors:
                    self._log(f"Warning: Failed to fetch page {child_id}: {e}")
                else:
                    raise

        return descendants

    def fetch_pages(
        self,
        page_ids: List[str],
        include_children: bool = False,
        include_body: bool = True,
        skip_errors: bool = True,
    ) -> List[PageData]:
        """
        Fetch pages with optional children using parallel fetching.

        This is the main entry point for fetching pages. It handles both
        single and multiple page IDs, with optional recursive child fetching.

        Args:
            page_ids: List of page IDs to fetch
            include_children: Whether to fetch child pages recursively
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch

        Returns:
            List of PageData instances
        """
        all_pages = []
        seen_ids = set()

        for i, page_id in enumerate(page_ids):
            if page_id in seen_ids:
                continue

            if not self.quiet and len(page_ids) > 1:
                console.print(f"[dim]Processing page {i + 1}/{len(page_ids)}...[/dim]")

            if include_children:
                pages = self.fetch_with_children(
                    page_id, include_root=True, include_body=include_body, skip_errors=skip_errors
                )
            else:
                try:
                    pages = [self._fetch_page_content(page_id, include_body=include_body)]
                except ConfluenceAPIError as e:
                    if skip_errors:
                        if not self.quiet:
                            console.print(f"  [yellow]![/yellow] Skipped page {page_id}: {e}")
                        continue
                    raise

            for page in pages:
                if page.id not in seen_ids:
                    all_pages.append(page)
                    seen_ids.add(page.id)

        return all_pages
