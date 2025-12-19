# Contributing to Confluence Export CLI

Thank you for your interest in contributing to Confluence Export CLI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

Please be respectful and considerate in all interactions. We're all here to build something useful together.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/confluence-export.git
   cd confluence-export
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/yourusername/confluence-export.git
   ```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

   Or install from requirements files:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

### Project Structure

```
confluence-export/
├── confluence_export/
│   ├── __init__.py          # Package init
│   ├── __main__.py          # Module entry point
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
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Development dependencies
```

## Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for both linting and formatting.

### Linting Rules

We enforce the following rule sets:
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
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Check formatting without making changes
ruff format --check .
```

### Style Guidelines

- **Line length**: 100 characters maximum
- **Quotes**: Double quotes for strings
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Sorted with first-party imports (`confluence_export`) grouped separately

### Before Committing

Always run both the linter and formatter before committing:

```bash
ruff check --fix .
ruff format .
```

## Testing

We use [pytest](https://pytest.org/) for testing.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_cli.py

# Run a specific test
pytest tests/test_cli.py::test_function_name

# Run tests with coverage report
pytest --cov=confluence_export --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Test Markers

- `@pytest.mark.unit` - Fast tests with no external dependencies
- `@pytest.mark.integration` - Tests that may require mocking external services

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with the `test_` prefix
- Name test functions with the `test_` prefix
- Use descriptive test names that explain what's being tested
- Use fixtures from `conftest.py` when available
- Mock external API calls using `responses` or `pytest-mock`

Example test structure:

```python
import pytest
from confluence_export.client import ConfluenceClient


class TestConfluenceClient:
    """Tests for the ConfluenceClient class."""

    def test_client_initialization(self):
        """Test that the client initializes with correct parameters."""
        client = ConfluenceClient(
            base_url="https://example.atlassian.net",
            email="test@example.com",
            api_token="token123"
        )
        assert client.base_url == "https://example.atlassian.net"

    @pytest.mark.unit
    def test_get_page_returns_page_data(self, mock_confluence_response):
        """Test that get_page returns the expected page data."""
        # Test implementation
        pass
```

## Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-docx-export` - New features
- `fix/handle-empty-pages` - Bug fixes
- `docs/update-readme` - Documentation updates
- `refactor/simplify-fetcher` - Code refactoring

### Commit Messages

Write clear, concise commit messages:
- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 72 characters
- Add a blank line before detailed description if needed

Examples:
```
Add support for DOCX export format

Fix crash when exporting pages with no content

Update installation instructions in README
```

### Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit them

3. **Ensure all tests pass**:
   ```bash
   pytest
   ```

4. **Ensure code passes linting**:
   ```bash
   ruff check .
   ruff format --check .
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub with:
   - A clear title describing the change
   - A description of what was changed and why
   - Reference to any related issues (e.g., "Fixes #123")

7. **Respond to review feedback** and make updates as needed

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Tests pass locally
- [ ] New code has appropriate test coverage
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

1. **Python version** (`python --version`)
2. **Package version** (`confluence-export --version`)
3. **Operating system**
4. **Steps to reproduce** the issue
5. **Expected behavior**
6. **Actual behavior**
7. **Error messages** or stack traces (if applicable)

### Feature Requests

When requesting a feature, please include:

1. **Problem statement** - What problem does this solve?
2. **Proposed solution** - How would this feature work?
3. **Alternatives considered** - What other approaches did you consider?
4. **Use cases** - Who would benefit from this feature?

## Adding New Export Formats

To add a new export format:

1. Create a new exporter class in `confluence_export/exporters/`:

   ```python
   from .base import BaseExporter

   class NewFormatExporter(BaseExporter):
       """Exporter for NewFormat files."""

       format_name = "newformat"
       file_extension = ".nf"

       def export(self, page_data: dict, output_path: str) -> str:
           # Implementation here
           pass
   ```

2. Register the exporter in `confluence_export/exporters/__init__.py`

3. Add tests in `tests/test_exporters.py`

4. Update documentation in `README.md` and `docs/`

## Questions?

If you have questions about contributing, feel free to open an issue with the "question" label.

---

Thank you for contributing! 🎉


