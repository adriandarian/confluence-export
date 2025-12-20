# API Reference

This document provides detailed API documentation for using Confluence Export as a Python library.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
  - [ConfluenceClient](#confluenceclient)
  - [PageFetcher](#pagefetcher)
  - [PageData](#pagedata)
- [Exporters](#exporters)
  - [BaseExporter](#baseexporter)
  - [MarkdownExporter](#markdownexporter)
  - [HTMLExporter](#htmlexporter)
  - [TextExporter](#textexporter)
  - [PDFExporter](#pdfexporter)
- [Configuration](#configuration)
- [Utilities](#utilities)
- [Exceptions](#exceptions)
- [Examples](#examples)

---

## Installation

```bash
pip install -e .
```

---

## Quick Start

```python
from confluence_export.client import ConfluenceClient
from confluence_export.fetcher import PageFetcher
from confluence_export.exporters import MarkdownExporter

# Create client
client = ConfluenceClient(
    base_url="https://yoursite.atlassian.net",
    email="your.email@example.com",
    api_token="your-api-token"
)

# Fetch pages
fetcher = PageFetcher(client)
pages = fetcher.fetch_pages(
    page_ids=["123456789"],
    include_children=True,
    include_body=True
)

# Export to Markdown
exporter = MarkdownExporter(output_dir="./exports")
for page in pages:
    output_path = exporter.export(page)
    print(f"Exported: {output_path}")
```

---

## Core Classes

### ConfluenceClient

The main client for interacting with the Confluence Cloud REST API.

```python
from confluence_export.client import ConfluenceClient
```

#### Constructor

```python
ConfluenceClient(
    base_url: str,
    email: str,
    api_token: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `base_url` | str | Confluence site URL (e.g., `https://yoursite.atlassian.net`) |
| `email` | str | Atlassian account email |
| `api_token` | str | Atlassian API token |
| `max_retries` | int | Maximum retry attempts for failed requests |
| `retry_delay` | float | Initial delay between retries (uses exponential backoff) |

#### Methods

##### `get_page(page_id, include_body=True)`

Fetch a single page by ID.

```python
page = client.get_page("123456789")
print(page["title"])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_id` | str | - | The page ID |
| `include_body` | bool | `True` | Whether to include page content |

**Returns:** `Dict[str, Any]` - Page data dictionary

##### `get_page_body(page_id, body_format="storage")`

Get the body content of a page.

```python
content = client.get_page_body("123456789", body_format="storage")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_id` | str | - | The page ID |
| `body_format` | str | `"storage"` | Format: `"storage"`, `"atlas_doc_format"`, or `"view"` |

**Returns:** `str` - Page body content

##### `get_page_children(page_id, limit=250)`

Get immediate child pages.

```python
children = client.get_page_children("123456789")
for child in children:
    print(child["title"])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_id` | str | - | Parent page ID |
| `limit` | int | `250` | Maximum children per request |

**Returns:** `List[Dict[str, Any]]` - List of child page data

##### `get_all_descendants(page_id)`

Recursively get all descendant pages.

```python
descendants = client.get_all_descendants("123456789")
print(f"Found {len(descendants)} descendant pages")
```

**Returns:** `List[Dict[str, Any]]` - All descendant pages with hierarchy info

##### `get_space_pages(space_key, limit=250)`

Get all pages in a space.

```python
pages = client.get_space_pages("DOCS")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `space_key` | str | - | The space key (e.g., "DOCS") |
| `limit` | int | `250` | Maximum pages per request |

**Returns:** `List[Dict[str, Any]]` - All pages in the space

##### `export_page_as_pdf(page_id)`

Export a page as PDF.

```python
pdf_bytes = client.export_page_as_pdf("123456789")
with open("page.pdf", "wb") as f:
    f.write(pdf_bytes)
```

**Returns:** `bytes` - PDF file content

**Raises:** `ConfluenceAPIError` if PDF export fails

##### `test_connection()`

Test the API connection.

```python
if client.test_connection():
    print("Connected successfully!")
```

**Returns:** `bool` - True if connection successful

---

### PageFetcher

High-level page fetching with parallel execution and progress display.

```python
from confluence_export.fetcher import PageFetcher
```

#### Constructor

```python
PageFetcher(
    client: ConfluenceClient,
    verbose: bool = False,
    quiet: bool = False,
    max_workers: int = 4
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | ConfluenceClient | - | The API client |
| `verbose` | bool | `False` | Show detailed progress |
| `quiet` | bool | `False` | Suppress all output |
| `max_workers` | int | `4` | Parallel worker count |

#### Methods

##### `fetch_pages(page_ids, include_children=False, include_body=True, skip_errors=True)`

Main entry point for fetching pages.

```python
fetcher = PageFetcher(client, max_workers=8)

# Fetch single page
pages = fetcher.fetch_pages(["123456789"])

# Fetch with children
pages = fetcher.fetch_pages(
    ["123456789"],
    include_children=True,
    include_body=True
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_ids` | List[str] | - | Page IDs to fetch |
| `include_children` | bool | `False` | Recursively include children |
| `include_body` | bool | `True` | Fetch page content |
| `skip_errors` | bool | `True` | Continue on failures |

**Returns:** `List[PageData]` - Fetched pages

##### `fetch_single_page(page_id, include_body=True)`

Fetch a single page.

```python
page = fetcher.fetch_single_page("123456789")
print(page.title)
```

**Returns:** `PageData`

##### `fetch_multiple_pages(page_ids, include_body=True, skip_errors=True)`

Fetch multiple pages in parallel.

```python
pages = fetcher.fetch_multiple_pages(["111", "222", "333"])
```

**Returns:** `List[PageData]`

##### `fetch_with_children(page_id, include_root=True, include_body=True, skip_errors=True)`

Fetch a page and all descendants.

```python
pages = fetcher.fetch_with_children("123456789")
print(f"Fetched {len(pages)} pages")
```

**Returns:** `List[PageData]` - Root page (if included) followed by descendants

---

### PageData

Dataclass representing a Confluence page.

```python
from confluence_export.fetcher import PageData
```

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | str | Page ID |
| `title` | str | Page title |
| `space_key` | Optional[str] | Space key |
| `body_storage` | str | Page content in storage format |
| `hierarchy_path` | List[str] | Parent page titles |
| `hierarchy_depth` | int | Depth in page tree (0 = root) |
| `parent_id` | Optional[str] | Parent page ID |

#### Class Methods

##### `from_api_response(data, body="")`

Create from API response dictionary.

```python
page_data = PageData.from_api_response(api_response, body=content)
```

---

## Exporters

All exporters inherit from `BaseExporter` and share a common interface.

### BaseExporter

Abstract base class for all exporters.

```python
from confluence_export.exporters.base import BaseExporter
```

#### Constructor

```python
BaseExporter(
    output_dir: str,
    flat: bool = False
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | str | - | Base output directory |
| `flat` | bool | `False` | Flat file structure |

#### Methods

##### `export(page)`

Export a single page.

```python
output_path = exporter.export(page)
```

**Returns:** `str` - Path to exported file

##### `export_all(pages)`

Export multiple pages.

```python
paths = exporter.export_all(pages)
```

**Returns:** `List[str]` - Paths to exported files

##### `convert(page)` (abstract)

Convert page content to export format. Must be implemented by subclasses.

**Returns:** `bytes` - Converted content

##### `get_output_path(page)`

Get the output file path for a page.

```python
path = exporter.get_output_path(page)
```

**Returns:** `str` - Full output path

---

### MarkdownExporter

Export pages to Markdown format.

```python
from confluence_export.exporters import MarkdownExporter

exporter = MarkdownExporter(
    output_dir="./exports",
    flat=False
)

for page in pages:
    path = exporter.export(page)
```

#### Properties

- `format_name`: `"markdown"`
- `file_extension`: `".md"`

---

### HTMLExporter

Export pages to standalone HTML files.

```python
from confluence_export.exporters import HTMLExporter

exporter = HTMLExporter(output_dir="./exports")
```

#### Properties

- `format_name`: `"html"`
- `file_extension`: `".html"`

---

### TextExporter

Export pages to plain text.

```python
from confluence_export.exporters import TextExporter

exporter = TextExporter(output_dir="./exports")
```

#### Properties

- `format_name`: `"text"`
- `file_extension`: `".txt"`

---

### PDFExporter

Export pages to PDF using Confluence's native export.

```python
from confluence_export.exporters import PDFExporter

exporter = PDFExporter(
    output_dir="./exports",
    flat=False,
    client=confluence_client  # Required!
)
```

#### Constructor

```python
PDFExporter(
    output_dir: str,
    flat: bool = False,
    client: ConfluenceClient = None  # Required for PDF
)
```

#### Properties

- `format_name`: `"pdf"`
- `file_extension`: `".pdf"`

---

## Configuration

### Config Class

```python
from confluence_export.config import Config, load_config, save_config
```

#### Config Dataclass

```python
@dataclass
class Config:
    # Authentication
    base_url: Optional[str] = None
    email: Optional[str] = None
    
    # Page selection
    pages: Optional[List[str]] = None
    pages_file: Optional[str] = None
    
    # Export settings
    output: str = "./confluence-exports"
    formats: List[str] = field(default_factory=lambda: ["markdown"])
    flat: bool = False
    include_children: bool = False
    manifest: bool = False
    
    # Advanced settings
    workers: int = 4
    skip_errors: bool = True
    verbose: bool = False
    quiet: bool = False
```

#### Functions

##### `load_config(config_path=None)`

Load configuration from file.

```python
config = load_config()  # Auto-detect
config = load_config("/path/to/config.toml")  # Specific file
```

**Returns:** `Optional[Config]`

##### `save_config(config, config_path=None)`

Save configuration to file.

```python
config = Config(
    base_url="https://site.atlassian.net",
    email="user@example.com",
    formats=["markdown", "html"]
)
saved_path = save_config(config)
```

**Returns:** `str` - Path to saved file

##### `find_config_file(start_dir=None)`

Find configuration file in standard locations.

```python
from confluence_export.config import find_config_file

config_path = find_config_file()
if config_path:
    print(f"Found config: {config_path}")
```

**Returns:** `Optional[Path]`

---

## Utilities

```python
from confluence_export.utils import (
    extract_page_id_from_url,
    sanitize_filename,
    build_file_path,
    ensure_directory
)
```

### `extract_page_id_from_url(url_or_id)`

Extract page ID from a Confluence URL.

```python
page_id = extract_page_id_from_url(
    "https://site.atlassian.net/wiki/spaces/DOC/pages/123456/Title"
)
# Returns: "123456"

page_id = extract_page_id_from_url("123456")
# Returns: "123456"
```

### `sanitize_filename(name)`

Sanitize a string for use as a filename.

```python
safe_name = sanitize_filename("My Page: A Guide?")
# Returns: "My-Page--A-Guide-"
```

### `build_file_path(output_dir, page_title, page_id, extension, hierarchy_path, flat)`

Build the full output path for a page.

```python
path = build_file_path(
    output_dir="./exports",
    page_title="My Page",
    page_id="123456",
    extension=".md",
    hierarchy_path=["Parent"],
    flat=False
)
# Returns: "./exports/Parent/My-Page-123456.md"
```

### `ensure_directory(path)`

Create directory if it doesn't exist.

```python
ensure_directory("./exports/subdir")
```

---

## Exceptions

### ConfluenceAPIError

```python
from confluence_export.client import ConfluenceAPIError
```

Raised when Confluence API requests fail.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | str | Error message |
| `status_code` | Optional[int] | HTTP status code |
| `response` | Optional[dict] | API response body |

#### Example

```python
from confluence_export.client import ConfluenceClient, ConfluenceAPIError

client = ConfluenceClient(...)

try:
    page = client.get_page("invalid-id")
except ConfluenceAPIError as e:
    print(f"Error: {e}")
    print(f"Status: {e.status_code}")
```

---

## Examples

### Basic Export Script

```python
#!/usr/bin/env python3
"""Export Confluence pages to Markdown."""

import os
from confluence_export.client import ConfluenceClient
from confluence_export.fetcher import PageFetcher
from confluence_export.exporters import MarkdownExporter

def main():
    # Get credentials from environment
    client = ConfluenceClient(
        base_url=os.environ["CONFLUENCE_BASE_URL"],
        email=os.environ["CONFLUENCE_EMAIL"],
        api_token=os.environ["CONFLUENCE_API_TOKEN"]
    )
    
    # Fetch pages
    fetcher = PageFetcher(client, verbose=True)
    pages = fetcher.fetch_pages(
        page_ids=["123456789"],
        include_children=True
    )
    
    # Export
    exporter = MarkdownExporter("./docs")
    paths = exporter.export_all(pages)
    
    print(f"Exported {len(paths)} pages")

if __name__ == "__main__":
    main()
```

### Multi-Format Export

```python
from confluence_export.exporters import (
    MarkdownExporter,
    HTMLExporter,
    TextExporter
)

exporters = [
    MarkdownExporter("./exports/md"),
    HTMLExporter("./exports/html"),
    TextExporter("./exports/txt")
]

for page in pages:
    for exporter in exporters:
        exporter.export(page)
```

### Custom Exporter

```python
from confluence_export.exporters.base import BaseExporter
from confluence_export.fetcher import PageData

class JSONExporter(BaseExporter):
    """Export pages as JSON."""
    
    format_name = "json"
    file_extension = ".json"
    
    def convert(self, page: PageData) -> bytes:
        import json
        
        data = {
            "id": page.id,
            "title": page.title,
            "content": page.body_storage,
            "hierarchy": page.hierarchy_path
        }
        
        return json.dumps(data, indent=2).encode("utf-8")

# Usage
exporter = JSONExporter("./exports/json")
for page in pages:
    exporter.export(page)
```

### Error Handling

```python
from confluence_export.client import ConfluenceClient, ConfluenceAPIError

client = ConfluenceClient(...)

def safe_export(page_id: str) -> bool:
    try:
        page = client.get_page(page_id)
        # ... export logic
        return True
    except ConfluenceAPIError as e:
        if e.status_code == 404:
            print(f"Page {page_id} not found")
        elif e.status_code == 401:
            print("Authentication failed")
        else:
            print(f"API error: {e}")
        return False
```

### Using with asyncio (Wrapper)

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from confluence_export.client import ConfluenceClient
from confluence_export.fetcher import PageFetcher

async def export_pages_async(page_ids: list):
    """Async wrapper for page fetching."""
    
    client = ConfluenceClient(...)
    fetcher = PageFetcher(client, max_workers=8)
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        pages = await loop.run_in_executor(
            pool,
            lambda: fetcher.fetch_pages(page_ids, include_children=True)
        )
    
    return pages

# Usage
pages = asyncio.run(export_pages_async(["123", "456"]))
```

---

## Related Documentation

- [User Guide](user-guide.md) - Complete usage guide
- [Configuration Guide](configuration.md) - Config file options
- [Development Guide](development.md) - Contributing and development



