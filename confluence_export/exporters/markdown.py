"""Markdown exporter for Confluence content."""

import re

from markdownify import MarkdownConverter
from markdownify import markdownify as md

from ..fetcher import PageData
from .base import BaseExporter


class ConfluenceMarkdownConverter(MarkdownConverter):
    """Custom Markdown converter for Confluence-specific elements."""

    def convert_ac_structured_macro(self, el, text, convert_as_inline):
        """Handle Confluence structured macros."""
        macro_name = el.get("ac:name", "")

        if macro_name == "code":
            # Handle code blocks
            language = ""
            for param in el.find_all("ac:parameter"):
                if param.get("ac:name") == "language":
                    language = param.get_text()
                    break

            body = el.find("ac:plain-text-body")
            if body:
                code = body.get_text()
                return f"\n```{language}\n{code}\n```\n"

        elif macro_name in ("info", "note", "warning", "tip"):
            # Handle info/note/warning/tip panels
            body = el.find("ac:rich-text-body")
            if body:
                content = self.convert(body)
                prefix = f"**{macro_name.upper()}:** "
                return f"\n> {prefix}{content.strip()}\n\n"

        elif macro_name == "panel":
            body = el.find("ac:rich-text-body")
            if body:
                content = self.convert(body)
                return f"\n---\n{content.strip()}\n---\n\n"

        elif macro_name == "toc":
            return "\n[TOC]\n\n"

        elif macro_name == "expand":
            title = ""
            for param in el.find_all("ac:parameter"):
                if param.get("ac:name") == "title":
                    title = param.get_text()
                    break

            body = el.find("ac:rich-text-body")
            if body:
                content = self.convert(body)
                if title:
                    return f"\n<details>\n<summary>{title}</summary>\n\n{content.strip()}\n\n</details>\n\n"
                return f"\n{content.strip()}\n\n"

        # Default: just process the content
        return text

    def convert_ac_image(self, el, text, convert_as_inline):
        """Handle Confluence images."""
        ri_attachment = el.find("ri:attachment")
        if ri_attachment:
            filename = ri_attachment.get("ri:filename", "image")
            return f"![{filename}]({filename})"

        ri_url = el.find("ri:url")
        if ri_url:
            url = ri_url.get("ri:value", "")
            return f"![]({url})"

        return ""

    def convert_ac_link(self, el, text, convert_as_inline):
        """Handle Confluence links."""
        ri_page = el.find("ri:page")
        if ri_page:
            page_title = ri_page.get("ri:content-title", text or "link")
            # Create a wiki-style link
            link_text = el.find("ac:link-body") or el.find("ac:plain-text-link-body")
            display_text = link_text.get_text() if link_text else page_title
            return f"[{display_text}]({page_title.replace(' ', '-')})"

        ri_attachment = el.find("ri:attachment")
        if ri_attachment:
            filename = ri_attachment.get("ri:filename", "attachment")
            link_text = el.find("ac:link-body") or el.find("ac:plain-text-link-body")
            display_text = link_text.get_text() if link_text else filename
            return f"[{display_text}]({filename})"

        return text or ""

    def convert_ri_user(self, el, text, convert_as_inline):
        """Handle user mentions."""
        account_id = el.get("ri:account-id", "")
        return f"@{account_id}" if account_id else "@user"

    def convert_time(self, el, text, convert_as_inline):
        """Handle time/date elements."""
        datetime_val = el.get("datetime", "")
        return datetime_val or text

    def convert_ac_task_list(self, el, text, convert_as_inline):
        """Handle task lists."""
        return text

    def convert_ac_task(self, el, text, convert_as_inline):
        """Handle individual tasks."""
        # Find the task body
        body = el.find("ac:task-body")
        content = self.convert(body) if body else text

        # Check if completed
        status = el.find("ac:task-status")
        is_complete = status and status.get_text().lower() == "complete"

        checkbox = "[x]" if is_complete else "[ ]"
        return f"- {checkbox} {content.strip()}\n"


