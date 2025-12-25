#!/bin/bash
# Manual Release Script for Confluence Export CLI
# This script builds all distribution artifacts for manual release

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Get version from __init__.py
VERSION=$(grep -E "^__version__" confluence_export/__init__.py | cut -d'"' -f2)
TAG="v${VERSION}"

echo "🚀 Manual Release Script for Confluence Export CLI"
echo "📦 Version: ${VERSION}"
echo "🏷️  Tag: ${TAG}"
echo ""

# Check if tag exists
if git rev-parse "${TAG}" >/dev/null 2>&1; then
    echo "⚠️  Tag ${TAG} already exists!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
rm -rf confluence_export/__pycache__/ tests/__pycache__/
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Clean complete"
echo ""

# Build wheel and source distribution
echo "📦 Building wheel and source distribution..."
python -m build
echo "✅ Built:"
ls -lh dist/*.whl dist/*.tar.gz 2>/dev/null || true
echo ""

# Build executable for current platform
if command -v pyinstaller &> /dev/null; then
    echo "🔧 Building standalone executable for $(uname -s)..."
    pyinstaller confluence_export.spec --clean --noconfirm
    
    # Rename executable based on platform
    OS_NAME=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    if [ -f "dist/confluence-export" ]; then
        if [ "$OS_NAME" = "darwin" ]; then
            mv dist/confluence-export "dist/confluence-export-macos-${ARCH}"
            chmod +x "dist/confluence-export-macos-${ARCH}"
            echo "✅ Built: dist/confluence-export-macos-${ARCH}"
        elif [ "$OS_NAME" = "linux" ]; then
            mv dist/confluence-export "dist/confluence-export-linux-${ARCH}"
            chmod +x "dist/confluence-export-linux-${ARCH}"
            echo "✅ Built: dist/confluence-export-linux-${ARCH}"
        fi
    fi
else
    echo "⚠️  PyInstaller not found. Skipping executable build."
    echo "   Install with: pip install pyinstaller"
fi

echo ""
echo "✨ Build complete!"
echo ""
echo "📦 Distribution files ready in dist/:"
ls -lh dist/ 2>/dev/null || echo "  (none)"
echo ""
echo "📋 Next steps:"
echo "1. Review the files in dist/"
echo "2. Create git tag: git tag ${TAG}"
echo "3. Push tag: git push origin ${TAG}"
echo "4. Create GitHub release at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases/new"
echo "5. Upload all files from dist/ to the release"
echo "6. Publish to PyPI: twine upload dist/*.whl dist/*.tar.gz"

