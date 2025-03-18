# Mac-letterhead

A macOS utility that automatically merges a letterhead template with PDF documents using a simple drag-and-drop interface.

## Installation

Install the package:
```bash
uv pip install -e .
```

## Usage

Mac-letterhead provides a simple and reliable way to apply letterhead to PDF documents using an AppleScript droplet application.

### Creating the Letterhead Applier App

1. First, install the package:
   ```bash
   uv pip install .
   ```

2. Run the script to create your customized Letterhead App:
   ```bash
   ./scripts/create_letterhead_droplet.sh /path/to/your/letterhead.pdf
   ```
   
3. The application will be created on your Desktop by default. You can customize the name with:
   ```bash
   ./scripts/create_letterhead_droplet.sh --name "Company Letterhead" /path/to/your/letterhead.pdf
   ```

### Using the Letterhead Applier App

1. Print your document to PDF (using the standard "Save as PDF..." option)
2. Drag and drop the PDF onto the Letterhead Applier app icon
3. The letterhead will be applied automatically
4. You'll be prompted to save the merged document

The application combines your letterhead and document in a way that preserves both document content and letterhead design.

### Using Different Merge Strategies

If you already know which strategy works best for your letterhead, you can specify it directly:

```bash
uv run mac-letterhead print /path/to/your/letterhead.pdf "Document Name" "" /path/to/document.pdf --strategy overlay
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
uv run mac-letterhead --version
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
- Maintains original PDF metadata
- Preserves PDF quality
- Shows save dialog for output location
- Proper error handling with detailed logging
- Supports --version flag
- Type hints for better code maintainability

## Development

To install in development mode:
```bash
uv pip install -e .
```

### Publishing a New Release

#### First-time Setup

1. Create an account on PyPI if you don't have one
2. Create an API token on PyPI:
   - Go to https://pypi.org/manage/account/token/
   - Create a token with "Upload packages" scope
3. Add the token to GitHub repository secrets:
   - Go to your repository's Settings > Secrets and variables > Actions
   - Create a new secret named `PYPI_API_TOKEN`
   - Paste your PyPI token as the value

#### Publishing a Release

1. Update the version in:
   - pyproject.toml
   - letterhead_pdf/__init__.py
   - letterhead_pdf/main.py

2. Run the release script:
```bash
./tag_release.sh
```

This will:
- Create a git tag for the current version
- Push the tag to GitHub
- Trigger the GitHub workflow to publish to PyPI

The GitHub workflow will:
- Build the package
- Upload it to PyPI using the configured API token
- Make it available for installation via pip/uv

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