def convert_confluence_to_markdown(html_content: str) -> str:
    """
    Convert Confluence storage format HTML to Markdown.

    Args:
        html_content: The Confluence storage format HTML

    Returns:
        Markdown formatted text
    """
    if not html_content:
        return ""

    # Pre-process: handle Confluence-specific XML namespaces and macros
    processed_html = html_content

    # Handle code blocks specially before general processing
    def replace_code_macro(match):
        full_match = match.group(0)
        # Extract language parameter
        lang_match = re.search(r'ac:name="language"[^>]*>([^<]+)<', full_match)
        language = lang_match.group(1) if lang_match else ""
        # Extract code content
        code_match = re.search(
            r"<ac:plain-text-body[^>]*><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>",
            full_match,
            re.DOTALL,
        )
        if not code_match:
            code_match = re.search(
                r"<ac:plain-text-body[^>]*>(.*?)</ac:plain-text-body>", full_match, re.DOTALL
            )
        code = code_match.group(1) if code_match else ""
        return f"\n```{language}\n{code}\n```\n"

    # Replace code macros
    processed_html = re.sub(
        r'<ac:structured-macro[^>]*ac:name="code"[^>]*>.*?</ac:structured-macro>',
        replace_code_macro,
        processed_html,
        flags=re.DOTALL,
    )

    # Handle info/note/warning/tip panels
    def replace_panel_macro(match):
        full_match = match.group(0)
        macro_type_match = re.search(r'ac:name="(info|note|warning|tip)"', full_match)
        macro_type = macro_type_match.group(1).upper() if macro_type_match else "NOTE"
        # Extract body content
        body_match = re.search(
            r"<ac:rich-text-body[^>]*>(.*?)</ac:rich-text-body>", full_match, re.DOTALL
        )
        body = body_match.group(1) if body_match else ""
        # Simple HTML strip for the body
        body_text = re.sub(r"<[^>]+>", "", body).strip()
        return f"\n> **{macro_type}:** {body_text}\n\n"

    processed_html = re.sub(
        r'<ac:structured-macro[^>]*ac:name="(info|note|warning|tip)"[^>]*>.*?</ac:structured-macro>',
        replace_panel_macro,
        processed_html,
        flags=re.DOTALL,
    )

    # Handle TOC macro
    processed_html = re.sub(
        r'<ac:structured-macro[^>]*ac:name="toc"[^>]*>.*?</ac:structured-macro>',
        "\n[TOC]\n\n",
        processed_html,
        flags=re.DOTALL,
    )

    # Handle expand/collapse sections
    def replace_expand_macro(match):
        full_match = match.group(0)
        # Extract title
        title_match = re.search(r'ac:name="title"[^>]*>([^<]+)<', full_match)
        title = title_match.group(1) if title_match else "Details"
        # Extract body
        body_match = re.search(
            r"<ac:rich-text-body[^>]*>(.*?)</ac:rich-text-body>", full_match, re.DOTALL
        )
        body = body_match.group(1) if body_match else ""
        body_text = re.sub(r"<[^>]+>", "", body).strip()
        return f"\n<details>\n<summary>{title}</summary>\n\n{body_text}\n\n</details>\n\n"

    processed_html = re.sub(
        r'<ac:structured-macro[^>]*ac:name="expand"[^>]*>.*?</ac:structured-macro>',
        replace_expand_macro,
        processed_html,
        flags=re.DOTALL,
    )

    # Handle remaining structured macros (just extract content)
    processed_html = re.sub(
        r"<ac:structured-macro[^>]*>.*?</ac:structured-macro>",
        lambda m: re.sub(r"<[^>]+>", "", m.group(0)),
        processed_html,
        flags=re.DOTALL,
    )

    # Handle Confluence images
    def replace_image(match):
        full_match = match.group(0)
        # Check for attachment
        attachment_match = re.search(r'ri:filename="([^"]+)"', full_match)
        if attachment_match:
            filename = attachment_match.group(1)
            return f"![{filename}]({filename})"
        # Check for URL
        url_match = re.search(r'ri:value="([^"]+)"', full_match)
        if url_match:
            return f"![]({url_match.group(1)})"
        return ""

    processed_html = re.sub(
        r"<ac:image[^>]*>.*?</ac:image>", replace_image, processed_html, flags=re.DOTALL
    )

    # Handle Confluence links
    def replace_link(match):
        full_match = match.group(0)
        # Check for page link
        page_match = re.search(r'ri:content-title="([^"]+)"', full_match)
        if page_match:
            page_title = page_match.group(1)
            # Get link text
            link_text_match = re.search(
                r"<ac:(?:plain-text-)?link-body[^>]*>([^<]+)</ac:", full_match
            )
            display_text = link_text_match.group(1) if link_text_match else page_title
            return f"[{display_text}]({page_title.replace(' ', '-')})"
        # Check for attachment link
        attachment_match = re.search(r'ri:filename="([^"]+)"', full_match)
        if attachment_match:
            filename = attachment_match.group(1)
            link_text_match = re.search(
                r"<ac:(?:plain-text-)?link-body[^>]*>([^<]+)</ac:", full_match
            )
            display_text = link_text_match.group(1) if link_text_match else filename
            return f"[{display_text}]({filename})"
        return ""

    processed_html = re.sub(
        r"<ac:link[^>]*>.*?</ac:link>", replace_link, processed_html, flags=re.DOTALL
    )

    # Handle user mentions
    processed_html = re.sub(r'<ri:user[^>]*ri:account-id="([^"]+)"[^>]*/?>', r"@\1", processed_html)

    # Handle task lists
    def replace_task(match):
        full_match = match.group(0)
        # Check if complete
        is_complete = "complete" in full_match.lower()
        checkbox = "[x]" if is_complete else "[ ]"
        # Extract body
        body_match = re.search(r"<ac:task-body[^>]*>(.*?)</ac:task-body>", full_match, re.DOTALL)
        body = body_match.group(1) if body_match else ""
        body_text = re.sub(r"<[^>]+>", "", body).strip()
        return f"- {checkbox} {body_text}\n"

    processed_html = re.sub(
        r"<ac:task[^>]*>.*?</ac:task>", replace_task, processed_html, flags=re.DOTALL
    )

    # Remove task-list wrapper
    processed_html = re.sub(r"</?ac:task-list[^>]*>", "", processed_html)

    # Clean up any remaining ac: or ri: namespaced elements
    processed_html = re.sub(r"</?(?:ac|ri):[^>]+>", "", processed_html)

    # Convert to markdown using markdownify
    markdown = md(
        processed_html,
        heading_style="atx",
        bullets="-",
        strip=["script", "style"],
    )

    # Post-process cleanup
    # Remove excessive blank lines
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    # Clean up any remaining HTML-like artifacts
    markdown = markdown.strip()

    return markdown


