"""Markdown exporter for Confluence content."""

import re
from markdownify import markdownify as md, MarkdownConverter

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
    
    # Use custom converter with Confluence-specific handling
    converter = ConfluenceMarkdownConverter(
        heading_style="atx",
        bullets="-",
        code_language_callback=None,
    )
    
    # Pre-process: handle some Confluence-specific XML namespaces
    # The markdownify library doesn't handle XML namespaces well
    processed_html = html_content
    
    # Convert ac:structured-macro to custom elements
    processed_html = re.sub(
        r'<ac:structured-macro([^>]*)>',
        r'<ac-structured-macro\1>',
        processed_html
    )
    processed_html = processed_html.replace('</ac:structured-macro>', '</ac-structured-macro>')
    
    # Convert ac:image to custom elements
    processed_html = re.sub(
        r'<ac:image([^>]*)>',
        r'<ac-image\1>',
        processed_html
    )
    processed_html = processed_html.replace('</ac:image>', '</ac-image>')
    
    # Convert ac:link to custom elements
    processed_html = re.sub(
        r'<ac:link([^>]*)>',
        r'<ac-link\1>',
        processed_html
    )
    processed_html = processed_html.replace('</ac:link>', '</ac-link>')
    
    # Convert to markdown using the standard converter
    # For basic conversion (the custom converter handles edge cases)
    markdown = md(
        processed_html,
        heading_style="atx",
        bullets="-",
        strip=["script", "style"],
    )
    
    # Post-process cleanup
    # Remove excessive blank lines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    
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
        include_metadata: bool = False
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
            parts.append(f"title: \"{page.title}\"")
            parts.append(f"page_id: \"{page.id}\"")
            if page.space_key:
                parts.append(f"space: \"{page.space_key}\"")
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

