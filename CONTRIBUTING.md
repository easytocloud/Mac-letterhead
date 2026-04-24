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
│   ├── markdown_processor.py # Backwards-compat shim → re-exports from markdown/
│   ├── markdown/           # Markdown-to-PDF pipeline (modular)
│   │   ├── processor.py    # MarkdownProcessor orchestrator, capability flags
│   │   ├── pdf_analyzer.py # Letterhead margin analysis
│   │   ├── html_cleaner.py # HTML preprocessing for ReportLab
│   │   ├── flowable_builder.py # ReportLab flowable construction
│   │   └── backends/       # PDF rendering backends
│   │       ├── weasyprint_backend.py
│   │       └── reportlab_backend.py
│   ├── pdf_utils.py        # Low-level PDF operations
│   ├── mcp_server.py       # MCP server for AI tool integration
│   ├── installation/       # Droplet creation system
│   └── resources/          # Default CSS, icons, and assets
├── tests/                  # Unit tests
│   ├── test_security.py    # Security regression tests
│   ├── test_gfm_features.py
│   └── test_list_rendering.py
├── tools/                  # Development utilities
├── test-input/             # Test input files (user-managed)
├── test-output/            # Generated test outputs
└── Makefile               # Development and testing commands
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
# Unit tests
make test-unit              # Unit tests with default Python version
make test-unit-py3.11       # Unit tests with specific Python version
make test-all-unit          # Unit tests across Python 3.10, 3.11, 3.12

# Rendering tests (document generation validation)
make rendering-reportlab-basic      # Basic ReportLab rendering
make rendering-reportlab-enhanced   # Enhanced ReportLab with full features
make rendering-weasyprint           # WeasyPrint rendering (requires system deps)
make rendering-backend-matrix       # All backend/markdown combinations
make test-all-rendering             # All rendering tests

# Direct pytest run (fastest for development)
uv run --with pytest pytest tests/ -v
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
- **`letterhead_pdf/markdown/processor.py`**: `MarkdownProcessor` orchestrator — backend selection, WeasyPrint→ReportLab fallback, capability flags
- **`letterhead_pdf/markdown/pdf_analyzer.py`**: Letterhead margin analysis (`analyze_letterhead`, `analyze_page_regions`)
- **`letterhead_pdf/markdown/html_cleaner.py`**: HTML preprocessing for ReportLab
- **`letterhead_pdf/markdown/flowable_builder.py`**: ReportLab flowable construction and list parsing
- **`letterhead_pdf/markdown/backends/`**: WeasyPrint and ReportLab rendering backends
- **`letterhead_pdf/markdown_processor.py`**: Backwards-compatibility shim — do not add logic here
- **`letterhead_pdf/pdf_utils.py`**: Low-level PDF operations using macOS Quartz
- **`letterhead_pdf/mcp_server.py`**: MCP server for AI tool integration, dynamic tool schemas
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

#### Testing MCP Server
```bash
# Set up letterhead directory for testing
mkdir -p ~/.letterhead
cp test-input/sample.pdf ~/.letterhead/test.pdf

# Test generic MCP server (style specified per tool call)
uvx mac-letterhead mcp &
# Server runs in background - use Claude or MCP client to test

# Test style-specific MCP server  
uvx mac-letterhead mcp --style test --output-dir ~/Desktop/mcp-test &

# Kill server when done testing
pkill -f "mac-letterhead mcp"
```

**MCP Development Notes**:
- Tools dynamically adapt schemas based on server configuration
- Generic servers require `style` parameter in tool calls
- Style-specific servers pre-configure letterhead and CSS resolution
- Test both configuration modes when making changes to MCP functionality

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

Releases are automated via [semantic-release](https://semantic-release.gitbook.io/) and GitHub Actions:

1. Merge Conventional Commit messages to `main` (e.g. `feat:`, `fix:`, `chore:`)
2. GitHub Actions detects the commit type, bumps the version, updates `CHANGELOG.md` and `letterhead_pdf/__init__.py`, and publishes to PyPI
3. No manual tagging required — the version is inferred from commit prefixes

**Local preview** (without publishing):
```bash
make release-dry-run
```

## Getting Help

- **Issues**: Check existing GitHub issues or create a new one
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Questions**: Feel free to ask in your pull request

Thank you for contributing to Mac-letterhead!