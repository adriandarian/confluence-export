"""Tests for content exporters."""

from confluence_export.exporters import (
    HTMLExporter,
    MarkdownExporter,
    TextExporter,
)
from confluence_export.exporters.markdown import convert_confluence_to_markdown
from confluence_export.fetcher import PageData


class TestMarkdownConverter:
    """Tests for Confluence to Markdown conversion."""

    def test_empty_content(self):
        """Test that empty content returns empty string."""
        assert convert_confluence_to_markdown("") == ""
        assert convert_confluence_to_markdown(None) == ""

    def test_simple_paragraph(self):
        """Test simple paragraph conversion."""
        html = "<p>Hello World</p>"
        result = convert_confluence_to_markdown(html)
        assert "Hello World" in result

    def test_headings(self):
        """Test heading conversion."""
        html = "<h1>Heading 1</h1><h2>Heading 2</h2><h3>Heading 3</h3>"
        result = convert_confluence_to_markdown(html)
        assert "# Heading 1" in result
        assert "## Heading 2" in result
        assert "### Heading 3" in result

    def test_bold_and_italic(self):
        """Test bold and italic text."""
        html = "<p><strong>bold</strong> and <em>italic</em></p>"
        result = convert_confluence_to_markdown(html)
        assert "**bold**" in result
        assert "*italic*" in result or "_italic_" in result

    def test_links(self):
        """Test link conversion."""
        html = '<p><a href="https://example.com">Example</a></p>'
        result = convert_confluence_to_markdown(html)
        assert "[Example](https://example.com)" in result

    def test_code_block(self):
        """Test Confluence code macro conversion."""
        html = """
        <ac:structured-macro ac:name="code">
            <ac:parameter ac:name="language">python</ac:parameter>
            <ac:plain-text-body><![CDATA[print("hello")]]></ac:plain-text-body>
        </ac:structured-macro>
        """
        result = convert_confluence_to_markdown(html)
        assert "```python" in result
        assert 'print("hello")' in result
        assert "```" in result

    def test_info_panel(self):
        """Test Confluence info macro conversion."""
        html = """
        <ac:structured-macro ac:name="info">
            <ac:rich-text-body><p>Important note here.</p></ac:rich-text-body>
        </ac:structured-macro>
        """
        result = convert_confluence_to_markdown(html)
        assert "INFO" in result or "info" in result.lower()
        assert "Important note here" in result

    def test_warning_panel(self):
        """Test Confluence warning macro conversion."""
        html = """
        <ac:structured-macro ac:name="warning">
            <ac:rich-text-body><p>Warning message.</p></ac:rich-text-body>
        </ac:structured-macro>
        """
        result = convert_confluence_to_markdown(html)
        assert "WARNING" in result or "warning" in result.lower()

    def test_toc_macro(self):
        """Test TOC macro conversion."""
        html = '<ac:structured-macro ac:name="toc"></ac:structured-macro>'
        result = convert_confluence_to_markdown(html)
        assert "[TOC]" in result

    def test_expand_macro(self):
        """Test expand/collapse macro conversion."""
        html = """
        <ac:structured-macro ac:name="expand">
            <ac:parameter ac:name="title">Click to expand</ac:parameter>
            <ac:rich-text-body><p>Hidden content</p></ac:rich-text-body>
        </ac:structured-macro>
        """
        result = convert_confluence_to_markdown(html)
        # Expand macro extracts the title and content
        assert "Click to expand" in result
        assert "Hidden content" in result

    def test_confluence_image(self):
        """Test Confluence image conversion."""
        html = '<ac:image><ri:attachment ri:filename="image.png"/></ac:image>'
        result = convert_confluence_to_markdown(html)
        assert "![image.png](image.png)" in result

    def test_confluence_page_link(self):
        """Test Confluence page link conversion."""
        html = """
        <ac:link>
            <ri:page ri:content-title="Other Page"/>
            <ac:link-body>Link Text</ac:link-body>
        </ac:link>
        """
        result = convert_confluence_to_markdown(html)
        assert "[Link Text]" in result
        assert "Other-Page" in result or "Other Page" in result

    def test_user_mention(self):
        """Test user mention conversion."""
        html = '<ri:user ri:account-id="12345abc"/>'
        result = convert_confluence_to_markdown(html)
        assert "@12345abc" in result

    def test_task_list(self):
        """Test task list conversion."""
        html = """
        <ac:task-list>
            <ac:task>
                <ac:task-status>incomplete</ac:task-status>
                <ac:task-body>Todo item</ac:task-body>
            </ac:task>
            <ac:task>
                <ac:task-status>complete</ac:task-status>
                <ac:task-body>Done item</ac:task-body>
            </ac:task>
        </ac:task-list>
        """
        result = convert_confluence_to_markdown(html)
        # Task list items are converted to checkbox format
        assert "Todo item" in result
        assert "Done item" in result
        # At least one checkbox marker should be present
        assert "[x]" in result or "[ ]" in result

    def test_table(self):
        """Test table conversion."""
        html = """
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        """
        result = convert_confluence_to_markdown(html)
        assert "Header 1" in result
        assert "Cell 1" in result


