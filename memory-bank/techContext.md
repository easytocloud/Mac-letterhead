# Mac-letterhead Technical Context

## Technologies Used

### Core Technologies

- **Python 3.11+**: Primary programming language
- **PyMuPDF (fitz)**: PDF manipulation library
- **Markdown**: Python Markdown parser
- **WeasyPrint**: HTML/CSS to PDF converter (primary)
- **ReportLab**: PDF generation library (fallback)
- **PyObjC**: Python to Objective-C bridge for macOS integration

### Supporting Technologies

- **HTML5lib**: HTML parsing for Markdown conversion
- **Pillow**: Image processing
- **uv**: Modern Python packaging and dependency management

## Development Setup

### Environment Requirements

- **Python**: Version 3.11 or higher
- **macOS**: For full functionality including desktop application
- **Optional Dependencies**: For WeasyPrint functionality
  - Pango
  - Cairo
  - GDK-PixBuf
  - Harfbuzz

### Development Tools

- **Make**: Build automation
- **uv**: Package management and virtual environments
- **Git**: Version control

### Testing Environment

- Multiple Python versions (3.11, 3.12, 3.13)
- Separate test environments for basic and full functionality

## Technical Constraints

### Platform Constraints

- **Primary Platform**: macOS (for desktop application)
- **Secondary Platforms**: Any platform supporting Python 3.11+ (for CLI functionality)

### Dependency Constraints

- **Self-contained**: Minimize external dependencies
- **Optional Dependencies**: WeasyPrint and its dependencies are optional
- **Compatibility**: Support for Python 3.11+ only

### Performance Constraints

- **Memory Usage**: Efficient handling of large PDF files
- **Processing Speed**: Quick merging for typical document sizes

## Dependencies

### Core Dependencies

```
html5lib==1.1
markdown==3.7
pillow==11.1.0
pymupdf==1.25.4
pyobjc-core==11.0
pyobjc-framework-cocoa==11.0
pyobjc-framework-quartz==11.0
reportlab==4.3.1
six==1.16.0
webencodings==0.5.1
```

### Optional Dependencies (Markdown Support)

```
weasyprint==65.0
cffi>=1.15.0
cssselect2>=0.7.0
fonttools>=4.38.0
pydyf>=0.5.0
pyphen>=0.13.0
tinycss2>=1.2.0
```

### System Dependencies (for WeasyPrint)

- **Pango**: Text layout and rendering
- **Cairo**: 2D graphics library
- **GDK-PixBuf**: Image loading library
- **Harfbuzz**: Text shaping engine

## Installation Methods

### Basic Installation (PDF Only)

```bash
uvx mac-letterhead
```

### Full Installation (PDF + Markdown)

```bash
uvx mac-letterhead[markdown]@0.8.0
```

## Tool Usage Patterns

### Makefile

The project uses a Makefile for common development tasks:

- **test-basic**: Test basic functionality (PDF only)
- **test-full**: Test full functionality (PDF + Markdown)
- **test-all**: Run all tests
- **clean**: Clean build artifacts
- **update-version**: Update version in all necessary files
- **publish**: Publish to PyPI

### Testing Strategy

- Separate test environments for basic and full functionality
- Testing across multiple Python versions
- Automated test file generation

### Version Management

- Single source of truth for version in Makefile
- Automated version propagation to all necessary files
- Semantic versioning

### Continuous Integration

- GitHub Actions for automated testing and publishing
- Version tagging triggers PyPI release

## Development Workflow

1. **Setup**: Clone repository and install dependencies
   ```bash
   git clone <repository-url>
   cd Mac-letterhead
   uv venv
   uv pip install -e ".[markdown]"
   ```

2. **Development**: Make changes and run tests
   ```bash
   # Run basic tests
   make test-basic
   
   # Run full tests
   make test-full
   ```

3. **Version Update**: Update version before release
   ```bash
   # Edit VERSION in Makefile
   make update-version
   ```

4. **Release**: Publish to PyPI
   ```bash
   make publish
   ```

## Technical Debt and Considerations

- **WeasyPrint Dependencies**: Complex installation requirements for WeasyPrint
- **Platform Specificity**: Desktop application currently macOS-only
- **Testing Coverage**: Ensure comprehensive testing across all supported platforms
- **Documentation**: Keep documentation updated with new features and changes
