"""Page fetcher for retrieving Confluence pages."""

import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .client import ConfluenceAPIError, ConfluenceClient


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
    """

    def __init__(self, client: ConfluenceClient, verbose: bool = False):
        """
        Initialize the page fetcher.

        Args:
            client: The Confluence API client
            verbose: Whether to print progress messages
        """
        self.client = client
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(message, file=sys.stderr)

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

        page_data = self.client.get_page(page_id, include_body=False)

        body = ""
        if include_body:
            body = self.client.get_page_body(page_id, body_format="storage")

        return PageData.from_api_response(page_data, body)

    def fetch_multiple_pages(
        self, page_ids: List[str], include_body: bool = True, skip_errors: bool = True
    ) -> List[PageData]:
        """
        Fetch multiple pages by their IDs.

        Args:
            page_ids: List of page IDs to fetch
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch; otherwise raise

        Returns:
            List of PageData instances
        """
        pages = []

        for i, page_id in enumerate(page_ids, 1):
            self._log(f"Fetching page {i}/{len(page_ids)}: {page_id}")

            try:
                page = self.fetch_single_page(page_id, include_body=include_body)
                pages.append(page)
            except ConfluenceAPIError as e:
                if skip_errors:
                    self._log(f"Warning: Failed to fetch page {page_id}: {e}")
                else:
                    raise

        return pages

    def fetch_with_children(
        self,
        page_id: str,
        include_root: bool = True,
        include_body: bool = True,
        skip_errors: bool = True,
    ) -> List[PageData]:
        """
        Fetch a page and all its descendant pages.

        Args:
            page_id: The root page ID
            include_root: Whether to include the root page itself
            include_body: Whether to fetch the page body content
            skip_errors: If True, skip pages that fail to fetch; otherwise raise

        Returns:
            List of PageData instances (root first if included, then descendants)
        """
        pages = []

        # Fetch root page if requested
        if include_root:
            self._log(f"Fetching root page {page_id}...")
            try:
                root_page = self.fetch_single_page(page_id, include_body=include_body)
                pages.append(root_page)
            except ConfluenceAPIError as e:
                if skip_errors:
                    self._log(f"Warning: Failed to fetch root page {page_id}: {e}")
                else:
                    raise

        # Fetch all descendants
        self._log(f"Fetching descendants of page {page_id}...")

        # Get root page title for hierarchy path
        root_title = ""
        if pages:
            root_title = pages[0].title
        else:
            try:
                root_data = self.client.get_page(page_id, include_body=False)
                root_title = root_data.get("title", "")
            except ConfluenceAPIError:
                pass

        descendants = self._fetch_descendants_recursive(
            page_id,
            parent_path=[root_title] if root_title else [],
            include_body=include_body,
            skip_errors=skip_errors,
        )

        pages.extend(descendants)
        self._log(f"Found {len(pages)} total pages")

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
        Recursively fetch all descendants of a page.

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

            self._log(f"  {'  ' * depth}Fetching: {child_title}")

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
        Fetch pages with optional children.

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

        for page_id in page_ids:
            if page_id in seen_ids:
                continue

            if include_children:
                pages = self.fetch_with_children(
                    page_id, include_root=True, include_body=include_body, skip_errors=skip_errors
                )
            else:
                try:
                    pages = [self.fetch_single_page(page_id, include_body=include_body)]
                except ConfluenceAPIError as e:
                    if skip_errors:
                        self._log(f"Warning: Failed to fetch page {page_id}: {e}")
                        continue
                    raise

            for page in pages:
                if page.id not in seen_ids:
                    all_pages.append(page)
                    seen_ids.add(page.id)

        return all_pages
