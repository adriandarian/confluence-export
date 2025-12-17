"""HTML exporter for Confluence content."""

from ..fetcher import PageData
from .base import BaseExporter


class HTMLExporter(BaseExporter):
    """Export Confluence pages as HTML files."""
    
    format_name = "html"
    file_extension = "html"
    
    def __init__(
        self,
        output_dir: str,
        flat: bool = False,
        include_wrapper: bool = True,
        include_styles: bool = True
    ):
        """
        Initialize the HTML exporter.
        
        Args:
            output_dir: Base output directory
            flat: If True, use flat structure
            include_wrapper: If True, wrap content in full HTML document
            include_styles: If True, include basic CSS styles
        """
        super().__init__(output_dir, flat)
        self.include_wrapper = include_wrapper
        self.include_styles = include_styles
    
    def _get_styles(self) -> str:
        """Get CSS styles for the HTML document."""
        return """
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem;
                color: #333;
            }
            h1, h2, h3, h4, h5, h6 {
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                color: #1a1a1a;
            }
            h1 { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
            code {
                background-color: #f4f4f4;
                padding: 0.2em 0.4em;
                border-radius: 3px;
                font-family: 'SF Mono', Monaco, 'Courier New', monospace;
                font-size: 0.9em;
            }
            pre {
                background-color: #f4f4f4;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
            }
            pre code {
                padding: 0;
                background: none;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 0.75em;
                text-align: left;
            }
            th {
                background-color: #f4f4f4;
            }
            tr:nth-child(even) {
                background-color: #fafafa;
            }
            blockquote {
                border-left: 4px solid #ddd;
                margin: 1em 0;
                padding: 0.5em 1em;
                color: #666;
                background-color: #f9f9f9;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            a {
                color: #0066cc;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .confluence-information-macro,
            .confluence-information-macro-body {
                background-color: #e8f4fd;
                border: 1px solid #b8d4e8;
                border-radius: 4px;
                padding: 1em;
                margin: 1em 0;
            }
            .panel {
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 1em 0;
            }
            .panelHeader {
                background-color: #f4f4f4;
                padding: 0.5em 1em;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
            .panelContent {
                padding: 1em;
            }
        </style>
        """
    
    def _wrap_html(self, content: str, title: str) -> str:
        """
        Wrap content in a full HTML document.
        
        Args:
            content: The HTML content
            title: The page title
            
        Returns:
            Complete HTML document
        """
        styles = self._get_styles() if self.include_styles else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {styles}
</head>
<body>
    <article>
        <h1>{title}</h1>
        {content}
    </article>
</body>
</html>
"""
    
    def convert(self, page: PageData) -> bytes:
        """
        Convert page content to HTML.
        
        Args:
            page: The page data to convert
            
        Returns:
            HTML content as bytes
        """
        content = page.body_storage
        
        if self.include_wrapper:
            content = self._wrap_html(content, page.title)
        
        return content.encode("utf-8")