class MarkdownExporter(BaseExporter):
    """Export Confluence pages as Markdown files."""

    format_name = "markdown"
    file_extension = "md"

    def __init__(
        self,
        output_dir: str,
        flat: bool = False,
        include_title: bool = True,
        include_metadata: bool = False,
    ):
        """
        Initialize the Markdown exporter.

        Args:
            output_dir: Base output directory
            flat: If True, use flat structure
            include_title: If True, include page title as H1
            include_metadata: If True, include page metadata as YAML frontmatter
        """
        super().__init__(output_dir, flat)
        self.include_title = include_title
        self.include_metadata = include_metadata

    def convert(self, page: PageData) -> bytes:
        """
        Convert page content to Markdown.

        Args:
            page: The page data to convert

        Returns:
            Markdown content as bytes
        """
        parts = []

        # Add YAML frontmatter if requested
        if self.include_metadata:
            parts.append("---")
            parts.append(f'title: "{page.title}"')
            parts.append(f'page_id: "{page.id}"')
            if page.space_key:
                parts.append(f'space: "{page.space_key}"')
            parts.append("---")
            parts.append("")

        # Add title as H1 if requested
        if self.include_title:
            parts.append(f"# {page.title}")
            parts.append("")

        # Convert body content
        markdown_content = convert_confluence_to_markdown(page.body_storage)
        parts.append(markdown_content)

        content = "\n".join(parts)
        return content.encode("utf-8")
