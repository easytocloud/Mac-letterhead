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

# Testing (uses Python 3.10 by default)
make test-basic         # Run basic tests (PDF only)
make test-full          # Run full tests (PDF + Markdown with ReportLab)
make test-weasyprint    # Run WeasyPrint tests (requires system dependencies)
make test-all           # Run all tests
make test-py3.10-basic  # Test specific Python version

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
uvx mac-letterhead install --name "Company"

# Direct merge operations
uvx mac-letterhead merge letterhead.pdf "Output" ~/Desktop document.pdf
uvx mac-letterhead merge-md letterhead.pdf "Output" ~/Desktop document.md

# MCP server for AI integration
uvx mac-letterhead mcp --style easytocloud        # Style-specific server
uvx mac-letterhead mcp                             # Generic server, style specified per tool call
uvx mac-letterhead mcp --style personal --output-dir ~/Documents/personal-docs
```

### Install Command Behavior

The `install` command creates droplet applications using a name-based convention:

- `--name` is mandatory and sets both the app name and style
- Automatically resolves `~/.letterhead/<name>.pdf` and `~/.letterhead/<name>.css`
- `--letterhead` and `--css` flags can override the resolved paths
- Applications are created on Desktop by default

**Examples:**
```bash
# Uses ~/.letterhead/company.pdf and ~/.letterhead/company.css
uvx mac-letterhead install --name "company"

# Override letterhead but keep name-based CSS
uvx mac-letterhead install --name "report" --letterhead /path/to/custom.pdf

# Development droplet using local code
uvx mac-letterhead install --name "test" --dev
```

### Testing Individual Components
```bash
# Run specific test for Python version
make test-py3.10-basic  # Python 3.10 support
make test-py3.11-full   # Python 3.11 support
make test-py3.12-weasyprint # Python 3.12 support

# Test all versions at once
make test-all

# Test files are processed from test-input/ 
# Version-specific outputs in test-output/ (e.g., css-test-markdown-py3.10-basic.pdf)
```

## Architecture Overview

### Core Components

**Main Application (`letterhead_pdf/main.py`)**
- CLI interface with argparse
- Command handlers: `install`, `merge`, `merge-md`, `mcp`
- MCP server integration for AI tool usage
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

**MCP Server Integration (`letterhead_pdf/mcp_server.py`)**
- Model Context Protocol server for AI tool integration
- Dynamic tool schema adaptation based on server configuration
- Convention-based file resolution from `~/.letterhead/` directory
- Support for both generic multi-style and dedicated single-style servers
- Tools: `create_letterhead_pdf`, `merge_letterhead_pdf`, `analyze_letterhead`, `list_letterhead_templates`

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

**MCP Server Capabilities**
- **Dual Configuration Modes**: Generic multi-style server or dedicated single-style servers
- **Dynamic Tool Schemas**: Tools adapt parameter requirements based on server configuration
- **Convention-Based Resolution**: Auto-resolves `~/.letterhead/<style>.pdf` and `~/.letterhead/<style>.css`
- **AI Integration**: Enables natural language PDF generation through Claude and other AI tools
- **Flexible Output Control**: Configurable output directories and filename prefixes

### Dependencies and Compatibility

**Core Dependencies**
- PyObjC frameworks (Cocoa, Quartz) for macOS integration
- PyMuPDF for PDF analysis and margin detection
- ReportLab for fallback PDF generation
- WeasyPrint for high-quality Markdown rendering (optional)

**Optional Dependencies**
- Markdown + Pygments for syntax highlighting
- HTML5lib for HTML parsing
- MCP (Model Context Protocol) for AI tool integration

**Python Support**
- Requires Python ≥3.10
- Currently tested with Python 3.10, 3.11, 3.12

### File Structure Patterns

**Package Structure**
- Main entry point: `letterhead_pdf/main.py` 
- Core logic: `pdf_merger.py`, `markdown_processor.py`, `pdf_utils.py`
- MCP server: `letterhead_pdf/mcp_server.py` (AI tool integration)
- Installation system: `letterhead_pdf/installation/` (modular components)
- Resources: `letterhead_pdf/resources/` (defaults.css, icons)
- Tests: `tests/` with generated test files and utilities
- Documentation: `README_MCP.md`, `sample_mcp_config.json`, `setup_letterheads.sh`

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

## MCP Server Integration

### Configuration Setup
Mac-letterhead includes an MCP (Model Context Protocol) server that enables AI tools like Claude to create letterheaded PDFs directly through natural language commands.

**Directory Structure** (Convention-based):
```bash
~/.letterhead/
├── easytocloud.pdf     # Letterhead template
├── easytocloud.css     # Optional styling
├── personal.pdf        # Another letterhead
└── personal.css        # Its styling
```

### Server Configuration Modes

**Generic Multi-Style Server** (Recommended for flexibility):
```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Generic letterhead PDF generator"
    }
  }
}
```
- Usage: *"Using letterhead server, create an easytocloud style PDF about..."*
- Tools require `style` parameter (mandatory)
- Can handle any style in `~/.letterhead/`

**Style-Specific Servers** (Optimized for dedicated use):
```json
{
  "mcpServers": {
    "easytocloud": {
      "command": "uvx", 
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "easytocloud"],
      "description": "EasyToCloud letterhead generator"
    }
  }
}
```
- Usage: *"Create an easytocloud letterheaded PDF about..."*
- Server pre-configured with style
- Tools don't require style parameter

### Available MCP Tools

1. **`create_letterhead_pdf`**: Convert Markdown to letterheaded PDF
2. **`merge_letterhead_pdf`**: Apply letterhead to existing PDF  
3. **`analyze_letterhead`**: Analyze letterhead margins and layout
4. **`list_letterhead_templates`**: List available letterhead files

### Dynamic Tool Behavior
The MCP server automatically adapts tool schemas based on configuration:
- **Generic server**: Tools require `style` parameter
- **Style-specific server**: Tools use pre-configured style, `style` parameter not available

### Setup Commands
```bash
# Set up letterhead directory and sample files
./setup_letterheads.sh

# Test server configuration  
uvx mac-letterhead mcp --style test-style
uvx mac-letterhead mcp  # Generic mode
```

For complete MCP configuration details, see `README_MCP.md`.