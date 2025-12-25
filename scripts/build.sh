#!/bin/bash
# Build script for Confluence Export CLI
# Creates both wheel package and standalone executables

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔨 Building Confluence Export CLI..."
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
rm -rf confluence_export/__pycache__/ tests/__pycache__/
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Clean complete"
echo ""

# Build wheel package
echo "📦 Building wheel package..."
python -m build --wheel
echo "✅ Wheel package built: dist/confluence_export-*.whl"
echo ""

# Build executable (PyInstaller)
if command -v pyinstaller &> /dev/null; then
    echo "🔧 Building standalone executable..."
    pyinstaller confluence_export.spec --clean --noconfirm
    echo "✅ Executable built: dist/confluence-export"
    echo ""
    
    # Show file size
    if [ -f "dist/confluence-export" ]; then
        SIZE=$(du -h dist/confluence-export | cut -f1)
        echo "📊 Executable size: $SIZE"
    fi
else
    echo "⚠️  PyInstaller not found. Skipping executable build."
    echo "   Install with: pip install pyinstaller"
fi

echo ""
echo "✨ Build complete!"
echo ""
echo "📦 Distribution files:"
ls -lh dist/ 2>/dev/null || echo "  (none)"

