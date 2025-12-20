# Development Guide

This guide covers setting up a development environment, running tests, and contributing to Confluence Export CLI.

## Table of Contents

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Architecture Overview](#architecture-overview)
- [Adding New Export Formats](#adding-new-export-formats)
- [Contributing](#contributing)
- [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/confluence-export.git
cd confluence-export

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

---

## Project Structure

```
confluence-export/
├── confluence_export/           # Main package
│   ├── __init__.py             # Package init, version
│   ├── __main__.py             # Module entry point
│   ├── cli.py                  # CLI implementation
│   ├── client.py               # Confluence API client
│   ├── config.py               # Configuration handling
│   ├── fetcher.py              # Page fetching logic
│   ├── manifest.py             # Export manifest generation
│   ├── utils.py                # Utility functions
│   └── exporters/              # Export format handlers
│       ├── __init__.py
│       ├── base.py             # Base exporter class
│       ├── markdown.py         # Markdown exporter
│       ├── html.py             # HTML exporter
│       ├── text.py             # Text exporter
│       └── pdf.py              # PDF exporter
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_cli.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_exporters.py
│   ├── test_fetcher.py
│   ├── test_manifest.py
│   └── test_utils.py
├── docs/                        # Documentation
│   ├── user-guide.md
│   ├── configuration.md
│   ├── api-reference.md
│   └── development.md
├── pyproject.toml               # Project configuration
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development dependencies
├── setup.py                     # Legacy setup file
├── README.md                    # Project overview
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT License
└── CODE_OF_CONDUCT.md           # Code of conduct
```

---

## Development Setup

### Installing Dependencies

```bash
# Install package with development dependencies
pip install -e ".[dev]"

# Or install from requirements files
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Development Dependencies

| Package | Purpose |
|---------|---------|
| `ruff` | Linting and formatting |
| `pytest` | Testing framework |
| `pytest-cov` | Code coverage |
| `pytest-mock` | Mocking utilities |
| `responses` | HTTP response mocking |

### Environment Variables for Testing

Create a `.env.test` file (not committed):

```env
CONFLUENCE_BASE_URL=https://test.atlassian.net
CONFLUENCE_EMAIL=test@example.com
CONFLUENCE_API_TOKEN=test-token
```

---

## Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Style Guidelines

- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Sorted with `confluence_export` as first-party

### Linting Rules

We enforce these rule sets:
- **E/W**: pycodestyle errors and warnings
- **F**: Pyflakes
- **I**: isort (import sorting)
- **B**: flake8-bugbear
- **C4**: flake8-comprehensions
- **UP**: pyupgrade
- **SIM**: flake8-simplify
- **TCH**: flake8-type-checking
- **PTH**: flake8-use-pathlib
- **RUF**: Ruff-specific rules

### Running Linters

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check formatting without changes
ruff format --check .
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
ruff check --fix .
ruff format .
```

---

## Testing

We use [pytest](https://pytest.org/) for testing.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cli.py

# Run specific test function
pytest tests/test_cli.py::test_create_parser

# Run specific test class
pytest tests/test_client.py::TestConfluenceClient

# Run tests matching a pattern
pytest -k "test_export"
```

### Test Coverage

```bash
# Run with coverage report
pytest --cov=confluence_export

# Generate HTML coverage report
pytest --cov=confluence_export --cov-report=html
# Open htmlcov/index.html in browser

# Show missing lines
pytest --cov=confluence_export --cov-report=term-missing
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

Mark tests appropriately:

```python
import pytest

@pytest.mark.unit
def test_sanitize_filename():
    """Fast test with no external dependencies."""
    pass

@pytest.mark.integration
def test_api_connection():
    """Test that may require mocking external services."""
    pass
```

### Writing Tests

#### Test Structure

```python
import pytest
from confluence_export.client import ConfluenceClient

class TestConfluenceClient:
    """Tests for the ConfluenceClient class."""
    
    def test_initialization(self):
        """Test client initializes with correct parameters."""
        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="token123"
        )
        assert client.base_url == "https://example.atlassian.net"
    
    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        client = ConfluenceClient(
            base_url="https://example.atlassian.net/",
            email="test@example.com",
            api_token="token123"
        )
        assert client.base_url == "https://example.atlassian.net"
```

#### Using Fixtures

```python
# In conftest.py
import pytest

@pytest.fixture
def mock_client():
    """Create a mock Confluence client."""
    return ConfluenceClient(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test-token"
    )

@pytest.fixture
def sample_page_data():
    """Create sample page data for testing."""
    return {
        "id": "123456",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Content</p>"}}
    }

# In test files
def test_with_fixtures(mock_client, sample_page_data):
    # Use fixtures
    pass
```

#### Mocking HTTP Requests

```python
import responses

@responses.activate
def test_get_page(mock_client):
    """Test fetching a page."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        json={"id": "123456", "title": "Test"},
        status=200
    )
    
    page = mock_client.get_page("123456")
    assert page["title"] == "Test"
```

---

## Architecture Overview

### Component Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     CLI      │────▶│   Fetcher    │────▶│    Client    │
│   (cli.py)   │     │ (fetcher.py) │     │ (client.py)  │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │                    │                     │
       ▼                    ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Config     │     │   PageData   │     │  Confluence  │
│ (config.py)  │     │  (dataclass) │     │     API      │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Manifest   │     │   Exporters  │
│(manifest.py) │     │  (exporters/)│
└──────────────┘     └──────────────┘
```

### Data Flow

1. **CLI** parses arguments and loads configuration
2. **Client** authenticates and provides API access
3. **Fetcher** retrieves pages (with parallel fetching)
4. **PageData** objects hold page content and metadata
5. **Exporters** convert and write to files
6. **Manifest** (optional) generates index files

### Key Design Decisions

- **Parallel Fetching**: `ThreadPoolExecutor` for concurrent API calls
- **Pluggable Exporters**: Abstract base class for easy extension
- **Progress Display**: Rich library for terminal UI
- **Configuration Layers**: CLI > Environment > Config file > Defaults

---

## Adding New Export Formats

### Step 1: Create the Exporter

Create a new file in `confluence_export/exporters/`:

```python
# confluence_export/exporters/docx.py
"""DOCX exporter for Confluence content."""

from docx import Document  # python-docx
from .base import BaseExporter
from ..fetcher import PageData


class DOCXExporter(BaseExporter):
    """Export Confluence pages to DOCX format."""
    
    format_name = "docx"
    file_extension = ".docx"
    
    def convert(self, page: PageData) -> bytes:
        """Convert page content to DOCX."""
        from io import BytesIO
        
        doc = Document()
        doc.add_heading(page.title, 0)
        
        # Convert HTML to DOCX paragraphs
        # ... conversion logic ...
        
        # Save to bytes
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
```

### Step 2: Register the Exporter

Update `confluence_export/exporters/__init__.py`:

```python
from .base import BaseExporter
from .docx import DOCXExporter  # Add import
from .html import HTMLExporter
from .markdown import MarkdownExporter
from .pdf import PDFExporter
from .text import TextExporter

__all__ = [
    "BaseExporter",
    "DOCXExporter",  # Add to exports
    "HTMLExporter",
    "MarkdownExporter",
    "PDFExporter",
    "TextExporter",
]
```

### Step 3: Add CLI Support

Update `cli.py` to include the new format:

```python
# In create_parser()
export_group.add_argument(
    "--format",
    nargs="+",
    choices=["markdown", "md", "html", "txt", "text", "pdf", "docx"],  # Add docx
    ...
)

# In create_exporters()
def create_exporters(...):
    ...
    elif fmt == "docx":
        exporters[fmt] = DOCXExporter(output_dir, flat=flat)
```

### Step 4: Add Tests

Create `tests/test_exporters_docx.py`:

```python
import pytest
from confluence_export.exporters import DOCXExporter
from confluence_export.fetcher import PageData


class TestDOCXExporter:
    """Tests for DOCX exporter."""
    
    @pytest.fixture
    def exporter(self, tmp_path):
        return DOCXExporter(str(tmp_path))
    
    @pytest.fixture
    def sample_page(self):
        return PageData(
            id="123",
            title="Test Page",
            body_storage="<p>Hello World</p>"
        )
    
    def test_convert_returns_bytes(self, exporter, sample_page):
        result = exporter.convert(sample_page)
        assert isinstance(result, bytes)
    
    def test_export_creates_file(self, exporter, sample_page, tmp_path):
        path = exporter.export(sample_page)
        assert path.endswith(".docx")
        assert (tmp_path / path.split("/")[-1]).exists()
```

### Step 5: Update Documentation

Add the new format to:
- `README.md`
- `docs/user-guide.md`
- `docs/api-reference.md`

---

## Contributing

### Branch Naming

Use descriptive prefixes:
- `feature/add-docx-export`
- `fix/handle-empty-pages`
- `docs/update-readme`
- `refactor/simplify-fetcher`

### Commit Messages

Follow conventional commits:
```
feat: add DOCX export format
fix: handle pages with no content
docs: update API reference
refactor: simplify page fetcher logic
test: add tests for config loading
```

### Pull Request Checklist

- [ ] Code follows style guidelines (`ruff check .` passes)
- [ ] All tests pass (`pytest`)
- [ ] New code has test coverage
- [ ] Documentation updated
- [ ] Commit messages are clear

### Code Review Guidelines

When reviewing:
1. Check for correctness
2. Verify test coverage
3. Review documentation
4. Consider edge cases
5. Check performance implications

---

## Release Process

### Version Bumping

Update version in `confluence_export/__init__.py`:

```python
__version__ = "1.1.0"
```

### Creating a Release

```bash
# Ensure all tests pass
pytest

# Ensure code is formatted
ruff check .
ruff format .

# Create release commit
git add .
git commit -m "Release v1.1.0"
git tag v1.1.0

# Push
git push origin main --tags
```

### Building Distribution

```bash
# Install build tools
pip install build twine

# Build
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI (when ready)
twine upload dist/*
```

---

## Related Documentation

- [User Guide](user-guide.md) - Complete usage guide
- [Configuration Guide](configuration.md) - Config file options
- [API Reference](api-reference.md) - Python API documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines



