# Confluence Export CLI

A powerful command-line tool to export Confluence pages to multiple formats (Markdown, HTML, Text, PDF) with support for bulk exports and recursive child page fetching.

> 📖 **New to this tool?** Check out the [Complete User Guide](GUIDE.md) for detailed instructions, examples, and troubleshooting.

## Features

- **Multiple Export Formats**: Export pages to Markdown, HTML, plain text, or PDF
- **Bulk Export**: Export multiple pages at once
- **Recursive Export**: Automatically include all child pages with `--include-children`
- **Flexible Output**: Choose between flat or hierarchical folder structures
- **Confluence Cloud Support**: Works with Confluence Cloud (*.atlassian.net)
- **URL or ID Input**: Accept page IDs or full Confluence URLs

## Installation

### Prerequisites

- Python 3.8 or higher
- A Confluence Cloud account with API token access

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/confluence-export.git
cd confluence-export

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Install Dependencies Only

```bash
pip install -r requirements.txt
```

## Authentication

### Getting Your API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "confluence-export")
4. Copy the generated token

### Providing Credentials

You can provide credentials in three ways:

#### 1. Command-line Arguments

```bash
confluence-export \
  --base-url https://yoursite.atlassian.net \
  --email your.email@example.com \
  --token your-api-token \
  --pages 12345
```

#### 2. Environment Variables

```bash
export CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
export CONFLUENCE_EMAIL=your.email@example.com
export CONFLUENCE_API_TOKEN=your-api-token

confluence-export --pages 12345
```

#### 3. `.env` File

Create a `.env` file in your working directory:

```env
CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
CONFLUENCE_EMAIL=your.email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

## Usage

### Basic Usage

```bash
# Export a single page as Markdown
confluence-export --pages 12345 --format markdown

# Export using a Confluence URL
confluence-export --pages "https://yoursite.atlassian.net/wiki/spaces/SPACE/pages/12345/Page+Title" --format markdown
```

### Multiple Pages

```bash
# Export multiple pages
confluence-export --pages 12345 67890 11111 --format markdown

# Export to multiple formats
confluence-export --pages 12345 --format markdown html pdf
```

### Including Child Pages

```bash
# Export a page and all its children
confluence-export --pages 12345 --include-children --format markdown

# Export multiple parent pages with all their children
confluence-export --pages 12345 67890 --include-children --format markdown
```

### Exporting an Entire Space

```bash
# Export all pages from a space
confluence-export --space MYSPACE --format markdown

# Export a space to multiple formats
confluence-export --space DOCS --format markdown html pdf --output ./space-backup
```

### Output Options

```bash
# Specify output directory
confluence-export --pages 12345 --format markdown --output ./my-exports

# Use flat structure (all files in one directory)
confluence-export --pages 12345 --include-children --format markdown --flat

# Preserve hierarchy (default - creates nested folders)
confluence-export --pages 12345 --include-children --format markdown
```

### All Options

```
usage: confluence-export [-h] [--version] [--base-url URL] [--email EMAIL]
                         [--token TOKEN] --pages PAGE [PAGE ...]
                         [--include-children]
                         [--format FORMAT [FORMAT ...]] [--output DIR]
                         [--flat] [--skip-errors] [--no-skip-errors]
                         [--verbose] [--quiet]

Authentication:
  --base-url URL        Confluence site URL (e.g., https://yoursite.atlassian.net)
  --email EMAIL         Atlassian account email
  --token TOKEN         Atlassian API token

Page Selection:
  --pages PAGE [PAGE ...] Page IDs or URLs to export. Can specify multiple.
  --space SPACE_KEY     Export all pages from a space (e.g., 'MYSPACE')
  --include-children    Recursively export all child pages

Export Options:
  --format FORMAT       Export format(s): markdown/md, html, txt/text, pdf
  --output DIR, -o DIR  Output directory (default: ./confluence-exports)
  --flat                Use flat file structure

Advanced Options:
  --skip-errors         Skip failed pages and continue (default: True)
  --no-skip-errors      Stop on first error
  --verbose, -v         Enable verbose output
  --quiet, -q           Suppress all output except errors
```

## Export Formats

### Markdown (`--format markdown` or `--format md`)

Converts Confluence storage format to clean Markdown. Handles:
- Headings, paragraphs, lists
- Code blocks with language hints
- Tables
- Links and images
- Confluence macros (info panels, expandable sections, etc.)
- Task lists

### HTML (`--format html`)

Exports as standalone HTML files with:
- Embedded CSS styling
- Responsive design
- Clean, readable typography

### Text (`--format txt` or `--format text`)

Plain text export that:
- Strips all HTML formatting
- Preserves document structure
- Great for full-text search or archival

### PDF (`--format pdf`)

Uses Confluence's native PDF export:
- Preserves original formatting
- Includes images and attachments
- Maintains Confluence styling

## Output Structure

### Hierarchical (Default)

When exporting with `--include-children`, files are organized in folders matching the page hierarchy:

```
confluence-exports/
├── Parent-Page-12345.md
├── Parent-Page/
│   ├── Child-Page-1-23456.md
│   ├── Child-Page-2-34567.md
│   └── Child-Page-2/
│       └── Grandchild-Page-45678.md
```

### Flat (`--flat`)

All files are placed in a single directory with unique names:

```
confluence-exports/
├── Parent-Page-12345.md
├── Child-Page-1-23456.md
├── Child-Page-2-34567.md
└── Grandchild-Page-45678.md
```

## Examples

### Export an Entire Space Section

```bash
# Export a top-level page and all its descendants
confluence-export \
  --pages 12345 \
  --include-children \
  --format markdown html \
  --output ./documentation \
  --verbose
```

### Create a Backup

```bash
# Export everything to all formats
confluence-export \
  --pages 12345 67890 \
  --include-children \
  --format markdown html txt pdf \
  --output ./backup-$(date +%Y%m%d)
```

### Quick Single Page Export

```bash
# Export just one page to markdown
confluence-export --pages 12345 -o ./
```

## Troubleshooting

### Authentication Errors

- Verify your API token is valid and hasn't expired
- Ensure you're using the email associated with your Atlassian account
- Check that your base URL is correct (should be `https://yoursite.atlassian.net`)

### Page Not Found

- Verify the page ID is correct
- Ensure you have permission to view the page
- Try using the full page URL instead of just the ID

### Rate Limiting

The tool automatically handles rate limiting with exponential backoff. If you're exporting many pages, the process may slow down temporarily.

### PDF Export Fails

PDF export requires additional permissions in Confluence. Ensure your account has export permissions for the target pages.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
confluence-export/
├── confluence_export/
│   ├── __init__.py          # Package init
│   ├── cli.py               # CLI entry point
│   ├── client.py            # Confluence API client
│   ├── fetcher.py           # Page fetching logic
│   ├── utils.py             # Utility functions
│   └── exporters/
│       ├── __init__.py
│       ├── base.py          # Base exporter class
│       ├── markdown.py      # Markdown exporter
│       ├── html.py          # HTML exporter
│       ├── text.py          # Text exporter
│       └── pdf.py           # PDF exporter
├── requirements.txt
├── setup.py
└── README.md
```

## License

MIT License - see LICENSE file for details.

## Documentation

- [README.md](README.md) - Quick start and overview
- [GUIDE.md](GUIDE.md) - Complete user guide with detailed examples

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
