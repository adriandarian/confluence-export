# Configuration Guide

Confluence Export CLI supports configuration files to save your commonly used settings. This eliminates the need to type long command-line arguments repeatedly.

## Table of Contents

- [Configuration File Locations](#configuration-file-locations)
- [File Format](#file-format)
- [Configuration Sections](#configuration-sections)
- [Creating a Configuration File](#creating-a-configuration-file)
- [Precedence Order](#precedence-order)
- [Examples](#examples)
- [Security Considerations](#security-considerations)

---

## Configuration File Locations

The tool searches for configuration files in the following order:

1. **Current directory** - `.confluence-export.toml` or `confluence-export.toml`
2. **Home directory** - `~/.confluence-export.toml`

You can also specify a custom config file with the `--config` option:

```bash
confluence-export --config /path/to/my-config.toml --pages 123456
```

### Supported File Names

- `.confluence-export.toml` (recommended)
- `confluence-export.toml`
- `.confluence-exportrc`

---

## File Format

Configuration files use [TOML](https://toml.io/) format, which is easy to read and write.

### Basic Structure

```toml
# Confluence Export Configuration

[auth]
base_url = "https://yoursite.atlassian.net"
email = "your.email@company.com"
# Note: API token should be set via environment variable

[pages]
ids = ["123456", "789012"]
# file = "pages.txt"

[export]
output = "./confluence-exports"
formats = ["markdown", "html"]
flat = false
include_children = true
manifest = false

[advanced]
workers = 4
skip_errors = true
verbose = false
quiet = false
```

---

## Configuration Sections

### `[auth]` - Authentication

| Key | Type | Description |
|-----|------|-------------|
| `base_url` | string | Your Confluence site URL |
| `email` | string | Your Atlassian account email |

> **Security Note:** The API token should NOT be stored in the config file. Use the `CONFLUENCE_API_TOKEN` environment variable instead.

```toml
[auth]
base_url = "https://yourcompany.atlassian.net"
email = "developer@company.com"
```

### `[pages]` - Page Selection

| Key | Type | Description |
|-----|------|-------------|
| `ids` | array of strings | List of page IDs or URLs to export |
| `file` | string | Path to file containing page IDs (one per line) |

```toml
[pages]
# Specify pages directly
ids = [
    "123456789",
    "987654321",
    "https://site.atlassian.net/wiki/spaces/DOC/pages/111111/Page"
]

# Or use a file
# file = "pages-to-export.txt"
```

### `[export]` - Export Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `output` | string | `"./confluence-exports"` | Output directory |
| `formats` | array of strings | `["markdown"]` | Export formats |
| `flat` | boolean | `false` | Use flat file structure |
| `include_children` | boolean | `false` | Include child pages |
| `manifest` | boolean | `false` | Generate manifest files |

```toml
[export]
output = "./docs/exported"
formats = ["markdown", "html"]
flat = false
include_children = true
manifest = true
```

### `[advanced]` - Advanced Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `workers` | integer | `4` | Number of parallel fetch workers |
| `skip_errors` | boolean | `true` | Continue on page errors |
| `verbose` | boolean | `false` | Show detailed output |
| `quiet` | boolean | `false` | Suppress output |

```toml
[advanced]
workers = 8
skip_errors = true
verbose = true
```

---

## Creating a Configuration File

### Method 1: Use `--save-config`

The easiest way to create a config file is to run your desired command with `--save-config`:

```bash
confluence-export \
  --base-url https://yoursite.atlassian.net \
  --email your.email@company.com \
  --pages 123456 789012 \
  --format markdown html \
  --include-children \
  --output ./my-exports \
  --save-config
```

This creates `.confluence-export.toml` in the current directory with all your settings.

### Method 2: Specify Output Path

Save to a specific file:

```bash
confluence-export \
  --base-url https://yoursite.atlassian.net \
  --pages 123456 \
  --save-config my-project.toml
```

### Method 3: Create Manually

Create a file named `.confluence-export.toml`:

```toml
# My Project Configuration

[auth]
base_url = "https://mycompany.atlassian.net"
email = "me@mycompany.com"

[pages]
ids = ["123456789"]

[export]
output = "./docs"
formats = ["markdown"]
include_children = true
```

---

## Precedence Order

When multiple sources provide the same setting, they are applied in this order (later overrides earlier):

1. **Defaults** - Built-in default values
2. **Config file** - Values from `.confluence-export.toml`
3. **Environment variables** - `CONFLUENCE_*` variables
4. **Command-line arguments** - Explicit CLI flags

### Example

Given this config file:
```toml
[export]
output = "./from-config"
formats = ["markdown"]
```

And this command:
```bash
confluence-export --output ./from-cli --pages 123456
```

The output directory will be `./from-cli` (CLI overrides config).

---

## Examples

### Development Project Config

```toml
# .confluence-export.toml - Development documentation sync

[auth]
base_url = "https://myteam.atlassian.net"
email = "dev@myteam.com"

[pages]
# Root documentation page
ids = ["123456789"]

[export]
output = "./docs/confluence"
formats = ["markdown"]
include_children = true
flat = false
manifest = true

[advanced]
workers = 4
verbose = false
```

### Backup Script Config

```toml
# backup-config.toml - Weekly backup configuration

[auth]
base_url = "https://company.atlassian.net"
email = "backup-service@company.com"

[export]
output = "/backups/confluence/latest"
formats = ["markdown", "html", "pdf"]
include_children = true
manifest = true

[advanced]
workers = 2
skip_errors = true
quiet = true
```

### Multi-Space Export Config

```toml
# spaces-config.toml

[auth]
base_url = "https://enterprise.atlassian.net"
email = "admin@enterprise.com"

[pages]
# Multiple spaces - run separately for each
ids = [
    "11111111",  # Engineering root
    "22222222",  # Product root
    "33333333",  # Design root
]

[export]
output = "./all-docs"
formats = ["markdown"]
include_children = true
flat = false
```

### Minimal Config (Auth Only)

```toml
# Just save auth settings, specify pages on command line

[auth]
base_url = "https://mysite.atlassian.net"
email = "user@mysite.com"
```

Usage:
```bash
export CONFLUENCE_API_TOKEN=your-token
confluence-export --pages 123456 --format markdown
```

---

## Security Considerations

### Never Store API Tokens in Config Files

The API token should always be provided via:

1. **Environment variable** (recommended):
   ```bash
   export CONFLUENCE_API_TOKEN=your-api-token
   ```

2. **`.env` file** (for local development):
   ```env
   CONFLUENCE_API_TOKEN=your-api-token
   ```

3. **Command-line argument** (for one-off use):
   ```bash
   confluence-export --token your-api-token --pages 123456
   ```

### Gitignore Patterns

Add these to your `.gitignore`:

```gitignore
# Confluence Export
.env
*.env
.confluence-export.toml
confluence-export.toml
pages.txt
```

### File Permissions

On Unix systems, protect your config file:

```bash
chmod 600 .confluence-export.toml
```

---

## Ignoring Config Files

To run without loading any configuration file:

```bash
confluence-export --no-config --pages 123456
```

This is useful when you want to use a completely different set of options without being affected by an existing config.

---

## Related Documentation

- [User Guide](user-guide.md) - Complete usage guide
- [API Reference](api-reference.md) - Python API documentation
- [Development Guide](development.md) - Contributing and development


