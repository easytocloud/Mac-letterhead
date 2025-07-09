# Mac-letterhead

![PyPI Version](https://img.shields.io/pypi/v/Mac-letterhead.svg)
![Build Status](https://github.com/easytocloud/Mac-letterhead/actions/workflows/publish.yml/badge.svg)
![License](https://img.shields.io/github/license/easytocloud/Mac-letterhead.svg)

<!-- GitHub can't render .icns files directly, so we use HTML to link the icon badge -->
<a href="https://pypi.org/project/Mac-letterhead/" title="Mac-letterhead on PyPI">
  <img src="https://raw.githubusercontent.com/easytocloud/Mac-letterhead/main/letterhead_pdf/resources/icon.png" width="128" height="128" alt="Mac-letterhead Logo" align="right" />
</a>

A macOS utility for merging letterhead templates with PDF and Markdown documents. Apply company letterheads, watermarks, or stationery to your documents with a simple drag-and-drop interface.

## Why Mac-letterhead?

- **Drag & Drop Simplicity**: Convert your letterhead PDF into a macOS app that applies your letterhead with a simple drag-and-drop
- **Professional Results**: Merge PDFs without quality loss, preserving all formatting and content
- **Smart Markdown Support**: Convert Markdown files to beautifully formatted PDFs, automatically detecting and respecting letterhead margins
- **Multi-page Letterhead Support**: Different designs for first page, even pages, and odd pages
- **Multiple Merging Strategies**: Various blending modes to suit different letterhead designs
- **No Subscription Fees**: Free, open-source solution for businesses of all sizes

## Installation

Mac-letterhead requires the Python uv package manager (install with `pip install uv` if you don't have it).

### System Dependencies

First, install the required system dependencies (one-time setup):

```bash
brew install pango cairo fontconfig freetype harfbuzz
```

### Install Mac-letterhead

Starting with version 0.9.5, Mac-letterhead includes enhanced smart margin detection and improved architecture:

```bash
uvx mac-letterhead
```

> **Note**: Version 0.9.5 includes intelligent letterhead positioning detection, modular architecture, and enhanced development tooling.

## Quick Start

### 1. Create a Desktop Droplet Application

The "install" command creates a desktop application (droplet) that you can use to apply your letterhead:

```bash
uvx mac-letterhead install /path/to/your/letterhead.pdf
```

This creates a desktop application icon that you can drag-and-drop documents onto. The application is named based on your letterhead file.

### 2. Apply Letterhead to Documents

You can use either PDF or Markdown files:

#### For PDF Documents
1. Export your document as a PDF
2. Drag and drop the PDF onto your letterhead application
3. Save the merged document

#### For Markdown Documents
1. Write your document in Markdown (.md)
2. Drag and drop the Markdown file onto your letterhead application
3. The file will be converted to PDF with proper margins and merged with the letterhead
4. Save the merged document

That's it! Your document now has the letterhead applied.

### Markdown Features

Mac-letterhead provides intelligent Markdown-to-PDF conversion with letterhead support:

- **Smart Letterhead Detection**: Automatically analyzes letterhead PDFs to find safe areas for content
- **Intelligent Position Detection**: Recognizes left, right, and center-positioned letterheads for optimal margins
- **Professional Formatting**:
  - Headers (h1-h6) with proper sizing and spacing
  - Tables with clean borders and consistent padding
  - Code blocks with syntax highlighting
  - Lists, blockquotes, and footnotes
  - Links and images
- **Layout Intelligence**:
  - Detects both text and graphics in letterhead
  - Adjusts margins to avoid overlapping with logos and footer text
  - Maintains consistent formatting across pages
  - Prevents table splitting across pages

#### What's New in v0.9.5

- **Smart Margin Detection Algorithm**:
  - Intelligently detects letterhead position (left, right, center)
  - **Left-positioned letterheads**: Wider left margin, minimal right margin
  - **Right-positioned letterheads**: Minimal left margin, wider right margin  
  - **Center-positioned letterheads**: Symmetric margins
  - Provides ~82% usable page width regardless of letterhead design
- **Modular Architecture**:
  - Reorganized codebase with better component separation
  - Enhanced troubleshooting capabilities
  - Cleaner installation system
- **Development Mode**:
  - Local test droplets for development and testing
  - Enhanced debugging capabilities
- **uvx Environment Compatibility**:
  - Fixed WeasyPrint library path issues in isolated environments
  - Improved reliability across different system configurations

#### Previous Enhancements

- **v0.8.2**: Fixed ReportLab dependency and improved fallback rendering
- **v0.8.1**: Markdown support included by default
- **v0.8.0**: Enhanced code formatting and improved typography

## Advanced Options

### Custom Application Name and Location

```bash
uvx mac-letterhead install /path/to/letterhead.pdf --name "Company Letterhead"
```

### Development Mode

For development and testing, you can create droplets that use your local development code:

```bash
# Create a development droplet using local code
uvx mac-letterhead install /path/to/letterhead.pdf --name "Development Test" --dev
```

Development droplets allow you to test changes without affecting production installations.

### Different Merging Strategies

You can directly merge documents with specific strategies:

For PDF files:

```bash
uvx mac-letterhead merge /path/to/letterhead.pdf "Document" ~/Desktop /path/to/document.pdf --strategy overlay
```

For Markdown files:
```bash
uvx mac-letterhead merge-md /path/to/letterhead.pdf "Document" ~/Desktop /path/to/document.md --strategy overlay
```

Available strategies:

- `darken`: **(Default)** Works well for light letterheads with dark text/logos
- `multiply`: Good for adding watermark-like elements
- `overlay`: Better visibility of both document and letterhead
- `transparency`: Smooth blending between elements
- `reverse`: Places letterhead on top of content
- `all`: Compare all strategies at once

### Multi-Page Letterhead Support

Mac-letterhead intelligently handles multi-page letterhead templates:

- **Single-page letterhead**: Applied to all document pages
- **Two-page letterhead**:
  - First page → First document page
  - Second page → All other document pages
- **Three-page letterhead**:
  - First page → First document page
  - Second page → Even-numbered pages
  - Third page → Odd-numbered pages

This is ideal for professional documents with customized headers/footers for various page positions.

## Logging and Troubleshooting

### Log Files
- **Application logs**: `~/Library/Logs/Mac-letterhead/letterhead.log`
- **Droplet logs**: `~/Library/Logs/Mac-letterhead/droplet.log`

### Common Commands
- **View version**: `uvx mac-letterhead --version`
- **Adjust log level**: `uvx mac-letterhead --log-level WARNING install /path/to/letterhead.pdf`
- **Development mode**: Use `--dev` flag for local testing

### Common Issues

#### WeasyPrint Library Issues
If you encounter WeasyPrint library errors, the system automatically falls back to ReportLab:
```
WARNING: WeasyPrint could not import some external libraries. Using ReportLab fallback.
```
This is normal and doesn't affect functionality.

#### Permission Issues
If droplets ask for file access permissions:
1. Check **System Preferences > Security & Privacy > Privacy > Files and Folders**
2. Allow access for the letterhead application
3. Test by double-clicking the droplet (shows info dialog)

#### Margin Detection Issues
The smart margin detection algorithm analyzes letterhead position automatically. If margins seem incorrect:
1. Ensure your letterhead PDF has clear visual elements (logos, text, graphics)
2. Check that letterhead elements are positioned in header or footer areas
3. For troubleshooting, contact support with sample letterhead file

## Use Cases

- **Corporate Communications**: Apply company letterhead to business documents
- **Legal Documents**: Add watermarks or legal disclaimers to contracts
- **Invoices & Statements**: Brand financial documents with your company logo and information
- **Proposals & Reports**: Create professional-looking documents from Markdown or PDF
- **Academic Papers**: Add university/institution letterhead to research papers
- **Documentation**: Convert Markdown documentation to letterhead-branded PDFs
- **Meeting Minutes**: Write in Markdown and automatically apply corporate styling

## Features

- **Easy Installation**: Simple `uvx` command installation and usage
- **Smart Letterhead Detection**: Intelligent position detection for optimal document layout
- **Multiple Letterhead Templates**: Support for various letterhead designs and positions
- **Advanced Multi-page Support**: Different letterhead designs for first page, even pages, and odd pages
- **Development Mode**: Local testing capabilities with `--dev` flag
- **Self-contained Applications**: Desktop droplets with embedded templates
- **High-quality Output**: PDF processing without quality loss
- **Original Metadata Preservation**: Maintains document properties and structure
- **Multiple Blend Modes**: Various merging strategies for different letterhead styles
- **Professional Markdown Support**: 
  - Intelligent margin detection and adjustment
  - Syntax highlighting for code blocks
  - Professional formatting for tables, lists, and headers
  - Support for complex document structures
- **Robust Architecture**:
  - Modular component design for better maintainability
  - Enhanced error handling and logging
  - uvx environment compatibility
  - Automatic fallback rendering
- **Cross-platform Compatibility**: Works across different macOS configurations

## License

MIT License
