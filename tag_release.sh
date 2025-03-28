#!/bin/bash
# Script to tag and create a new release

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: GitHub CLI is not authenticated"
    echo "Please run: gh auth login"
    exit 1
fi

# Get version from __init__.py
VERSION=$(grep '^__version__ = ' letterhead_pdf/__init__.py | cut -d'"' -f2)

# Create and push tag
echo "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "Release version $VERSION"
git push origin "v$VERSION"

# Generate release notes from git log
echo "Generating release notes..."
RELEASE_NOTES=$(git log --pretty=format:"- %s" $(git describe --tags --abbrev=0 @^)..@)

# Create GitHub release
echo "Creating GitHub release v$VERSION..."
gh release create "v$VERSION" \
    --title "Release v$VERSION" \
    --notes "Release version $VERSION

Changes in this release:
$RELEASE_NOTES" \
    --draft=false

echo "✓ Created and pushed tag v$VERSION"
echo "✓ Created GitHub release v$VERSION"
echo "✓ This will trigger the GitHub workflow to publish to PyPI"
