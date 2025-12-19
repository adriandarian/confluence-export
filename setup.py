"""Setup script for Confluence Export CLI."""

from pathlib import Path

from setuptools import find_packages, setup

long_description = Path("README.md").read_text(encoding="utf-8")
requirements_text = Path("requirements.txt").read_text(encoding="utf-8")
requirements = [
    line.strip()
    for line in requirements_text.splitlines()
    if line.strip() and not line.startswith("#")
]

setup(
    name="confluence-export",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Export Confluence pages to Markdown, HTML, Text, or PDF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/confluence-export",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "confluence-export=confluence_export.cli:main",
        ],
    },
)
