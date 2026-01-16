"""Confluence API client for interacting with Confluence Cloud."""

import base64
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests


class ConfluenceAPIError(Exception):
    """Exception raised for Confluence API errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ConfluenceClient:
    """
    Client for interacting with the Confluence Cloud REST API.

    Handles authentication and provides methods for fetching pages
    and their content.
    """

    API_V2_PATH = "/wiki/api/v2"
    API_V1_PATH = "/wiki/rest/api"

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the Confluence client.

        Args:
            base_url: The Confluence site URL (e.g., https://yoursite.atlassian.net)
            email: Atlassian account email
            api_token: Atlassian API token
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create auth header
        credentials = f"{email}:{api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Basic {encoded_credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        api_version: str = "v2",
        params: Optional[Dict[str, Any]] = None,
        accept: Optional[str] = None,
        stream: bool = False,
    ) -> requests.Response:
        """
        Make an HTTP request to the Confluence API with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            api_version: API version to use ('v1' or 'v2')
            params: Query parameters
            accept: Override Accept header
            stream: Whether to stream the response

        Returns:
            The response object

        Raises:
            ConfluenceAPIError: If the request fails after all retries
        """
        api_path = self.API_V2_PATH if api_version == "v2" else self.API_V1_PATH
        url = urljoin(self.base_url, f"{api_path}{endpoint}")

        headers = {}
        if accept:
            headers["Accept"] = accept

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers if headers else None,
                    stream=stream,
                    timeout=30,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", self.retry_delay * (2**attempt))
                    )
                    time.sleep(retry_after)
                    continue

                # Raise for other error status codes
                if response.status_code >= 400:
                    error_msg = f"API request failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = f"{error_msg}: {error_data['message']}"
                    except ValueError:
                        pass
                    raise ConfluenceAPIError(
                        error_msg, response.status_code, response.json() if response.text else None
                    )

                return response

            except requests.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))
                    continue
                raise ConfluenceAPIError(f"Request failed: {e!s}") from e

        raise ConfluenceAPIError(
            f"Request failed after {self.max_retries} attempts: {last_exception!s}"
        )

    def get_content_info(self, content_id: str) -> Dict[str, Any]:
        """
        Get content info (page or folder) by its ID using v1 API.

        Args:
            content_id: The content ID (page or folder)

        Returns:
            Content data dictionary with type information
        """
        params = {"expand": "space"}
        response = self._make_request("GET", f"/content/{content_id}", api_version="v1", params=params)
        return response.json()

    def get_page(self, page_id: str, include_body: bool = True) -> Dict[str, Any]:
        """
        Get a page by its ID.

        Args:
            page_id: The page ID
            include_body: Whether to include the page body content

        Returns:
            Page data dictionary
        """
        params = {}
        if include_body:
            params["body-format"] = "storage"

        response = self._make_request("GET", f"/pages/{page_id}", params=params)
        return response.json()

    def get_page_body(self, page_id: str, body_format: str = "storage") -> str:
        """
        Get the body content of a page.

        Args:
            page_id: The page ID
            body_format: Format of the body ('storage', 'atlas_doc_format', 'view')

        Returns:
            The page body content as a string
        """
        # First get the page to get the body
        params = {"body-format": body_format}
        response = self._make_request("GET", f"/pages/{page_id}", params=params)
        data = response.json()

        # Extract body from the response
        if "body" in data:
            body_data = data["body"]
            if body_format in body_data:
                return body_data[body_format].get("value", "")

        return ""

    def get_folder_children(self, folder_id: str, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Get all child pages of a folder.

        Args:
            folder_id: The folder ID
            limit: Maximum number of children to fetch per request

        Returns:
            List of child page data dictionaries
        """
        children = []
        cursor = None

        while True:
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", f"/pages/{folder_id}/children", params=params)
            data = response.json()

            results = data.get("results", [])
            children.extend(results)

            # Check for more pages
            links = data.get("_links", {})
            if "next" not in links:
                break

            # Extract cursor from next link
            next_link = links["next"]
            if "cursor=" in next_link:
                cursor = next_link.split("cursor=")[1].split("&")[0]
            else:
                break

        return children

    def get_folder_contents_by_ancestor(self, folder_id: str, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Get all pages/folders under a folder using CQL ancestor search.

        Args:
            folder_id: The folder ID
            limit: Maximum number of items to fetch per request (default 250 for optimal API performance)

        Returns:
            List of page/folder data dictionaries
        """
        items = []
        start = 0

        while True:
            params = {
                "cql": f"ancestor = {folder_id}",
                "limit": limit,
                "start": start,
                "expand": "ancestors",
            }

            response = self._make_request("GET", "/content/search", api_version="v1", params=params)
            data = response.json()

            results = data.get("results", [])
            items.extend(results)

            # Check if there are more results
            if len(results) < limit:
                break

            start += limit

        return items

    def get_page_children(self, page_id: str, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Get all child pages of a page.

        Args:
            page_id: The parent page ID
            limit: Maximum number of children to fetch per request

        Returns:
            List of child page data dictionaries
        """
        children = []
        cursor = None

        while True:
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", f"/pages/{page_id}/children", params=params)
            data = response.json()

            results = data.get("results", [])
            children.extend(results)

            # Check for more pages
            links = data.get("_links", {})
            if "next" not in links:
                break

            # Extract cursor from next link
            next_link = links["next"]
            if "cursor=" in next_link:
                cursor = next_link.split("cursor=")[1].split("&")[0]
            else:
                break

        return children

    def get_all_descendants(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Recursively get all descendant pages of a page.

        Args:
            page_id: The root page ID

        Returns:
            List of all descendant page data dictionaries with hierarchy info
        """

        def _fetch_descendants(
            pid: str, depth: int = 0, path: Optional[List[str]] = None
        ) -> List[Dict[str, Any]]:
            if path is None:
                path = []

            descendants = []
            children = self.get_page_children(pid)

            for child in children:
                child["_hierarchy_depth"] = depth
                child["_hierarchy_path"] = path.copy()
                descendants.append(child)

                # Recursively get children
                child_path = [*path, child.get("title", "")]
                descendants.extend(_fetch_descendants(child["id"], depth + 1, child_path))

            return descendants

        return _fetch_descendants(page_id)

    def export_page_as_pdf(self, page_id: str) -> bytes:
        """
        Export a page as PDF using Confluence's PDF export.

        Note: PDF export in Confluence Cloud requires the page to be accessed
        via a special export URL. This method attempts multiple approaches.

        Args:
            page_id: The page ID to export

        Returns:
            PDF content as bytes

        Raises:
            ConfluenceAPIError: If PDF export fails
        """
        # Confluence Cloud PDF export URL format
        # Try the spaces/flyingpdf/pdfpageexport.action endpoint
        pdf_url = f"{self.base_url}/wiki/spaces/flyingpdf/pdfpageexport.action?pageId={page_id}"

        try:
            response = self.session.get(pdf_url, stream=True, timeout=60)
            if (
                response.status_code == 200
                and "pdf" in response.headers.get("Content-Type", "").lower()
            ):
                return response.content
        except requests.RequestException:
            pass

        # Fallback: Try the REST API v1 content export
        try:
            endpoint = f"/content/{page_id}/export/pdf"
            response = self._make_request(
                "GET", endpoint, api_version="v1", accept="application/pdf", stream=True
            )
            return response.content
        except ConfluenceAPIError:
            pass

        # Last resort: Try direct PDF rendering endpoint
        try:
            pdf_url = f"{self.base_url}/wiki/exportword?pageId={page_id}&export=pdf"
            response = self.session.get(pdf_url, stream=True, timeout=60)
            if response.status_code == 200:
                return response.content
        except requests.RequestException:
            pass

        raise ConfluenceAPIError(
            f"PDF export is not available for page {page_id}. "
            "This may require additional permissions or Confluence add-ons.",
            status_code=501,
        )

    def get_space_pages(self, space_key: str, limit: int = 250) -> List[Dict[str, Any]]:
        """
        Get all pages in a space.

        Args:
            space_key: The space key
            limit: Maximum number of pages to fetch per request

        Returns:
            List of page data dictionaries
        """
        pages = []
        cursor = None

        while True:
            params = {"space-key": space_key, "limit": limit}
            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", "/pages", params=params)
            data = response.json()

            results = data.get("results", [])
            pages.extend(results)

            # Check for more pages
            links = data.get("_links", {})
            if "next" not in links:
                break

            # Extract cursor from next link
            next_link = links["next"]
            if "cursor=" in next_link:
                cursor = next_link.split("cursor=")[1].split("&")[0]
            else:
                break

        return pages

    def test_connection(self) -> bool:
        """
        Test the connection and authentication.

        Returns:
            True if connection is successful

        Raises:
            ConfluenceAPIError: If connection fails
        """
        try:
            # Try to get current user info
            response = self._make_request("GET", "/users/current", api_version="v1")
            return response.status_code == 200
        except ConfluenceAPIError:
            raise
