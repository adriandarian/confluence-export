# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-19

### 🎉 First Stable Release

This is the first production-ready release of Confluence Export CLI, a powerful tool for exporting Confluence pages to multiple formats.

### Added

#### Core Features
- **Multiple Export Formats**: Export Confluence pages to Markdown, HTML, plain text, or PDF
- **Bulk Export**: Export multiple pages in a single command
- **Recursive Export**: Automatically include all child pages with `--include-children`
- **Space Export**: Export entire Confluence spaces with `--space SPACEKEY`
- **URL Support**: Accept full Confluence URLs in addition to page IDs
- **Hierarchical Output**: Preserve page hierarchy in folder structure (or use `--flat`)

#### Performance
- **Parallel Fetching**: Configurable worker threads (`--workers`) for fast bulk exports
- **Progress Display**: Beautiful progress bars and status updates using Rich library
- **Rate Limit Handling**: Automatic exponential backoff for API rate limits
- **Connection Retry**: Automatic retry with backoff for transient network errors

#### Configuration
- **Configuration Files**: Save settings in `.confluence-export.toml` files
- **Environment Variables**: Support for `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`
- **`.env` File Support**: Automatic loading of credentials from `.env` files
- **Pages File Input**: Read page IDs/URLs from a file with `--pages-file`

#### Export Features
- **Export Manifest**: Generate `INDEX.md` and `manifest.json` with `--manifest`
- **Confluence Macro Support**: Proper conversion of info panels, code blocks, expandable sections, and more
- **Table Support**: Full table conversion to Markdown format
- **Task List Support**: Confluence task lists converted to Markdown checkboxes
- **Image References**: Image links preserved in exports

#### Developer Experience
- **Comprehensive CLI**: Full-featured command-line interface with helpful examples
- **Verbose Mode**: Detailed logging with `--verbose`
- **Quiet Mode**: Suppress output with `--quiet`
- **Skip Errors**: Continue on failures with `--skip-errors` (default)
- **Exit Codes**: Proper exit codes for scripting and CI/CD integration

### Export Format Details

#### Markdown Export
- Clean, readable Markdown output
- Confluence storage format to Markdown conversion
- Code block language detection
- Heading hierarchy preservation
- Link and image handling
- Confluence-specific macro conversion

#### HTML Export
- Standalone HTML files with embedded CSS
- Responsive design
- Clean typography
- Syntax highlighting for code blocks

#### Text Export
- Plain text extraction
- Document structure preservation
- Ideal for full-text search and archival

#### PDF Export
- Native Confluence PDF export
- Original formatting preserved
- Includes images and attachments

### Technical Details

- **Python Support**: Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **Platform Support**: Windows, macOS, Linux
- **API**: Confluence Cloud REST API v2
- **Dependencies**: requests, markdownify, beautifulsoup4, python-dotenv, rich, tomli

### Documentation

- Comprehensive README with quick start guide
- Detailed GUIDE.md with examples and troubleshooting
- CONTRIBUTING.md with development guidelines
- CODE_OF_CONDUCT.md
- SECURITY.md

---

## [Unreleased]

### Planned Features
- Confluence Server/Data Center support
- Attachment download support
- Custom Markdown templates
- HTML template customization
- Incremental/delta exports
- Export scheduling

---

[1.0.0]: https://github.com/yourusername/confluence-export/releases/tag/v1.0.0
[Unreleased]: https://github.com/yourusername/confluence-export/compare/v1.0.0...HEAD

