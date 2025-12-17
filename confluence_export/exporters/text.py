"""Plain text exporter for Confluence content."""

import re
from bs4 import BeautifulSoup

from ..fetcher import PageData
from .base import BaseExporter


class TextExporter(BaseExporter):
    """Export Confluence pages as plain text files."""
    
    format_name = "txt"
    file_extension = "txt"
    
    def __init__(
        self,
        output_dir: str,
        flat: bool = False,
        include_title: bool = True,
        preserve_structure: bool = True
    ):
        """
        Initialize the text exporter.
        
        Args:
            output_dir: Base output directory
            flat: If True, use flat structure
            include_title: If True, include page title at the top
            preserve_structure: If True, try to preserve some document structure
        """
        super().__init__(output_dir, flat)
        self.include_title = include_title
        self.preserve_structure = preserve_structure
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert HTML content to plain text.
        
        Args:
            html_content: The HTML content
            
        Returns:
            Plain text representation
        """
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()
        
        if self.preserve_structure:
            # Add newlines around block elements
            for tag in soup.find_all(["p", "div", "br", "li", "tr"]):
                tag.insert_after("\n")
            
            # Add extra newlines around headers
            for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                tag.insert_before("\n\n")
                tag.insert_after("\n")
            
            # Handle list items
            for li in soup.find_all("li"):
                li.insert_before("• ")
            
            # Handle table cells
            for td in soup.find_all(["td", "th"]):
                td.insert_after("\t")
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        # Replace multiple spaces with single space
        text = re.sub(r"[ \t]+", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n", "\n\n", text)
        # Strip leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def convert(self, page: PageData) -> bytes:
        """
        Convert page content to plain text.
        
        Args:
            page: The page data to convert
            
        Returns:
            Plain text content as bytes
        """
        parts = []
        
        if self.include_title:
            parts.append(page.title)
            parts.append("=" * len(page.title))
            parts.append("")
        
        text_content = self._html_to_text(page.body_storage)
        parts.append(text_content)
        
        content = "\n".join(parts)
        return content.encode("utf-8")

