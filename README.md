# Mac-letterhead

![PyPI Version](https://img.shields.io/pypi/v/Mac-letterhead.svg)
![Build Status](https://github.com/easytocloud/Mac-letterhead/actions/workflows/publish.yml/badge.svg)
![License](https://img.shields.io/github/license/easytocloud/Mac-letterhead.svg)

<!-- GitHub can't render .icns files directly, so we use HTML to link the icon badge -->
<a href="https://pypi.org/project/Mac-letterhead/" title="Mac-letterhead on PyPI">
  <img src="https://raw.githubusercontent.com/easytocloud/Mac-letterhead/main/letterhead_pdf/resources/icon.png" width="128" height="128" alt="Mac-letterhead Logo" align="right" />
</a>

A macOS utility that automatically merges a letterhead template with PDF documents using a simple drag-and-drop interface. Apply corporate letterhead designs to your documents effortlessly.

## Usage

Mac-letterhead provides a simple and reliable way to apply letterhead to PDF documents using a drag-and-drop application.

### Creating the Letterhead Applier App

Simply install the letterhead PDF as a drag-and-drop application:

```bash
uvx mac-letterhead install /path/to/your/letterhead.pdf
```

This will create a droplet application on your Desktop. The application will be named based on your letterhead file (e.g., "Letterhead CompanyLogo").

You can customize the name and location:
```bash
uvx mac-letterhead install /path/to/your/letterhead.pdf --name "Company Letterhead" --output-dir "~/Documents"
```

### Using the Letterhead Applier App

1. Print your document to PDF (using the standard "Save as PDF..." option)
2. Drag and drop the PDF onto the Letterhead Applier app icon
3. The letterhead will be applied automatically
4. You'll be prompted to save the merged document

The application combines your letterhead and document in a way that preserves both document content and letterhead design.

### Multi-Page Letterhead Support

Mac-letterhead now intelligently handles multi-page letterhead templates:

- **Single-page letterhead**: Applied to all pages of the document
- **Two-page letterhead**: 
  - First page applied to the first page of your document
  - Second page applied to all other pages of your document
- **Three-page letterhead**:
  - First page applied to the first page of your document
  - Second page applied to all even-numbered pages (except the first if it's even)
  - Third page applied to all odd-numbered pages (except the first if it's odd)

This is particularly useful for creating documents with different header/footer designs for first pages, even pages, and odd pages, matching professional print standards.

### Using Different Merge Strategies

If you already know which strategy works best for your letterhead, you can specify it directly:

```bash
uvx mac-letterhead merge /path/to/your/letterhead.pdf "Document Name" "/path/to/save" /path/to/document.pdf --strategy overlay
```

Available strategies:

- `multiply`: Original strategy using multiply blend mode
- `reverse`: Draws content first, then letterhead on top with blend mode
- `overlay`: Uses overlay blend mode for better visibility
- `transparency`: Uses transparency layers for better blending
- `darken`: **(Default)** Uses darken blend mode which works well for light letterheads with dark text/logos
- `all`: Generates files using all strategies for comparison (the main output file will use the darken strategy)

### Version Information

To check the current version:
```bash
uvx mac-letterhead --version
```

### Error Logging

The tool logs all operations and errors to:
```
~/Library/Logs/Mac-letterhead/letterhead.log
```

If you encounter any issues while using the tool, check this log file for detailed error messages and stack traces.

## Features

- Easy installation of letterhead services
- Supports multiple letterhead templates
- **Advanced multi-page letterhead support** for different first/even/odd page designs
- Self-contained application bundles with embedded letterhead templates
- No temporary file extraction - letterheads are used directly from the app bundle
- Maintains original PDF metadata
- Preserves PDF quality
- Shows save dialog for output location
- Proper error handling with detailed logging
- Supports standard versioning with --version flag
- Comprehensive blend modes for different letterhead styles
- Integration with macOS application design standards
- Type hints for better code maintainability

## Troubleshooting

If you encounter any issues:

1. Check the log file at `~/Library/Logs/Mac-letterhead/letterhead.log`
2. The log contains detailed information about:
   - All operations performed
   - Error messages with stack traces
   - Input/output file paths
   - PDF processing steps

## License

MIT License
