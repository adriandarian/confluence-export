"""Shared fixtures for Confluence Export tests."""

import pytest

from confluence_export.client import ConfluenceClient
from confluence_export.fetcher import PageData


@pytest.fixture
def sample_page_data() -> PageData:
    """Create a sample PageData instance for testing."""
    return PageData(
        id="12345",
        title="Test Page",
        space_key="TEST",
        body_storage="<p>Hello <strong>World</strong></p>",
        hierarchy_path=["Parent", "Child"],
        hierarchy_depth=2,
        parent_id="11111",
    )


@pytest.fixture
def sample_page_with_complex_content() -> PageData:
    """Create a PageData with complex Confluence content."""
    return PageData(
        id="67890",
        title="Complex Page",
        space_key="TEST",
        body_storage="""
            <h1>Main Heading</h1>
            <p>Some introductory text.</p>
            <h2>Code Example</h2>
            <ac:structured-macro ac:name="code">
                <ac:parameter ac:name="language">python</ac:parameter>
                <ac:plain-text-body><![CDATA[def hello():
    print("Hello, World!")]]></ac:plain-text-body>
            </ac:structured-macro>
            <h2>Info Panel</h2>
            <ac:structured-macro ac:name="info">
                <ac:rich-text-body><p>This is important information.</p></ac:rich-text-body>
            </ac:structured-macro>
            <h2>Table</h2>
            <table>
                <tr><th>Name</th><th>Value</th></tr>
                <tr><td>Item 1</td><td>100</td></tr>
                <tr><td>Item 2</td><td>200</td></tr>
            </table>
            <h2>Links</h2>
            <p>See also: <ac:link><ri:page ri:content-title="Other Page"/></ac:link></p>
        """,
        hierarchy_path=[],
        hierarchy_depth=0,
    )


@pytest.fixture
def sample_api_response() -> dict:
    """Create a sample Confluence API response."""
    return {
        "id": "12345",
        "title": "Test Page",
        "spaceId": "TEST",
        "parentId": "11111",
        "status": "current",
        "_links": {
            "self": "https://example.atlassian.net/wiki/api/v2/pages/12345",
        },
    }


@pytest.fixture
def sample_children_response() -> dict:
    """Create a sample children API response."""
    return {
        "results": [
            {"id": "22222", "title": "Child Page 1"},
            {"id": "33333", "title": "Child Page 2"},
            {"id": "44444", "title": "Child Page 3"},
        ],
        "_links": {},
    }


@pytest.fixture
def mock_client(mocker) -> ConfluenceClient:
    """Create a mocked ConfluenceClient."""
    # Patch the session to avoid real HTTP calls
    mocker.patch("requests.Session")

    client = ConfluenceClient(
        base_url="https://example.atlassian.net",
        email="test@example.com",
        api_token="fake-token",
    )
    return client


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for export tests."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return str(output_dir)
