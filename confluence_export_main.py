#!/usr/bin/env python3
"""Entry point for PyInstaller executable."""

import sys

from confluence_export.cli import main

if __name__ == "__main__":
    sys.exit(main())
