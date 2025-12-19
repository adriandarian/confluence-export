# 🎉 Confluence Export CLI v1.0.0

**The first stable release of Confluence Export CLI** - a powerful command-line tool to export Confluence pages to multiple formats.

## 📦 Installation

```bash
# From PyPI (when published)
pip install confluence-export

# From wheel file (attached below)
pip install confluence_export-1.0.0-py3-none-any.whl

# From source
pip install git+https://github.com/adriandarian/confluence-export.git@v1.0.0
```

## ✨ Features

### Export Formats
- **Markdown** - Clean, readable Markdown with full Confluence macro support
- **HTML** - Standalone HTML files with embedded CSS styling
- **Text** - Plain text extraction for search and archival
- **PDF** - Native Confluence PDF export

### Page Selection
- 🔗 **Full URL support** - Paste Confluence URLs directly
- 🔢 **Page IDs** - Use numeric page IDs
- 📁 **File input** - Read page lists from a file with `--pages-file`
- 🗂️ **Space export** - Export entire spaces with `--space`
- 👨‍👩‍👧‍👦 **Child pages** - Recursively include children with `--include-children`

### Performance & UX
- ⚡ **Parallel fetching** - Configurable worker threads for fast exports
- 📊 **Progress display** - Beautiful progress bars with Rich
- 🔄 **Auto-retry** - Handles rate limits and network errors gracefully
- 📋 **Export manifest** - Generate INDEX.md and manifest.json

### Configuration
- 📝 **Config files** - Save settings in `.confluence-export.toml`
- 🔐 **Environment variables** - Secure credential management
- 📄 **`.env` support** - Auto-load from .env files

## 🚀 Quick Start

```bash
# Set up credentials
export CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
export CONFLUENCE_EMAIL=your.email@example.com
export CONFLUENCE_API_TOKEN=your-api-token

# Export a page using its URL
confluence-export --pages "https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/123456/My+Page"

# Export multiple pages to multiple formats
confluence-export --pages 123456 789012 --format markdown html --output ./exports

# Export from a file
confluence-export --pages-file pages.txt --format markdown

# Export an entire space with all child pages
confluence-export --space DOCS --include-children --manifest --output ./backup
```

## 📋 Requirements

- Python 3.8, 3.9, 3.10, 3.11, 3.12, or 3.13
- Confluence Cloud account with API token

## 📚 Documentation

- [README](https://github.com/adriandarian/confluence-export#readme) - Quick start guide
- [User Guide](https://github.com/adriandarian/confluence-export/blob/main/docs/user-guide.md) - Detailed documentation
- [Configuration](https://github.com/adriandarian/confluence-export/blob/main/docs/configuration.md) - Config file reference

## 📥 Downloads

| File | Description |
|------|-------------|
| `confluence_export-1.0.0-py3-none-any.whl` | Python wheel (recommended) |
| `confluence_export-1.0.0.tar.gz` | Source distribution |

## 🙏 Acknowledgments

Thanks to all contributors and testers who helped make this release possible!

---

**Full Changelog**: https://github.com/adriandarian/confluence-export/blob/main/CHANGELOG.md

