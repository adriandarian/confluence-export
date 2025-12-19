"""Tests for export manifest generation."""

import json
from pathlib import Path

from confluence_export.fetcher import PageData
from confluence_export.manifest import ExportManifest


class TestExportManifest:
    """Tests for ExportManifest class."""

    def test_create_manifest(self, temp_output_dir):
        """Test creating a manifest instance."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown", "html"],
            include_children=True,
            flat=False,
        )

        assert manifest.output_dir == temp_output_dir
        assert manifest.base_url == "https://example.atlassian.net"
        assert manifest.formats == ["markdown", "html"]
        assert manifest.include_children is True
        assert manifest.flat is False

    def test_add_pages(self, temp_output_dir):
        """Test adding pages to manifest."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        pages = [
            PageData(id="1", title="Page 1", body_storage="<p>Content 1</p>"),
            PageData(id="2", title="Page 2", body_storage="<p>Content 2</p>"),
        ]
        manifest.add_pages(pages)

        assert len(manifest.pages) == 2
        assert manifest.pages[0].id == "1"
        assert manifest.pages[1].id == "2"

    def test_add_export_result(self, temp_output_dir):
        """Test recording successful exports."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        manifest.add_export_result("123", "Test Page", "markdown", "/path/to/file.md")

        assert len(manifest.exported_files) == 1
        assert manifest.exported_files[0]["page_id"] == "123"
        assert manifest.exported_files[0]["title"] == "Test Page"
        assert manifest.exported_files[0]["format"] == "markdown"
        assert manifest.exported_files[0]["path"] == "/path/to/file.md"

    def test_add_export_failure(self, temp_output_dir):
        """Test recording failed exports."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        manifest.add_export_failure("123", "Test Page", "pdf", "PDF export failed")

        assert len(manifest.failed_exports) == 1
        assert manifest.failed_exports[0]["page_id"] == "123"
        assert manifest.failed_exports[0]["error"] == "PDF export failed"

    def test_generate_manifest(self, temp_output_dir):
        """Test generating manifest data structure."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown", "html"],
            include_children=True,
            flat=False,
        )

        pages = [
            PageData(id="1", title="Root Page", body_storage="<p>Root</p>"),
            PageData(
                id="2",
                title="Child Page",
                body_storage="<p>Child</p>",
                parent_id="1",
                hierarchy_path=["Root Page"],
                hierarchy_depth=1,
            ),
        ]
        manifest.add_pages(pages)
        manifest.add_export_result(
            "1", "Root Page", "markdown", f"{temp_output_dir}/Root-Page-1.md"
        )
        manifest.add_export_result(
            "2", "Child Page", "markdown", f"{temp_output_dir}/Child-Page-2.md"
        )

        data = manifest.generate()

        assert data["manifest_version"] == "1.0"
        assert "generated_at" in data
        assert data["export_info"]["base_url"] == "https://example.atlassian.net"
        assert data["export_info"]["formats"] == ["markdown", "html"]
        assert data["export_info"]["include_children"] is True
        assert data["statistics"]["total_pages"] == 2
        assert data["statistics"]["total_files"] == 2
        assert len(data["pages"]) == 2
        assert len(data["hierarchy"]) == 1  # Only root pages at top level

    def test_save_json(self, temp_output_dir):
        """Test saving manifest as JSON."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        pages = [PageData(id="1", title="Test Page", body_storage="<p>Test</p>")]
        manifest.add_pages(pages)
        manifest.add_export_result("1", "Test Page", "markdown", f"{temp_output_dir}/test.md")

        json_path = manifest.save_json()

        assert Path(json_path).exists()
        with Path(json_path).open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["manifest_version"] == "1.0"
        assert data["statistics"]["total_pages"] == 1

    def test_save_markdown(self, temp_output_dir):
        """Test saving manifest as Markdown index."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        pages = [PageData(id="1", title="Test Page", body_storage="<p>Test</p>")]
        manifest.add_pages(pages)
        manifest.add_export_result("1", "Test Page", "markdown", f"{temp_output_dir}/test.md")

        md_path = manifest.save_markdown()

        assert Path(md_path).exists()
        content = Path(md_path).read_text(encoding="utf-8")
        assert "# Export Index" in content
        assert "Test Page" in content
        assert "https://example.atlassian.net" in content

    def test_save_both_formats(self, temp_output_dir):
        """Test saving both JSON and Markdown manifest."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        pages = [PageData(id="1", title="Test Page", body_storage="<p>Test</p>")]
        manifest.add_pages(pages)

        paths = manifest.save()

        assert "json" in paths
        assert "markdown" in paths
        assert Path(paths["json"]).exists()
        assert Path(paths["markdown"]).exists()

    def test_hierarchy_building(self, temp_output_dir):
        """Test that hierarchy is correctly built from pages."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
        )

        pages = [
            PageData(id="1", title="Root 1", body_storage="<p>Root 1</p>"),
            PageData(
                id="2",
                title="Child 1.1",
                body_storage="<p>Child</p>",
                parent_id="1",
                hierarchy_depth=1,
            ),
            PageData(
                id="3",
                title="Child 1.2",
                body_storage="<p>Child</p>",
                parent_id="1",
                hierarchy_depth=1,
            ),
            PageData(id="4", title="Root 2", body_storage="<p>Root 2</p>"),
        ]
        manifest.add_pages(pages)

        data = manifest.generate()

        # Should have 2 root nodes
        assert len(data["hierarchy"]) == 2
        # Find Root 1
        root1 = next(h for h in data["hierarchy"] if h["title"] == "Root 1")
        assert len(root1["children"]) == 2

    def test_manifest_with_errors(self, temp_output_dir):
        """Test manifest includes errors when exports fail."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown", "pdf"],
        )

        pages = [PageData(id="1", title="Test Page", body_storage="<p>Test</p>")]
        manifest.add_pages(pages)
        manifest.add_export_result("1", "Test Page", "markdown", f"{temp_output_dir}/test.md")
        manifest.add_export_failure("1", "Test Page", "pdf", "PDF export not available")

        data = manifest.generate()

        assert data["statistics"]["failed_exports"] == 1
        assert "errors" in data
        assert len(data["errors"]) == 1
        assert data["errors"][0]["format"] == "pdf"


