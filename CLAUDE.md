# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mac-letterhead is a macOS utility that merges letterhead templates with PDF and Markdown documents using a drag-and-drop interface. It creates AppleScript droplet applications that users can drop documents onto to automatically apply letterhead templates.

## Development Commands

### Build and Test Commands
```bash
# Development setup
make dev-install        # Install package for local development using uv
make dev-droplet        # Create development droplet using local code
make test-setup         # Set up test files and environment

# Testing (uses Python 3.11 by default)
make test-basic         # Run basic tests (PDF only)
make test-full          # Run full tests (PDF + Markdown with ReportLab)
make test-weasyprint    # Run WeasyPrint tests (requires system dependencies)
make test-all           # Run all tests
make test-py3.11-basic  # Test specific Python version

# Cleaning
make clean-all          # Clean everything (build artifacts, test files, droplets)
make clean-build        # Remove build artifacts and virtual environments only
make clean-droplets     # Remove test droplets only

# Release
make release-version    # Update version numbers in source files  
make release-publish    # Run tests, update version, and publish to PyPI
```

### System Dependencies
For WeasyPrint functionality (high-quality Markdown to PDF conversion):
```bash
brew install pango cairo fontconfig freetype harfbuzz
```

### Running the Application
```bash
# Install and use
uvx mac-letterhead install /path/to/letterhead.pdf

# Direct merge operations
uvx mac-letterhead merge letterhead.pdf "Output" ~/Desktop document.pdf
uvx mac-letterhead merge-md letterhead.pdf "Output" ~/Desktop document.md
```

### Testing Individual Components
```bash
# Run specific test for Python version
make test-py3.11-basic
make test-py3.11-full
make test-py3.11-weasyprint

# Test files are generated in tests/files/
# Version outputs in tests/version-*.txt
```

## Architecture Overview

### Core Components

**Main Application (`letterhead_pdf/main.py`)**
- CLI interface with argparse
- Command handlers: `install`, `merge`, `merge-md`
- macOS save dialog integration using AppKit/Foundation
- Logging configuration and error handling

**PDF Processing Pipeline**
- `PDFMerger` (pdf_merger.py): Core PDF merging with multiple blend strategies
- `MarkdownProcessor` (markdown_processor.py): Markdown to PDF conversion with smart margin detection
- `pdf_utils.py`: Low-level PDF operations using Quartz/CoreGraphics

**Droplet Creation System (`letterhead_pdf/installation/`)**
- `DropletBuilder`: Main orchestrator for droplet creation
- `AppleScriptGenerator`: Creates AppleScript code for droplets
- `ResourceManager`: Handles icon and resource embedding
- `MacOSIntegration`: macOS-specific integration (app bundle creation)
- `DropletValidator`: Validates created droplets

### Key Features

**Smart Margin Detection**
- Analyzes letterhead PDFs using PyMuPDF (fitz) to detect content regions
- Automatically calculates safe printable areas for different letterhead positions
- Supports left, right, and center-positioned letterheads
- Maintains ~82% usable page width regardless of letterhead design

**Multi-Page Letterhead Support**
- Single page: Applied to all document pages
- Two pages: First page → first document page, second page → other pages
- Three pages: First page → first page, second page → even pages, third page → odd pages

**Dual Rendering Pipeline**
- WeasyPrint: High-quality rendering with full CSS support (preferred)
- ReportLab: Fallback rendering for when WeasyPrint unavailable

**PDF Merge Strategies**
- `darken` (default): Content first, letterhead with multiply blend
- `multiply`: Original multiply blend strategy
- `overlay`: Overlay blend mode for better visibility
- `transparency`: Uses transparency layers
- `reverse`: Letterhead on top with transparency

### Dependencies and Compatibility

**Core Dependencies**
- PyObjC frameworks (Cocoa, Quartz) for macOS integration
- PyMuPDF for PDF analysis and margin detection
- ReportLab for fallback PDF generation
- WeasyPrint for high-quality Markdown rendering (optional)

**Optional Dependencies**
- Markdown + Pygments for syntax highlighting
- HTML5lib for HTML parsing

**Python Support**
- Requires Python ≥3.11
- Currently tested with Python 3.11

### File Structure Patterns

**Package Structure**
- Main entry point: `letterhead_pdf/main.py` 
- Core logic: `pdf_merger.py`, `markdown_processor.py`, `pdf_utils.py`
- Installation system: `letterhead_pdf/installation/` (modular components)
- Resources: `letterhead_pdf/resources/` (defaults.css, icons)
- Tests: `tests/` with generated test files and utilities

**Configuration**
- Version management: Single source in `letterhead_pdf/__init__.py`
- Build system: `pyproject.toml` with Hatch backend
- Make targets: Comprehensive Makefile for all operations

### Development Workflow

**Testing Strategy**
- Test droplets created on Desktop for manual testing
- Automated tests for multiple Python versions
- Separate test environments for basic/full/WeasyPrint functionality
- Generated test files in `tests/files/` for validation

**Release Process**
1. Update VERSION in Makefile
2. `make release-publish` runs tests and updates version
3. Commits and tags automatically
4. GitHub Actions handles PyPI publication

### macOS Integration Details

**AppleScript Droplets**
- Created as full .app bundles with embedded Python code
- Support both development mode (local code) and production mode (installed package)
- Include letterhead preview functionality
- Handle file permissions and sandbox restrictions

**System Integration**
- Uses Quartz/CoreGraphics for PDF operations (native macOS PDF handling)
- AppKit for save dialogs and UI interactions
- Foundation for file operations and system integration