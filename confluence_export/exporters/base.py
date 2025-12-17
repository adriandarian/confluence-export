"""Base exporter class for Confluence content."""

from abc import ABC, abstractmethod
from typing import Optional
import os

from ..fetcher import PageData
from ..utils import build_file_path, ensure_directory, get_extension_for_format


class BaseExporter(ABC):
    """Abstract base class for content exporters."""
    
    format_name: str = ""
    file_extension: str = ""
    
    def __init__(self, output_dir: str, flat: bool = False):
        """
        Initialize the exporter.
        
        Args:
            output_dir: Base output directory for exported files
            flat: If True, use flat structure; otherwise preserve hierarchy
        """
        self.output_dir = output_dir
        self.flat = flat
        ensure_directory(output_dir)
    
    @abstractmethod
    def convert(self, page: PageData) -> bytes:
        """
        Convert page content to the export format.
        
        Args:
            page: The page data to convert
            
        Returns:
            The converted content as bytes
        """
        pass
    
    def get_output_path(self, page: PageData) -> str:
        """
        Get the output file path for a page.
        
        Args:
            page: The page data
            
        Returns:
            Full path to the output file
        """
        return build_file_path(
            output_dir=self.output_dir,
            page_title=page.title,
            page_id=page.id,
            extension=self.file_extension,
            hierarchy_path=page.hierarchy_path,
            flat=self.flat
        )
    
    def export(self, page: PageData) -> str:
        """
        Export a page to a file.
        
        Args:
            page: The page data to export
            
        Returns:
            Path to the exported file
        """
        output_path = self.get_output_path(page)
        
        # Ensure directory exists
        dir_path = os.path.dirname(output_path)
        if dir_path:
            ensure_directory(dir_path)
        
        # Convert and write content
        content = self.convert(page)
        
        mode = "wb"
        with open(output_path, mode) as f:
            f.write(content)
        
        return output_path
    
    def export_all(self, pages: list) -> list:
        """
        Export multiple pages.
        
        Args:
            pages: List of PageData instances to export
            
        Returns:
            List of paths to exported files
        """
        paths = []
        for page in pages:
            path = self.export(page)
            paths.append(path)
        return paths

