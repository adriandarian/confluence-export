"""Export manifest generator for documenting exported pages."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .fetcher import PageData


class ExportManifest:
    """
    Generates a manifest file documenting all exported pages.

    The manifest includes metadata about the export, a list of all pages,
    and their hierarchical structure.
    """

    def __init__(
        self,
        output_dir: str,
        base_url: str,
        formats: List[str],
        include_children: bool = False,
        flat: bool = False,
    ):
        """
        Initialize the manifest generator.

        Args:
            output_dir: The output directory for exports
            base_url: The Confluence base URL
            formats: List of export formats used
            include_children: Whether child pages were included
            flat: Whether flat structure was used
        """
        self.output_dir = output_dir
        self.base_url = base_url
        self.formats = formats
        self.include_children = include_children
        self.flat = flat
        self.start_time = datetime.now(timezone.utc)
        self.pages: List[PageData] = []
        self.exported_files: List[Dict[str, Any]] = []
        self.failed_exports: List[Dict[str, Any]] = []

    def add_pages(self, pages: List[PageData]) -> None:
        """Add pages to the manifest."""
        self.pages = pages

    def add_export_result(
        self,
        page_id: str,
        title: str,
        format_name: str,
        path: str,
    ) -> None:
        """Record a successful export."""
        self.exported_files.append(
            {
                "page_id": page_id,
                "title": title,
                "format": format_name,
                "path": path,
            }
        )

    def add_export_failure(
        self,
        page_id: str,
        title: str,
        format_name: str,
        error: str,
    ) -> None:
        """Record a failed export."""
        self.failed_exports.append(
            {
                "page_id": page_id,
                "title": title,
                "format": format_name,
                "error": error,
            }
        )

    def _build_hierarchy(self) -> List[Dict[str, Any]]:
        """Build a hierarchical tree structure of pages."""
        # Create a map of pages by ID
        page_map = {p.id: p for p in self.pages}

        # Find root pages (no parent or parent not in export)
        roots = []
        children_map: Dict[str, List[PageData]] = {}

        for page in self.pages:
            if page.parent_id and page.parent_id in page_map:
                if page.parent_id not in children_map:
                    children_map[page.parent_id] = []
                children_map[page.parent_id].append(page)
            else:
                roots.append(page)

        def build_tree(page: PageData) -> Dict[str, Any]:
            node = {
                "id": page.id,
                "title": page.title,
                "depth": page.hierarchy_depth,
            }
            if page.id in children_map:
                node["children"] = [
                    build_tree(child)
                    for child in sorted(children_map[page.id], key=lambda p: p.title)
                ]
            return node

        return [build_tree(root) for root in sorted(roots, key=lambda p: p.title)]

    def _get_files_by_page(self) -> Dict[str, List[Dict[str, str]]]:
        """Group exported files by page ID."""
        files_by_page: Dict[str, List[Dict[str, str]]] = {}
        for export in self.exported_files:
            page_id = export["page_id"]
            if page_id not in files_by_page:
                files_by_page[page_id] = []
            files_by_page[page_id].append(
                {
                    "format": export["format"],
                    "path": export["path"],
                }
            )
        return files_by_page

    def generate(self) -> Dict[str, Any]:
        """
        Generate the manifest data structure.

        Returns:
            Dictionary containing the complete manifest
        """
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()

        files_by_page = self._get_files_by_page()

        # Build pages list with export info
        pages_list = []
        for page in self.pages:
            page_info = {
                "id": page.id,
                "title": page.title,
                "space_key": page.space_key,
                "hierarchy_path": page.hierarchy_path,
                "hierarchy_depth": page.hierarchy_depth,
                "parent_id": page.parent_id,
                "files": files_by_page.get(page.id, []),
            }
            pages_list.append(page_info)

        manifest = {
            "manifest_version": "1.0",
            "generated_at": end_time.isoformat(),
            "export_info": {
                "base_url": self.base_url,
                "output_directory": self.output_dir,
                "formats": self.formats,
                "include_children": self.include_children,
                "flat_structure": self.flat,
                "duration_seconds": round(duration, 2),
            },
            "statistics": {
                "total_pages": len(self.pages),
                "total_files": len(self.exported_files),
                "failed_exports": len(self.failed_exports),
                "formats_used": list({e["format"] for e in self.exported_files}),
            },
            "pages": pages_list,
            "hierarchy": self._build_hierarchy(),
        }

        if self.failed_exports:
            manifest["errors"] = self.failed_exports

        return manifest

    def save_json(self, filename: str = "manifest.json") -> str:
        """
        Save the manifest as a JSON file.

        Args:
            filename: Name of the manifest file

        Returns:
            Path to the saved manifest
        """
        manifest = self.generate()
        output_path = Path(self.output_dir) / filename

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def save_markdown(self, filename: str = "INDEX.md") -> str:
        """
        Save the manifest as a Markdown index file.

        Args:
            filename: Name of the index file

        Returns:
            Path to the saved index
        """
        manifest = self.generate()
        output_path = Path(self.output_dir) / filename

        lines = [
            "# Export Index",
            "",
            f"Generated: {manifest['generated_at']}",
            "",
            "## Export Information",
            "",
            f"- **Source**: {manifest['export_info']['base_url']}",
            f"- **Formats**: {', '.join(manifest['export_info']['formats'])}",
            f"- **Include Children**: {'Yes' if manifest['export_info']['include_children'] else 'No'}",
            f"- **Structure**: {'Flat' if manifest['export_info']['flat_structure'] else 'Hierarchical'}",
            f"- **Duration**: {manifest['export_info']['duration_seconds']}s",
            "",
            "## Statistics",
            "",
            f"- **Total Pages**: {manifest['statistics']['total_pages']}",
            f"- **Total Files**: {manifest['statistics']['total_files']}",
            f"- **Failed**: {manifest['statistics']['failed_exports']}",
            "",
        ]

        # Add hierarchy section
        lines.extend(
            [
                "## Page Hierarchy",
                "",
            ]
        )

        def render_hierarchy(nodes: List[Dict], indent: int = 0) -> List[str]:
            result = []
            for node in nodes:
                prefix = "  " * indent
                result.append(f"{prefix}- **{node['title']}** (ID: {node['id']})")
                if "children" in node:
                    result.extend(render_hierarchy(node["children"], indent + 1))
            return result

        lines.extend(render_hierarchy(manifest["hierarchy"]))
        lines.append("")

        # Add pages with files
        lines.extend(
            [
                "## Exported Files",
                "",
            ]
        )

        for page in manifest["pages"]:
            if page["files"]:
                lines.append(f"### {page['title']}")
                lines.append("")
                for file_info in page["files"]:
                    # Make path relative for display
                    rel_path = file_info["path"]
                    if rel_path.startswith(self.output_dir):
                        rel_path = rel_path[len(self.output_dir) :].lstrip("/\\")
                    lines.append(f"- [{file_info['format']}]({rel_path})")
                lines.append("")

        # Add errors if any
        if manifest.get("errors"):
            lines.extend(
                [
                    "## Errors",
                    "",
                ]
            )
            for error in manifest["errors"]:
                lines.append(f"- **{error['title']}** ({error['format']}): {error['error']}")
            lines.append("")

        with output_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(output_path)

    def save(
        self, json_filename: str = "manifest.json", md_filename: str = "INDEX.md"
    ) -> Dict[str, str]:
        """
        Save both JSON and Markdown manifest files.

        Args:
            json_filename: Name for the JSON manifest
            md_filename: Name for the Markdown index

        Returns:
            Dictionary with paths to both files
        """
        return {
            "json": self.save_json(json_filename),
            "markdown": self.save_markdown(md_filename),
        }