class TestMarkdownExporter:
    """Tests for MarkdownExporter class."""

    def test_export_simple_page(self, sample_page_data, temp_output_dir):
        """Test exporting a simple page to Markdown."""
        from pathlib import Path

        exporter = MarkdownExporter(temp_output_dir)

        output_path = exporter.export(sample_page_data)

        output_path_str = str(output_path)
        assert output_path_str.endswith(".md")
        content = Path(output_path_str).read_text(encoding="utf-8")
        assert "# Test Page" in content
        assert "Hello" in content
        assert "World" in content

    def test_export_with_metadata(self, sample_page_data, temp_output_dir):
        """Test exporting with YAML frontmatter."""
        exporter = MarkdownExporter(temp_output_dir, include_metadata=True)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "---" in content
        assert 'title: "Test Page"' in content
        assert 'page_id: "12345"' in content
        assert 'space: "TEST"' in content

    def test_export_without_title(self, sample_page_data, temp_output_dir):
        """Test exporting without H1 title."""
        exporter = MarkdownExporter(temp_output_dir, include_title=False)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "# Test Page" not in content

    def test_hierarchical_output_path(self, sample_page_data, temp_output_dir):
        """Test that hierarchical pages create subdirectories."""
        exporter = MarkdownExporter(temp_output_dir, flat=False)

        output_path = exporter.get_output_path(sample_page_data)

        assert "Parent" in output_path
        assert "Child" in output_path


class TestHTMLExporter:
    """Tests for HTMLExporter class."""

    def test_export_with_wrapper(self, sample_page_data, temp_output_dir):
        """Test exporting with HTML document wrapper."""
        exporter = HTMLExporter(temp_output_dir, include_wrapper=True)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "<head>" in content
        assert "<title>Test Page</title>" in content
        assert "<body>" in content

    def test_export_with_styles(self, sample_page_data, temp_output_dir):
        """Test that styles are included when requested."""
        exporter = HTMLExporter(temp_output_dir, include_wrapper=True, include_styles=True)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "<style>" in content
        assert "font-family" in content

    def test_export_without_wrapper(self, sample_page_data, temp_output_dir):
        """Test exporting raw content without wrapper."""
        exporter = HTMLExporter(temp_output_dir, include_wrapper=False)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "<!DOCTYPE html>" not in content
        assert content == sample_page_data.body_storage

    def test_file_extension(self, temp_output_dir):
        """Test that HTML exporter uses .html extension."""
        exporter = HTMLExporter(temp_output_dir)
        assert exporter.file_extension == "html"


class TestTextExporter:
    """Tests for TextExporter class."""

    def test_export_simple_page(self, sample_page_data, temp_output_dir):
        """Test exporting a page as plain text."""
        exporter = TextExporter(temp_output_dir)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "Test Page" in content
        assert "Hello" in content
        assert "World" in content
        # Should not contain HTML tags
        assert "<p>" not in content
        assert "<strong>" not in content

    def test_export_with_title(self, sample_page_data, temp_output_dir):
        """Test that title is included with underline."""
        exporter = TextExporter(temp_output_dir, include_title=True)

        content = exporter.convert(sample_page_data).decode("utf-8")

        assert "Test Page" in content
        assert "=" * len("Test Page") in content

    def test_export_without_title(self, sample_page_data, temp_output_dir):
        """Test exporting without title header."""
        exporter = TextExporter(temp_output_dir, include_title=False)

        content = exporter.convert(sample_page_data).decode("utf-8")

        # Should not have the underline
        assert "=" * len("Test Page") not in content

    def test_strips_html_tags(self, temp_output_dir):
        """Test that HTML tags are properly stripped."""
        page = PageData(
            id="123",
            title="Test",
            body_storage="<div><p>Paragraph 1</p><p>Paragraph 2</p></div>",
        )
        exporter = TextExporter(temp_output_dir, include_title=False)

        content = exporter.convert(page).decode("utf-8")

        assert "<div>" not in content
        assert "<p>" not in content
        assert "Paragraph 1" in content
        assert "Paragraph 2" in content

    def test_file_extension(self, temp_output_dir):
        """Test that text exporter uses .txt extension."""
        exporter = TextExporter(temp_output_dir)
        assert exporter.file_extension == "txt"


class TestBaseExporter:
    """Tests for BaseExporter functionality."""

    def test_export_creates_directory(self, sample_page_data, temp_output_dir):
        """Test that export creates necessary directories."""
        exporter = MarkdownExporter(temp_output_dir, flat=False)

        output_path = exporter.export(sample_page_data)

        from pathlib import Path

        assert Path(output_path).exists()
        assert Path(output_path).parent.exists()

    def test_export_all(self, temp_output_dir):
        """Test exporting multiple pages."""
        pages = [
            PageData(id="1", title="Page 1", body_storage="<p>Content 1</p>"),
            PageData(id="2", title="Page 2", body_storage="<p>Content 2</p>"),
            PageData(id="3", title="Page 3", body_storage="<p>Content 3</p>"),
        ]
        exporter = MarkdownExporter(temp_output_dir)

        paths = exporter.export_all(pages)

        assert len(paths) == 3
        for path in paths:
            from pathlib import Path

            assert Path(path).exists()
