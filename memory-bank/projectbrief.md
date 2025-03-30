# Mac-letterhead Project Brief

## Project Overview

Mac-letterhead is a Python module that provides a drag-and-drop interface for merging letterhead templates with PDF and Markdown documents. The letterhead is applied 'under' the content, as if the document was printed on company stationery.

## Core Features

- **Drag & Drop Interface**: Easy document processing through a desktop application
- **Multiple Input Formats**: Support for both PDF and Markdown input files
- **Smart Letterhead Space Detection**: Avoids content overlap (particularly for Markdown)
- **Multiple Merging Strategies**: Options like darken, multiply, overlay, etc.
- **Multi-page Letterhead Support**: Different designs for first/subsequent pages

## Usage Modes

1. **Install Mode**:
   ```
   uvx mac-letterhead install /path/to/letterhead.pdf
   ```
   Creates a desktop application for drag-and-drop document processing

2. **Direct Merge Mode**:
   - For PDF files:
     ```
     uvx mac-letterhead merge /path/to/letterhead.pdf "Title" output_dir input.pdf
     ```
   - For Markdown files:
     ```
     uvx mac-letterhead merge-md /path/to/letterhead.pdf "Title" output_dir input.md
     ```

## Current Status

- PDF merging functionality is fully implemented and working
- Markdown processing is implemented with two rendering options:
  - WeasyPrint (preferred, high-quality output)
  - ReportLab (fallback when WeasyPrint is not available)
- Smart margin detection for letterhead content is implemented
- Multiple merging strategies are implemented
- Professional document formatting with proper spacing is in place

## Development Guidelines

- Keep the package 'self-contained' - rely only on components in the package
- Avoid dependencies on external software packages (Python or Brew)
- Use the Makefile in the project root for testing and publishing
- Avoid making changes to tests/utils unless explicitly requested

## Version Information

Current version: 0.8.0

The package now uses a tiered installation approach:
- Basic installation: Core PDF functionality only
- Full installation: PDF + Markdown functionality with WeasyPrint
