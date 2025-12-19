# Confluence Export CLI

[![PyPI version](https://badge.fury.io/py/confluence-export.svg)](https://badge.fury.io/py/confluence-export)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/adriandarian/confluence-export/actions/workflows/ci.yml/badge.svg)](https://github.com/adriandarian/confluence-export/actions/workflows/ci.yml)

A powerful command-line tool to export Confluence pages to multiple formats (Markdown, HTML, Text, PDF) with support for bulk exports, parallel fetching, and recursive child page fetching.

> 📖 **New to this tool?** Check out the [User Guide](docs/user-guide.md) for detailed instructions, examples, and troubleshooting.

## Features

- **Multiple Export Formats**: Export pages to Markdown, HTML, plain text, or PDF
- **Bulk Export**: Export multiple pages at once with parallel fetching
- **Recursive Export**: Automatically include all child pages with `--include-children`
- **Space Export**: Export entire Confluence spaces with `--space`
- **Flexible Input**: Accept page IDs, full URLs, or read from a file
- **Parallel Processing**: Fast exports with configurable worker threads
- **Progress Display**: Beautiful progress bars and status updates with Rich
- **Export Manifest**: Generate an index of all exported pages
- **Configuration Files**: Save settings in `.confluence-export.toml`
- **Flexible Output**: Choose between flat or hierarchical folder structures

## Installation

### From PyPI (Recommended)

```bash
pip install confluence-export
```

### From Source

```bash
# Clone the repository
git clone https://github.com/adriandarian/confluence-export.git
cd confluence-export

# Install the package
pip install -e .
```

## Quick Start

### 1. Get Your API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Copy the generated token

### 2. Set Up Authentication

```bash
# Option 1: Environment variables (recommended)
export CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
export CONFLUENCE_EMAIL=your.email@example.com
export CONFLUENCE_API_TOKEN=your-api-token

# Option 2: Create a .env file
echo "CONFLUENCE_BASE_URL=https://yoursite.atlassian.net" >> .env
echo "CONFLUENCE_EMAIL=your.email@example.com" >> .env
echo "CONFLUENCE_API_TOKEN=your-api-token" >> .env
```

### 3. Export Pages

```bash
# Export using a full Confluence URL
confluence-export --pages "https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/123456789/My+Page"

# Export multiple pages
confluence-export --pages 123456 789012 --format markdown html

# Export from a file containing URLs/IDs
confluence-export --pages-file pages.txt --format markdown

# Export an entire space
confluence-export --space DOCS --format markdown --output ./backup
```

## Page Selection Options

### Using URLs (Recommended)

Full Confluence URLs are automatically parsed:

```bash
confluence-export --pages "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123456789/My+Page+Title"
```

### Using Page IDs

The numeric ID from the URL:

```bash
confluence-export --pages 123456789
```

### From a File

Create a file with URLs or IDs (one per line):

```text
# pages.txt - Lines starting with # are comments
https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123/Overview

# Page IDs work too
456789

# Comma-separated on one line
111222, 333444
```

```bash
confluence-export --pages-file pages.txt
```

### Combine Methods

```bash
confluence-export --pages 123456 --pages-file more-pages.txt
```

## Export Formats

| Format | Flag | Description |
|--------|------|-------------|
| **Markdown** | `--format markdown` or `md` | Clean Markdown with Confluence macro support |
| **HTML** | `--format html` | Standalone HTML with embedded CSS |
| **Text** | `--format txt` or `text` | Plain text (great for search/archival) |
| **PDF** | `--format pdf` | Native Confluence PDF export |

Export to multiple formats at once:

```bash
confluence-export --pages 123456 --format markdown html pdf
```

## Advanced Features

### Parallel Fetching

Speed up large exports with parallel workers:

```bash
confluence-export --pages-file pages.txt --workers 8
```

### Export Manifest

Generate an index of all exported pages:

```bash
confluence-export --pages 123456 --include-children --manifest
```

Creates `INDEX.md` and `manifest.json` in the output directory.

### Configuration File

Save your settings to avoid repeating them:

```bash
# Save current settings
confluence-export --base-url https://mysite.atlassian.net \
  --email user@example.com \
  --output ./exports \
  --format markdown html \
  --save-config

# Now just run with pages
confluence-export --pages 123456
```

Configuration file (`.confluence-export.toml`):

```toml
[auth]
base_url = "https://mysite.atlassian.net"
email = "user@example.com"

[pages]
file = "pages.txt"  # Default pages file

[export]
output = "./exports"
formats = ["markdown", "html"]
include_children = true
manifest = true

[advanced]
workers = 8
```

### Include Child Pages

Recursively export all descendants:

```bash
confluence-export --pages 123456 --include-children
```

### Output Structure

**Hierarchical (default)**:
```
exports/
├── Parent-Page-123.md
└── Parent-Page/
    ├── Child-Page-456.md
    └── Child-Page/
        └── Grandchild-789.md
```

**Flat** (`--flat`):
```
exports/
├── Parent-Page-123.md
├── Child-Page-456.md
└── Grandchild-789.md
```

## All Options

```
Authentication:
  --base-url URL        Confluence site URL
  --email EMAIL         Atlassian account email
  --token TOKEN         Atlassian API token

Page Selection:
  --pages PAGE [PAGE ...]    Page IDs or URLs (space-separated)
  --pages-file FILE          File with page IDs/URLs (one per line)
  --space SPACE_KEY          Export all pages from a space
  --include-children         Recursively export child pages

Export Options:
  --format FORMAT [...]  Export format(s): markdown, html, txt, pdf
  --output, -o DIR       Output directory (default: ./confluence-exports)
  --flat                 Flat file structure (no folders)
  --manifest             Generate INDEX.md and manifest.json

Advanced Options:
  --workers, -w N        Parallel workers (default: 4)
  --skip-errors          Skip failed pages (default: True)
  --no-skip-errors       Stop on first error
  --verbose, -v          Verbose output
  --quiet, -q            Suppress output except errors

Configuration:
  --config, -c FILE      Config file path (auto-detected)
  --save-config [FILE]   Save settings to config file
  --no-config            Ignore config files
```

## Examples

### Backup an Entire Space

```bash
confluence-export \
  --space DOCS \
  --format markdown html pdf \
  --include-children \
  --manifest \
  --output "./backup-$(date +%Y%m%d)" \
  --workers 8
```

### Export Documentation Section

```bash
confluence-export \
  --pages "https://mysite.atlassian.net/wiki/spaces/DOCS/pages/123/Getting+Started" \
  --include-children \
  --format markdown \
  --manifest \
  --output ./docs
```

### Quick Single Page

```bash
confluence-export --pages 123456 -o ./
```

## Troubleshooting

### Authentication Errors

- Verify your API token at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- Ensure you're using the email associated with your Atlassian account
- Check that your base URL is correct (should be `https://yoursite.atlassian.net`)

### Page Not Found

- Verify the page ID or URL is correct
- Ensure you have permission to view the page
- Check if the page is in a restricted space

### Rate Limiting

The tool automatically handles rate limiting with exponential backoff. Large exports may temporarily slow down.

### PDF Export Fails

PDF export requires additional permissions in Confluence. Ensure your account has export permissions.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Format code
ruff format .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- [User Guide](docs/user-guide.md) - Complete user guide with detailed examples
- [Configuration Guide](docs/configuration.md) - Config file options and examples
- [API Reference](docs/api-reference.md) - Python API documentation
- [Development Guide](docs/development.md) - Contributing and development setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
