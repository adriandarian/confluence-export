# Confluence Export CLI - User Guide

A comprehensive guide to using the Confluence Export CLI tool for exporting Confluence Cloud pages to various formats.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Authentication Setup](#authentication-setup)
4. [Quick Start](#quick-start)
5. [Command Reference](#command-reference)
6. [Export Formats](#export-formats)
7. [Page Selection](#page-selection)
8. [Output Organization](#output-organization)
9. [Advanced Usage](#advanced-usage)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Introduction

Confluence Export CLI is a command-line tool that allows you to export pages from Confluence Cloud to multiple formats:

- **Markdown** (.md) - Great for documentation sites, GitHub, and version control
- **HTML** (.html) - Standalone web pages with styling
- **Text** (.txt) - Plain text for archival or search indexing
- **PDF** (.pdf) - Print-ready documents using Confluence's native export

### Key Features

- Export single pages or bulk export hundreds of pages
- Recursively export entire page hierarchies with `--include-children`
- Export all pages from a space with `--space`
- Preserve folder structure or flatten to a single directory
- Handle Confluence-specific content (macros, panels, code blocks, etc.)

---

## Installation

### Prerequisites

- **Python 3.8 or higher** - Check with `python --version`
- **pip** - Python package installer
- **Confluence Cloud account** - With API access

### Step 1: Clone or Download

```bash
# Clone the repository
git clone https://github.com/yourusername/confluence-export.git
cd confluence-export
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install the Package

```bash
# Install in development mode (editable)
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Check if it's installed
confluence-export --version

# Or run as a module
python -m confluence_export --version
```

---

## Authentication Setup

Confluence Export uses Atlassian API tokens for authentication. You'll need:

1. Your Atlassian account email
2. An API token
3. Your Confluence site URL

### Creating an API Token

1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Enter a label (e.g., "confluence-export-cli")
4. Click **"Create"**
5. **Copy the token immediately** - you won't be able to see it again!

### Configuring Credentials

You have three options for providing credentials:

#### Option 1: Environment Variables (Recommended for Scripts)

Set these environment variables before running the tool:

**Windows (Command Prompt):**
```cmd
set CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
set CONFLUENCE_EMAIL=your.email@company.com
set CONFLUENCE_API_TOKEN=your-api-token-here
```

**Windows (PowerShell):**
```powershell
$env:CONFLUENCE_BASE_URL = "https://yourcompany.atlassian.net"
$env:CONFLUENCE_EMAIL = "your.email@company.com"
$env:CONFLUENCE_API_TOKEN = "your-api-token-here"
```

**macOS/Linux:**
```bash
export CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
export CONFLUENCE_EMAIL=your.email@company.com
export CONFLUENCE_API_TOKEN=your-api-token-here
```

#### Option 2: .env File (Recommended for Development)

Create a `.env` file in your working directory:

```env
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_EMAIL=your.email@company.com
CONFLUENCE_API_TOKEN=your-api-token-here
```

> ⚠️ **Security Note:** Never commit `.env` files to version control! The included `.gitignore` already excludes them.

#### Option 3: Command-Line Arguments

Pass credentials directly (useful for one-off exports):

```bash
confluence-export \
  --base-url https://yourcompany.atlassian.net \
  --email your.email@company.com \
  --token your-api-token-here \
  --pages 12345
```

> ⚠️ **Security Note:** Command-line arguments may be visible in shell history.

---

## Quick Start

### Export a Single Page

```bash
# Using page ID
confluence-export --pages 123456789 --format markdown

# Using full URL
confluence-export --pages "https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/123456789/My+Page" --format markdown
```

### Export Multiple Pages

```bash
confluence-export --pages 111111 222222 333333 --format markdown
```

### Export a Page with All Children

```bash
confluence-export --pages 123456789 --include-children --format markdown
```

### Export an Entire Space

```bash
confluence-export --space DOCS --format markdown
```

### Export to Multiple Formats

```bash
confluence-export --pages 123456789 --format markdown html pdf
```

---

## Command Reference

### Basic Syntax

```
confluence-export [OPTIONS]
```

### Authentication Options

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--base-url URL` | `CONFLUENCE_BASE_URL` | Your Confluence site URL (e.g., `https://yoursite.atlassian.net`) |
| `--email EMAIL` | `CONFLUENCE_EMAIL` | Your Atlassian account email |
| `--token TOKEN` | `CONFLUENCE_API_TOKEN` | Your Atlassian API token |

### Page Selection Options

| Option | Description |
|--------|-------------|
| `--pages PAGE [PAGE ...]` | One or more page IDs or URLs to export |
| `--space SPACE_KEY` | Export all pages from a space |
| `--include-children` | Recursively include all child pages |

> **Note:** You must specify either `--pages` or `--space` (or both).

### Export Options

| Option | Default | Description |
|--------|---------|-------------|
| `--format FORMAT [...]` | `markdown` | Export format(s): `markdown`, `md`, `html`, `txt`, `text`, `pdf` |
| `--output DIR`, `-o DIR` | `./confluence-exports` | Output directory path |
| `--flat` | Off | Put all files in one directory (no hierarchy) |

### Advanced Options

| Option | Default | Description |
|--------|---------|-------------|
| `--skip-errors` | On | Continue exporting if a page fails |
| `--no-skip-errors` | - | Stop on first error |
| `--verbose`, `-v` | Off | Show detailed progress |
| `--quiet`, `-q` | Off | Suppress all output except errors |
| `--version` | - | Show version number |
| `--help`, `-h` | - | Show help message |

---

## Export Formats

### Markdown (`--format markdown` or `--format md`)

Converts Confluence's storage format to clean, readable Markdown.

**Handles:**
- Headings (H1-H6)
- Paragraphs and line breaks
- Bold, italic, strikethrough
- Ordered and unordered lists
- Tables
- Code blocks with syntax highlighting
- Links (internal and external)
- Images (as references)
- Blockquotes
- Task lists (checkboxes)

**Confluence-Specific Handling:**
- Info, Note, Warning, Tip panels → Blockquotes with labels
- Expand/Collapse sections → HTML `<details>` elements
- Code macros → Fenced code blocks with language
- TOC macro → `[TOC]` placeholder
- User mentions → `@account-id`

**Example Output:**
```markdown
# Page Title

This is a paragraph with **bold** and *italic* text.

> **NOTE:** This was an info panel in Confluence.

```python
def hello():
    print("Hello, World!")
```

| Column 1 | Column 2 |
|----------|----------|
| Cell A   | Cell B   |
```

### HTML (`--format html`)

Exports as standalone HTML files with embedded CSS styling.

**Features:**
- Complete HTML5 document structure
- Responsive, readable typography
- Styled tables with alternating row colors
- Syntax-highlighted code blocks
- Mobile-friendly layout

**Best For:**
- Offline viewing in a browser
- Sharing with non-technical users
- Archiving with original styling

### Text (`--format txt` or `--format text`)

Plain text export with all HTML stripped.

**Features:**
- Title underlined with `=` characters
- Bullet points preserved as `•`
- Table cells separated by tabs
- Clean paragraph breaks

**Best For:**
- Full-text search indexing
- Accessibility
- Minimal storage requirements

### PDF (`--format pdf`)

Uses Confluence's native PDF export functionality.

**Features:**
- Exact Confluence rendering
- Includes images and attachments
- Proper page breaks
- Headers and footers

**Requirements:**
- Your account must have PDF export permissions
- Some Confluence instances may require add-ons

**Note:** PDF export may not be available on all Confluence instances.

---

## Page Selection

### Finding Page IDs

**Method 1: From the URL**

When viewing a page, the URL contains the page ID:
```
https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/123456789/Page+Title
                                                      ^^^^^^^^^
                                                      This is the page ID
```

**Method 2: From Page Information**

1. Open the page in Confluence
2. Click the `...` menu (top right)
3. Select "Page Information"
4. Look for "Page ID" in the details

### Using Page URLs

You can pass full Confluence URLs instead of IDs:

```bash
confluence-export --pages "https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/123456789/My+Page"
```

The tool automatically extracts the page ID from URLs in these formats:
- `/wiki/spaces/SPACE/pages/ID/Title`
- `/wiki/pages/viewpage.action?pageId=ID`

### Finding Space Keys

The space key appears in page URLs after `/spaces/`:
```
https://yoursite.atlassian.net/wiki/spaces/DOCS/pages/...
                                            ^^^^
                                            Space key is "DOCS"
```

You can also find it in:
- Space settings
- The space sidebar header

---

## Output Organization

### Hierarchical Mode (Default)

When exporting with `--include-children`, the tool preserves the page hierarchy:

```
confluence-exports/
├── Parent-Page-123456.md
└── Parent-Page/
    ├── Child-Page-1-234567.md
    ├── Child-Page-2-345678.md
    └── Child-Page-2/
        └── Grandchild-Page-456789.md
```

This mirrors your Confluence page tree structure.

### Flat Mode (`--flat`)

All files are placed in a single directory:

```
confluence-exports/
├── Parent-Page-123456.md
├── Child-Page-1-234567.md
├── Child-Page-2-345678.md
└── Grandchild-Page-456789.md
```

**When to use flat mode:**
- Simpler file management
- Avoiding deep directory nesting
- When hierarchy isn't important

### File Naming

Files are named using the pattern:
```
{sanitized-title}-{page-id}.{extension}
```

For example:
- `Getting-Started-Guide-123456.md`
- `API-Reference-234567.html`

The page ID ensures uniqueness even if titles are similar.

---

## Advanced Usage

### Automated Backups

Create a scheduled backup script:

**Windows (backup.bat):**
```batch
@echo off
set CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
set CONFLUENCE_EMAIL=your.email@company.com
set CONFLUENCE_API_TOKEN=your-token

set BACKUP_DIR=C:\Backups\Confluence\%date:~-4,4%-%date:~-7,2%-%date:~-10,2%

confluence-export --space DOCS --format markdown html --output "%BACKUP_DIR%" --include-children --quiet
```

**macOS/Linux (backup.sh):**
```bash
#!/bin/bash
export CONFLUENCE_BASE_URL=https://yoursite.atlassian.net
export CONFLUENCE_EMAIL=your.email@company.com
export CONFLUENCE_API_TOKEN=your-token

BACKUP_DIR="/backups/confluence/$(date +%Y-%m-%d)"

confluence-export --space DOCS --format markdown html --output "$BACKUP_DIR" --include-children --quiet
```

### Migrating to Static Site Generators

Export to Markdown for use with Jekyll, Hugo, MkDocs, etc.:

```bash
# Export documentation space
confluence-export --space DOCS --format markdown --output ./docs/content --include-children

# Files are ready for your static site generator!
```

### Exporting for Version Control

```bash
# Export to a git repository
cd my-docs-repo
confluence-export --pages 123456 --include-children --format markdown --output ./docs

# Commit the changes
git add docs/
git commit -m "Update documentation from Confluence"
git push
```

### Combining Multiple Spaces

```bash
# Export multiple spaces to the same output
confluence-export --space DOCS --format markdown --output ./all-docs
confluence-export --space ENGINEERING --format markdown --output ./all-docs
confluence-export --space PRODUCT --format markdown --output ./all-docs
```

### Verbose Mode for Debugging

```bash
confluence-export --pages 123456 --include-children --format markdown --verbose
```

This shows:
- Each page being fetched
- Progress counters
- Individual export status
- Detailed error messages

---

## Troubleshooting

### Authentication Errors

**Error:** `401 Unauthorized`

**Solutions:**
1. Verify your API token is correct and hasn't expired
2. Make sure you're using the email associated with your Atlassian account
3. Check that your base URL is correct (should be `https://yoursite.atlassian.net`)
4. Ensure your account has access to the pages you're trying to export

**Error:** `Missing required authentication parameters`

**Solutions:**
1. Provide `--base-url`, `--email`, and `--token` arguments
2. Or set `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` environment variables
3. Or create a `.env` file with these values

### Page Not Found Errors

**Error:** `404 Not Found` or `Page not found`

**Solutions:**
1. Verify the page ID is correct
2. Check if the page still exists in Confluence
3. Ensure you have permission to view the page
4. Try using the full page URL instead of just the ID

### Rate Limiting

**Symptom:** Exports are slow or you see `429 Too Many Requests`

**What's happening:** Confluence is limiting your API requests.

**Solution:** The tool automatically handles rate limiting with exponential backoff. Just wait for it to complete.

**Prevention:** For large exports, run during off-peak hours.

### PDF Export Fails

**Error:** `PDF export is not available`

**Possible causes:**
1. Your account doesn't have PDF export permissions
2. Your Confluence instance doesn't support PDF export
3. The page has content that can't be exported to PDF

**Solutions:**
1. Contact your Confluence administrator for permissions
2. Try exporting to HTML instead
3. Export the page manually from Confluence's UI to verify it works

### Empty or Malformed Output

**Symptom:** Markdown files have missing content or strange formatting

**Possible causes:**
1. The page uses unsupported Confluence macros
2. The page has complex nested structures

**Solutions:**
1. Try exporting to HTML first to see the raw content
2. Check if the page renders correctly in Confluence itself
3. Report the issue with the page ID for investigation

### Connection Errors

**Error:** `Connection refused` or `Connection timed out`

**Solutions:**
1. Check your internet connection
2. Verify the Confluence site is accessible in your browser
3. Check if you're behind a proxy (may need additional configuration)
4. Ensure your firewall isn't blocking the connection

---

## FAQ

### Q: Can I export pages from Confluence Server/Data Center?

Currently, this tool is designed for Confluence Cloud. Confluence Server/Data Center has a different API structure. Support may be added in future versions.

### Q: Does this export attachments and images?

The current version exports image references but doesn't download the actual image files. Images will appear as Markdown image links or HTML `<img>` tags pointing to the original Confluence URLs.

### Q: Can I schedule automatic exports?

Yes! Create a script using the examples in [Advanced Usage](#advanced-usage) and schedule it with:
- Windows: Task Scheduler
- macOS: cron or launchd
- Linux: cron

### Q: How do I export a page that requires special permissions?

You need to use an API token from an account that has access to those pages. The tool uses the same permissions as your Confluence account.

### Q: Is my API token stored anywhere?

No. The tool only uses credentials during execution. They're never saved to disk (unless you put them in a `.env` file, which you control).

### Q: Can I export comments?

Currently, only page content is exported. Comments are not included.

### Q: What happens if a page is updated while I'm exporting?

Each page is fetched individually, so you'll get the content as it existed at the moment of that page's fetch. For consistency across a large export, consider running during low-activity periods.

### Q: How do I handle pages with special characters in titles?

The tool automatically sanitizes filenames, replacing special characters with underscores. The page ID in the filename ensures uniqueness.

### Q: Can I resume a failed export?

Currently, there's no built-in resume feature. However, you can:
1. Use `--skip-errors` (default) to continue past failures
2. Re-run the export - existing files will be overwritten with fresh content

---

## Getting Help

### Check the Version

```bash
confluence-export --version
```

### View Help

```bash
confluence-export --help
```

### Report Issues

If you encounter bugs or have feature requests, please open an issue on the GitHub repository with:

1. Your Python version (`python --version`)
2. The exact command you ran (redact sensitive info)
3. The full error message
4. The Confluence page ID (if applicable)

---

*Happy exporting! 📚*


