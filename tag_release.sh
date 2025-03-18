#!/bin/bash
# Script to tag and push a new release

# Get version from __init__.py
VERSION=$(grep '^__version__ = ' letterhead_pdf/__init__.py | cut -d'"' -f2)

# Create and push tag
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin "v$VERSION"

echo "Created and pushed tag v$VERSION"
echo "This will trigger the GitHub workflow to publish to PyPI"
