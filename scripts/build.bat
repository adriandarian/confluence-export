@echo off
REM Build script for Confluence Export CLI (Windows)
REM Creates both wheel package and standalone executables

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo 🔨 Building Confluence Export CLI...
echo.

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.egg-info rmdir /s /q *.egg-info
if exist confluence_export\__pycache__ rmdir /s /q confluence_export\__pycache__
if exist tests\__pycache__ rmdir /s /q tests\__pycache__
echo ✅ Clean complete
echo.

REM Build wheel package
echo 📦 Building wheel package...
python -m build --wheel
if errorlevel 1 (
    echo ❌ Failed to build wheel package
    exit /b 1
)
echo ✅ Wheel package built: dist\confluence_export-*.whl
echo.

REM Build executable (PyInstaller)
where pyinstaller >nul 2>&1
if %errorlevel% equ 0 (
    echo 🔧 Building standalone executable...
    pyinstaller confluence_export.spec --clean --noconfirm
    if errorlevel 1 (
        echo ❌ Failed to build executable
        exit /b 1
    )
    echo ✅ Executable built: dist\confluence-export.exe
    echo.
    
    REM Show file size
    if exist "dist\confluence-export.exe" (
        for %%A in ("dist\confluence-export.exe") do (
            echo 📊 Executable size: %%~zA bytes
        )
    )
) else (
    echo ⚠️  PyInstaller not found. Skipping executable build.
    echo    Install with: pip install pyinstaller
)

echo.
echo ✨ Build complete!
echo.
echo 📦 Distribution files:
dir /b dist 2>nul || echo   (none)

