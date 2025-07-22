# Contributing to Mac-letterhead

We welcome contributions to Mac-letterhead! This guide will help you set up your development environment and understand the workflow for contributing to the project.

## Development Setup

The best way to contribute is to clone the repository and work directly on the code:

```bash
# Clone the repository
git clone https://github.com/easytocloud/Mac-letterhead.git
cd Mac-letterhead

# Install for local development
make dev-install
```

This installs the package in development mode, allowing you to make changes to the code in `letterhead_pdf/` and see them reflected immediately.

## Project Structure

```
Mac-letterhead/
├── letterhead_pdf/          # Main package code
│   ├── main.py             # CLI interface and command handlers
│   ├── pdf_merger.py       # Core PDF merging functionality  
│   ├── markdown_processor.py # Markdown to PDF conversion
│   ├── pdf_utils.py        # Low-level PDF operations
│   ├── installation/       # Droplet creation system
│   └── resources/          # Default CSS, icons, and assets
├── tools/                  # Development utilities
├── test-input/            # Test input files (user-managed)
├── test-output/           # Generated test outputs
└── Makefile              # Development and testing commands
```

## Testing Your Changes

Mac-letterhead includes comprehensive testing across multiple Python versions. Always run the full test suite to verify your changes work correctly:

```bash
# Test all functionality across all supported Python versions
make test-all
```

This runs tests for Python 3.10, 3.11, and 3.12 with different configurations:
- **Basic tests**: Core PDF merging functionality
- **Full tests**: Markdown processing with ReportLab
- **WeasyPrint tests**: Advanced Markdown rendering (requires system dependencies)

### Individual Test Commands

```bash
# Test specific Python version and configuration
make test-py3.10-basic      # Python 3.10 basic functionality
make test-py3.11-full       # Python 3.11 with Markdown support
make test-py3.12-weasyprint # Python 3.12 with WeasyPrint

# Test all versions with specific configuration
make test-basic             # Basic tests across all Python versions
make test-full              # Full tests across all Python versions  
make test-weasyprint        # WeasyPrint tests across all Python versions
```

### Test Input Files

Place test documents in the `test-input/` directory:
- `*.md` files for Markdown testing
- `*.pdf` files for PDF merging tests

Test outputs are automatically generated in `test-output/` with version-specific filenames like `document-py3.10-basic.pdf`.

## Development Mode Testing

Create development droplets to test your changes:

```bash
# Create a test droplet using your local development code
make dev-droplet
```

This creates a droplet on your desktop that uses your local code changes, allowing you to test the full workflow without installing the package.

## System Dependencies

For full testing capabilities, install the required system libraries:

```bash
# macOS with Homebrew
brew install pango cairo fontconfig freetype harfbuzz
```

These are required for WeasyPrint functionality and high-quality PDF generation.

## Making Changes

### Code Organization

- **`letterhead_pdf/main.py`**: CLI interface, argument parsing, command routing
- **`letterhead_pdf/pdf_merger.py`**: Core PDF blending and merging logic
- **`letterhead_pdf/markdown_processor.py`**: Markdown to PDF conversion with smart margins
- **`letterhead_pdf/pdf_utils.py`**: Low-level PDF operations using macOS Quartz
- **`letterhead_pdf/installation/`**: Droplet creation, AppleScript generation, macOS integration

### Development Guidelines

1. **Follow Existing Patterns**: Study the existing code structure and follow the same patterns
2. **Test Thoroughly**: Run `make test-all` to ensure your changes work across all configurations
3. **Document Changes**: Update relevant documentation for user-facing changes
4. **Preserve Compatibility**: Maintain backward compatibility with existing letterhead files and workflows

### Common Development Tasks

#### Testing New Features
```bash
# Add test files to test-input/
echo "# Test Document" > test-input/my-test.md

# Run tests to see your changes
make test-all

# Check outputs in test-output/
ls test-output/
```

#### Debugging Issues
```bash
# Create development droplet for manual testing
make dev-droplet

# Check logs for debugging information
tail -f ~/Library/Logs/Mac-letterhead/letterhead.log
```

#### Analyzing Letterhead Files
```bash
# Use the analysis tool to understand letterhead structure
python tools/analyze_letterhead.py letterhead.pdf analysis.pdf
```

## Pull Request Process

1. **Fork the Repository**: Create your own fork of Mac-letterhead
2. **Create a Feature Branch**: `git checkout -b feature/your-feature-name`
3. **Make Your Changes**: Edit code in the `letterhead_pdf/` directory
4. **Test Thoroughly**: Run `make test-all` to ensure everything works
5. **Commit Your Changes**: Use descriptive commit messages
6. **Push to Your Fork**: `git push origin feature/your-feature-name`
7. **Submit Pull Request**: Create a PR with a clear description of your changes

### Pull Request Guidelines

- **Clear Description**: Explain what your changes do and why they're needed
- **Test Results**: Include evidence that `make test-all` passes
- **Documentation Updates**: Update README.md or other docs if needed
- **Small, Focused Changes**: Keep PRs focused on a single feature or fix
- **Responsive to Feedback**: Be prepared to make adjustments based on review

## Development Utilities

The `tools/` directory contains helpful development utilities:

### Letterhead Analysis
```bash
# Analyze letterhead PDF structure and margins
python tools/analyze_letterhead.py input.pdf analysis.pdf
```

This creates a visual analysis showing detected content regions, printable areas, and margin calculations.

### Creating Test Letterheads
```bash
# Generate test letterhead PDFs
python tools/create_letterhead.py
```

### Parser Comparison
```bash
# Compare different PDF parsing approaches
python tools/test_parser_comparison.py
```

## Release Process

Releases are handled automatically via GitHub Actions when tags are pushed. The workflow:

1. Code changes are merged to `main`
2. Version is updated in `Makefile` and `letterhead_pdf/__init__.py`
3. Tag is created: `git tag v0.x.x`
4. Tag is pushed: `git push origin v0.x.x`
5. GitHub Actions builds and publishes to PyPI

## Getting Help

- **Issues**: Check existing GitHub issues or create a new one
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Questions**: Feel free to ask in your pull request

Thank you for contributing to Mac-letterhead!