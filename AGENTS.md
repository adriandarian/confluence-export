# AI Agent Instructions

This document provides context and guidelines for AI coding assistants working with the Confluence Export CLI codebase.

## Project Overview

**Confluence Export CLI** is a Python command-line tool that exports Confluence pages to multiple formats (Markdown, HTML, Text, PDF). It uses the Confluence Cloud REST API and supports features like parallel fetching, recursive child page export, and configuration files.

- **Language**: Python 3.8+
- **Package Manager**: pip with pyproject.toml
- **Test Framework**: pytest
- **CLI Framework**: argparse
- **Key Dependencies**: requests, python-dotenv, rich, tomli

## Repository Structure

```
confluence-export/
├── confluence_export/          # Main package
│   ├── __init__.py            # Version info
│   ├── __main__.py            # Entry point for `python -m`
│   ├── cli.py                 # CLI argument parsing & main orchestration
│   ├── client.py              # Confluence API client (ConfluenceClient)
│   ├── config.py              # TOML configuration file handling
│   ├── fetcher.py             # Page fetching logic (PageFetcher)
│   ├── manifest.py            # Export manifest/index generation
│   ├── utils.py               # Utility functions (URL parsing, sanitization)
│   └── exporters/             # Format-specific exporters
│       ├── base.py            # Abstract BaseExporter class
│       ├── markdown.py        # Markdown exporter with HTML conversion
│       ├── html.py            # Standalone HTML exporter
│       ├── text.py            # Plain text exporter
│       └── pdf.py             # PDF exporter (uses Confluence API)
├── tests/                     # Test suite (pytest)
│   ├── conftest.py            # Shared fixtures
│   └── test_*.py              # Test modules mirror source structure
├── docs/                      # Documentation
├── pyproject.toml             # Package configuration & dependencies
├── requirements.txt           # Runtime dependencies
└── requirements-dev.txt       # Development dependencies
```

## Architecture Patterns

### Exporter Pattern
All format exporters inherit from `BaseExporter` (abstract class):

```python
class BaseExporter(ABC):
    @property
    @abstractmethod
    def file_extension(self) -> str: ...
    
    @abstractmethod
    def export(self, page: PageData, output_path: str) -> str: ...
```

### Data Classes
- `PageData` (in fetcher.py): Represents a Confluence page with id, title, content, hierarchy info
- `Config` (in config.py): Configuration settings dataclass
- `ExportManifest` (in manifest.py): Export tracking and index generation

### Console Output
Uses `rich` library for styled output:
- `console` - Standard output with `safe_box=True` for Windows compatibility
- `error_console` - Error output to stderr
- Progress bars use `rich.progress.Progress`

## Key Conventions

### Code Style
- Follow PEP 8
- Use type hints for function signatures
- Docstrings in Google style format
- Maximum line length: 100 characters

### Error Handling
- Use `--skip-errors` flag behavior (default: True) - continue on individual page failures
- Log errors but don't crash the entire export
- Return meaningful exit codes (0 = success, 1 = error)

### Environment Variables
```
CONFLUENCE_BASE_URL    # e.g., https://yoursite.atlassian.net
CONFLUENCE_EMAIL       # User email for API auth
CONFLUENCE_API_TOKEN   # API token (never save to config files)
```

### CLI Argument Precedence
1. Command-line arguments (highest priority)
2. Config file settings
3. Environment variables
4. Default values

## Common Development Tasks

### Setup
```bash
pip install -e ".[dev]"
# or
pip install -r requirements.txt -r requirements-dev.txt
```

### Running Tests
```bash
pytest                          # Run all tests
pytest tests/test_cli.py        # Run specific test file
pytest -v                       # Verbose output
pytest --cov=confluence_export  # With coverage
```

### Linting
```bash
ruff check confluence_export tests
ruff format confluence_export tests
```

### Building
```bash
python -m build
```

### Running the CLI
```bash
# As module
python -m confluence_export --help

# As installed command
confluence-export --help
```

## Testing Guidelines

- All tests use mocking - no real API calls
- Use `@patch` decorator for mocking requests
- Fixtures in `conftest.py` provide common test data
- Test files mirror source structure (`cli.py` → `test_cli.py`)

### Key Test Fixtures
- `mock_page_response`: Sample Confluence API response
- `mock_client`: Mocked ConfluenceClient instance
- `tmp_path`: pytest's temporary directory fixture

## Important Implementation Details

### URL Parsing
The `extract_page_id()` function in `utils.py` handles:
- Full Confluence URLs (both modern and legacy formats)
- Raw page IDs (numeric strings)
- Returns None for invalid inputs

### Parallel Fetching
- Uses `concurrent.futures.ThreadPoolExecutor`
- Default: 4 workers (configurable via `--workers`)
- Falls back to sequential for single pages

### File Naming
- `sanitize_filename()` removes/replaces invalid characters
- Hierarchical structure: `SpaceKey/Parent/Child/page.md`
- Flat structure: `SpaceKey - Parent - Child - page.md`

### Config File Detection
Searches in order:
1. Current directory: `.confluence-export.toml`, `confluence-export.toml`, `.confluence-exportrc`
2. Home directory: same files

## When Making Changes

1. **Adding a new exporter**: Inherit from `BaseExporter`, implement `file_extension` and `export()`, register in `cli.py`'s format handling

2. **Adding CLI arguments**: Update `create_parser()` in `cli.py`, handle in `main()`, consider adding to `Config` dataclass

3. **Modifying API calls**: Update `ConfluenceClient` in `client.py`, add corresponding mocks in tests

4. **Adding dependencies**: Update both `pyproject.toml` and `requirements.txt`

## Don't Forget

- Run tests after changes: `pytest`
- Check linting: `ruff check .`
- Update version in `__init__.py` for releases
- Keep `CHANGELOG.md` updated for significant changes
- Windows compatibility: Use `safe_box=True` for rich Console, handle path separators

