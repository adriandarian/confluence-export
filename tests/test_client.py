"""Tests for Confluence API client."""

import pytest
import responses
from requests.exceptions import ConnectionError

from confluence_export.client import ConfluenceAPIError, ConfluenceClient


class TestConfluenceClient:
    """Tests for ConfluenceClient class."""

    def test_init_creates_session_with_auth(self):
        """Test that client initializes with proper authentication."""
        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        assert client.base_url == "https://example.atlassian.net"
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"].startswith("Basic ")

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL."""
        client = ConfluenceClient(
            base_url="https://example.atlassian.net/",
            email="test@example.com",
            api_token="test-token",
        )

        assert client.base_url == "https://example.atlassian.net"


class TestConfluenceClientRequests:
    """Tests for ConfluenceClient HTTP requests."""

    @responses.activate
    def test_get_page_success(self):
        """Test successful page retrieval."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={
                "id": "12345",
                "title": "Test Page",
                "spaceId": "TEST",
            },
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        result = client.get_page("12345", include_body=False)

        assert result["id"] == "12345"
        assert result["title"] == "Test Page"

    @responses.activate
    def test_get_page_body(self):
        """Test page body retrieval."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={
                "id": "12345",
                "title": "Test Page",
                "body": {
                    "storage": {
                        "value": "<p>Hello World</p>",
                    },
                },
            },
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        result = client.get_page_body("12345", body_format="storage")

        assert result == "<p>Hello World</p>"

    @responses.activate
    def test_get_page_children(self):
        """Test fetching page children."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345/children",
            json={
                "results": [
                    {"id": "22222", "title": "Child 1"},
                    {"id": "33333", "title": "Child 2"},
                ],
                "_links": {},
            },
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        result = client.get_page_children("12345")

        assert len(result) == 2
        assert result[0]["id"] == "22222"
        assert result[1]["id"] == "33333"

    @responses.activate
    def test_get_page_children_pagination(self):
        """Test fetching page children with pagination."""
        # First page
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345/children",
            json={
                "results": [{"id": "22222", "title": "Child 1"}],
                "_links": {"next": "/pages/12345/children?cursor=abc123"},
            },
            status=200,
        )
        # Second page
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345/children",
            json={
                "results": [{"id": "33333", "title": "Child 2"}],
                "_links": {},
            },
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        result = client.get_page_children("12345")

        assert len(result) == 2

    @responses.activate
    def test_api_error_handling(self):
        """Test that API errors are properly raised."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/99999",
            json={"message": "Page not found"},
            status=404,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        with pytest.raises(ConfluenceAPIError) as exc_info:
            client.get_page("99999")

        assert exc_info.value.status_code == 404

    @responses.activate
    def test_rate_limiting_retry(self):
        """Test that rate limiting triggers retry."""
        # First request returns 429
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            status=429,
            headers={"Retry-After": "0"},
        )
        # Second request succeeds
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "title": "Test"},
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
            retry_delay=0.01,
        )

        result = client.get_page("12345", include_body=False)

        assert result["id"] == "12345"

    @responses.activate
    def test_connection_error_retries(self):
        """Test that connection errors trigger retries."""
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            body=ConnectionError("Connection failed"),
        )
        responses.add(
            responses.GET,
            "https://example.atlassian.net/wiki/api/v2/pages/12345",
            json={"id": "12345", "title": "Test"},
            status=200,
        )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
            retry_delay=0.01,
        )

        result = client.get_page("12345", include_body=False)

        assert result["id"] == "12345"

    @responses.activate
    def test_max_retries_exceeded(self):
        """Test that max retries raises error."""
        for _ in range(3):
            responses.add(
                responses.GET,
                "https://example.atlassian.net/wiki/api/v2/pages/12345",
                body=ConnectionError("Connection failed"),
            )

        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="test-token",
            max_retries=3,
            retry_delay=0.01,
        )

        with pytest.raises(ConfluenceAPIError) as exc_info:
            client.get_page("12345")

        assert "Request failed" in str(exc_info.value)


class TestConfluenceAPIError:
    """Tests for ConfluenceAPIError exception."""

    def test_error_with_message_only(self):
        """Test error with just a message."""
        error = ConfluenceAPIError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.status_code is None
        assert error.response is None

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = ConfluenceAPIError("Not found", status_code=404)
        assert error.status_code == 404

    def test_error_with_response(self):
        """Test error with response data."""
        response_data = {"message": "Detailed error"}
        error = ConfluenceAPIError("Error", status_code=500, response=response_data)
        assert error.response == response_data
