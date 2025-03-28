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

### Prerequisites

You should have the python uv package manager installed (when not: `pip install uv`).

## Quick Start

### 1. Create a Letterhead Application

Turn your letterhead PDF into a drag-and-drop application:

```bash
uvx mac-letterhead install /path/to/your/letterhead.pdf
```

This creates a desktop application named based on your letterhead file.

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

### Markdown Features (New in v0.6.0)

Mac-letterhead now provides intelligent Markdown-to-PDF conversion with letterhead support:

- **Smart Space Detection**: Automatically analyzes letterhead PDFs to find safe areas for content
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

## Advanced Options

### Custom Application Name and Location

```bash
uvx mac-letterhead install /path/to/letterhead.pdf --name "Company Letterhead" --output-dir "~/Documents"
```

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

- Check logs at: `~/Library/Logs/Mac-letterhead/letterhead.log`
- Adjust log level: `uvx mac-letterhead --log-level WARNING install /path/to/letterhead.pdf`
- View version: `uvx mac-letterhead --version`

## Use Cases

- **Corporate Communications**: Apply company letterhead to business documents
- **Legal Documents**: Add watermarks or legal disclaimers to contracts
- **Invoices & Statements**: Brand financial documents with your company logo and information
- **Proposals & Reports**: Create professional-looking documents from Markdown or PDF
- **Academic Papers**: Add university/institution letterhead to research papers
- **Documentation**: Convert Markdown documentation to letterhead-branded PDFs
- **Meeting Minutes**: Write in Markdown and automatically apply corporate styling

## Features

- Easy installation and usage
- Multiple letterhead templates support
- Advanced multi-page letterhead handling for different page designs
- Self-contained application bundles with embedded templates
- Direct template usage with no temporary file extraction
- Original PDF metadata preservation
- High-quality PDF output
- Customizable output location
- Detailed error handling and logging
- Multiple blend modes for different letterhead styles
- Markdown to PDF conversion with proper margins
- Smart letterhead space detection
- Professional document formatting
- Support for tables, code blocks, and footnotes

## License

MIT License
