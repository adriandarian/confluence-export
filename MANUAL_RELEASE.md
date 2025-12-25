# Manual Release Guide

This guide walks you through manually releasing Confluence Export CLI when GitHub Actions aren't available.

## Prerequisites

```bash
# Install build tools
pip install build wheel twine pyinstaller
```

## Step 1: Update Version

Edit `confluence_export/__init__.py` and update the version:

```python
__version__ = "1.0.1"  # Increment as needed
```

Commit the change:
```bash
git add confluence_export/__init__.py
git commit -m "Release v1.0.1"
```

## Step 2: Build All Artifacts

Run the manual release script:

```bash
./scripts/manual-release.sh
```

Or build manually:

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build wheel and source distribution
python -m build

# Build executable (macOS/Linux)
pyinstaller confluence_export.spec --clean --noconfirm
mv dist/confluence-export dist/confluence-export-macos-$(uname -m)  # or linux-$(uname -m)
chmod +x dist/confluence-export-macos-$(uname -m)
```

## Step 3: Create Git Tag

```bash
VERSION="1.0.1"  # Update this
TAG="v${VERSION}"

# Create and push tag
git tag ${TAG}
git push origin ${TAG}
```

## Step 4: Create GitHub Release

1. Go to: `https://github.com/YOUR_USERNAME/confluence-export/releases/new`
2. Select the tag you just created
3. Title: `v1.0.1` (or your version)
4. Description: Use "Generate release notes" or write your own
5. **Upload all files from `dist/` directory:**
   - `confluence_export-1.0.1-py3-none-any.whl`
   - `confluence_export-1.0.1.tar.gz`
   - `confluence-export-macos-*` (or linux/windows executables)
6. Click "Publish release"

## Step 5: Publish to PyPI

### First Time Setup (if not done)

1. Create account on [PyPI](https://pypi.org/account/register/)
2. Create API token: https://pypi.org/manage/account/token/
3. Configure twine:
   ```bash
   # Save credentials (optional, or use environment variables)
   # ~/.pypirc will be created
   ```

### Upload to PyPI

```bash
# Upload to PyPI (requires API token)
twine upload dist/*.whl dist/*.tar.gz
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

### Test Upload (Optional)

Test on TestPyPI first:
```bash
twine upload --repository testpypi dist/*.whl dist/*.tar.gz
```

## Step 6: Verify Release

1. **GitHub Release**: Check https://github.com/YOUR_USERNAME/confluence-export/releases
2. **PyPI**: Check https://pypi.org/project/confluence-export/
3. **Test Installation**:
   ```bash
   pip install confluence-export==1.0.1
   confluence-export --version
   ```

## Building Executables for Other Platforms

### Windows Executable

On a Windows machine:
```cmd
pyinstaller confluence_export.spec --clean --noconfirm
move dist\confluence-export.exe dist\confluence-export-windows-x86_64.exe
```

### Linux Executable

On a Linux machine:
```bash
pyinstaller confluence_export.spec --clean --noconfirm
mv dist/confluence-export dist/confluence-export-linux-x86_64
chmod +x dist/confluence-export-linux-x86_64
```

### macOS Executable

On a macOS machine:
```bash
pyinstaller confluence_export.spec --clean --noconfirm
mv dist/confluence-export dist/confluence-export-macos-$(uname -m)
chmod +x dist/confluence-export-macos-$(uname -m)
```

## Quick Reference

```bash
# Full manual release process
VERSION="1.0.1"
TAG="v${VERSION}"

# 1. Update version in __init__.py, then:
git add confluence_export/__init__.py
git commit -m "Release ${TAG}"

# 2. Build
./scripts/manual-release.sh

# 3. Tag and push
git tag ${TAG}
git push origin ${TAG}

# 4. Create GitHub release manually (upload dist/* files)

# 5. Publish to PyPI
twine upload dist/*.whl dist/*.tar.gz
```

## Troubleshooting

### "Tag already exists"
If the tag exists, either:
- Use a new version number
- Delete the tag: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`

### "PyPI upload fails"
- Check your API token is correct
- Ensure version number is unique (not already on PyPI)
- Try TestPyPI first: `twine upload --repository testpypi dist/*`

### "Executable doesn't work"
- Ensure you built it on the target platform
- Check file permissions: `chmod +x dist/confluence-export-*`
- Test locally before uploading

