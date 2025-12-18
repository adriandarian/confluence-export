"""PDF exporter for Confluence content."""

from typing import Optional

from ..client import ConfluenceClient
from ..fetcher import PageData
from .base import BaseExporter


class PDFExporter(BaseExporter):
    """Export Confluence pages as PDF files using Confluence's native export."""

    format_name = "pdf"
    file_extension = "pdf"

    def __init__(
        self, output_dir: str, flat: bool = False, client: Optional[ConfluenceClient] = None
    ):
        """
        Initialize the PDF exporter.

        Args:
            output_dir: Base output directory
            flat: If True, use flat structure
            client: Confluence API client (required for PDF export)
        """
        super().__init__(output_dir, flat)
        self._client = client

    @property
    def client(self) -> ConfluenceClient:
        """Get the Confluence client."""
        if self._client is None:
            raise ValueError("Confluence client is required for PDF export")
        return self._client

    @client.setter
    def client(self, value: ConfluenceClient) -> None:
        """Set the Confluence client."""
        self._client = value

    def convert(self, page: PageData) -> bytes:
        """
        Export page as PDF using Confluence's native export.

        Args:
            page: The page data to export

        Returns:
            PDF content as bytes
        """
        return self.client.export_page_as_pdf(page.id)