class TestManifestMarkdownOutput:
    """Tests for Markdown output format."""

    def test_markdown_contains_all_sections(self, temp_output_dir):
        """Test that Markdown output contains all expected sections."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["markdown"],
            include_children=True,
        )

        pages = [
            PageData(id="1", title="Root", body_storage="<p>Root</p>"),
            PageData(
                id="2",
                title="Child",
                body_storage="<p>Child</p>",
                parent_id="1",
                hierarchy_path=["Root"],
                hierarchy_depth=1,
            ),
        ]
        manifest.add_pages(pages)
        manifest.add_export_result("1", "Root", "markdown", f"{temp_output_dir}/Root-1.md")
        manifest.add_export_result("2", "Child", "markdown", f"{temp_output_dir}/Child-2.md")

        md_path = manifest.save_markdown()
        content = Path(md_path).read_text(encoding="utf-8")

        assert "# Export Index" in content
        assert "## Export Information" in content
        assert "## Statistics" in content
        assert "## Page Hierarchy" in content
        assert "## Exported Files" in content
        assert "Include Children**: Yes" in content

    def test_markdown_error_section(self, temp_output_dir):
        """Test that errors section appears when there are failures."""
        manifest = ExportManifest(
            output_dir=temp_output_dir,
            base_url="https://example.atlassian.net",
            formats=["pdf"],
        )

        pages = [PageData(id="1", title="Test", body_storage="<p>Test</p>")]
        manifest.add_pages(pages)
        manifest.add_export_failure("1", "Test", "pdf", "Export failed")

        md_path = manifest.save_markdown()
        content = Path(md_path).read_text(encoding="utf-8")

        assert "## Errors" in content
        assert "Export failed" in content
