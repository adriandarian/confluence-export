"""Tests for page fetcher."""

import responses

from confluence_export.client import ConfluenceClient
from confluence_export.fetcher import PageData, PageFetcher


class TestPageData:
    """Tests for PageData dataclass."""

    def test_create_page_data(self):
        """Test creating PageData instance."""
        page = PageData(
            id="12345",
            title="Test Page",
            space_key="TEST",
            body_storage="<p>Content</p>",
        )

        assert page.id == "12345"
        assert page.title == "Test Page"
        assert page.space_key == "TEST"
        assert page.body_storage == "<p>Content</p>"
        assert page.hierarchy_path == []
        assert page.hierarchy_depth == 0

    def test_from_api_response(self):
        """Test creating PageData from API response."""
        response = {
            "id": "12345",
            "title": "Test Page",
            "spaceId": "TEST",
            "parentId": "11111",
            "_hierarchy_path": ["Parent"],
            "_hierarchy_depth": 1,
        }

        page = PageData.from_api_response(response, body="<p>Hello</p>")

        assert page.id == "12345"
        assert page.title == "Test Page"
        assert page.space_key == "TEST"
        assert page.body_storage == "<p>Hello</p>"
        assert page.hierarchy_path == ["Parent"]
        assert page.hierarchy_depth == 1
        assert page.parent_id == "11111"

    def test_from_api_response_with_space_dict(self):
        """Test creating PageData when space is a dict."""
        response = {
            "id": "12345",
            "title": "Test Page",
            "space": {"key": "SPACE"},
        }

        page = PageData.from_api_response(response)

        assert page.space_key == "SPACE"

    def test_from_api_response_defaults(self):
        """Test defaults when API response has missing fields."""
        response = {}

        page = PageData.from_api_response(response)

        assert page.id == ""
        assert page.title == "Untitled"
        assert page.space_key is None
        assert page.hierarchy_path == []


class TestPageFetcher:
    """Tests for PageFetcher class."""

    @responses.activate
    def test_fetch_single_page(self):
        """Test fetching a single page."""
        # Mock page metadata
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "title": "Test Page", "spaceId": "TEST"},
            status=200,
        )
        # Mock page body
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={
                "id": "12345",
                "body": {"storage": {"value": "<p>Content</p>"}},
            },
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client)

        page = fetcher.fetch_single_page("12345")

        assert page.id == "12345"
        assert page.title == "Test Page"
        assert page.body_storage == "<p>Content</p>"

    @responses.activate
    def test_fetch_single_page_without_body(self):
        """Test fetching a page without body content."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "title": "Test Page"},
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client)

        page = fetcher.fetch_single_page("12345", include_body=False)

        assert page.id == "12345"
        assert page.body_storage == ""

    @responses.activate
    def test_fetch_multiple_pages(self):
        """Test fetching multiple pages."""
        for page_id, title in [("111", "Page 1"), ("222", "Page 2")]:
            responses.add(
                responses.GET,
                f"https://example.atlassian.net/wiki/api/v2/pages/{page_id}",
                json={"id": page_id, "title": title},
                status=200,
            )
            responses.add(
                responses.GET,
                f"https://example.atlassian.net/wiki/api/v2/pages/{page_id}",
                json={"id": page_id, "body": {"storage": {"value": f"<p>{title}</p>"}}},
                status=200,
            )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client)

        pages = fetcher.fetch_multiple_pages(["111", "222"])

        assert len(pages) == 2
        assert pages[0].title == "Page 1"
        assert pages[1].title == "Page 2"

    @responses.activate
    def test_fetch_multiple_pages_skip_errors(self):
        """Test that errors are skipped when skip_errors=True."""
        # First page succeeds
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/111",
            json={"id": "111", "title": "Page 1"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/111",
            json={"id": "111", "body": {"storage": {"value": ""}}},
            status=200,
        )
        # Second page fails
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/222",
            json={"message": "Not found"},
            status=404,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client)

        pages = fetcher.fetch_multiple_pages(["111", "222"], skip_errors=True)

        assert len(pages) == 1
        assert pages[0].id == "111"

    @responses.activate
    def test_fetch_with_children(self):
        """Test fetching a page with its children."""
        # Root page
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/100",
            json={"id": "100", "title": "Root"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/100",
            json={"id": "100", "body": {"storage": {"value": "<p>Root content</p>"}}},
            status=200,
        )
        # Root's children
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/100/children",
            json={
                "results": [{"id": "101", "title": "Child 1"}],
                "_links": {},
            },
            status=200,
        )
        # Child page body
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/101",
            json={"id": "101", "body": {"storage": {"value": "<p>Child content</p>"}}},
            status=200,
        )
        # Child's children (none)
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/101/children",
            json={"results": [], "_links": {}},
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client)

        pages = fetcher.fetch_with_children("100")

        assert len(pages) == 2
        assert pages[0].id == "100"
        assert pages[0].title == "Root"
        assert pages[1].id == "101"
        assert pages[1].hierarchy_path == ["Root"]


class TestPageFetcherVerbose:
    """Tests for PageFetcher verbose mode."""

    @responses.activate
    def test_verbose_mode_logs_messages(self, capsys):
        """Test that verbose mode prints progress messages."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "title": "Test"},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "body": {"storage": {"value": ""}}},
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )
        fetcher = PageFetcher(client, verbose=True)

        fetcher.fetch_single_page("12345")

        captured = capsys.readouterr()
        assert "Fetching page 12345" in captured.err
