# Mac-letterhead Technical Context

## Technologies Used

### Core Technologies

- **Python 3.11+**: Primary programming language with enhanced uvx support
- **PyMuPDF (fitz)**: PDF manipulation and intelligent letterhead analysis
- **Markdown**: Python Markdown parser with smart margin integration
- **WeasyPrint**: HTML/CSS to PDF converter (primary) with library path management
- **ReportLab**: PDF generation library (fallback) with consistent API
- **PyObjC**: Python to Objective-C bridge for macOS integration

### Supporting Technologies

- **HTML5lib**: HTML parsing for Markdown conversion
- **Pillow**: Image processing
- **uv**: Modern Python packaging, dependency management, and isolated execution
- **AppleScript**: macOS automation for droplet creation and execution
- **CSS3**: Advanced styling for professional document formatting

### Development Technologies

- **Modular Architecture**: Component-based design for better maintainability
- **Template System**: Context-aware script generation for different execution modes
- **Smart Analysis**: Geometric algorithms for letterhead position detection
- **Environment Detection**: Runtime adaptation to different execution contexts

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

- **Make**: Build automation with semantic versioning
- **uv**: Package management, virtual environments, and isolated execution
- **Git**: Version control with automated tagging
- **AppleScript Editor**: Template development and testing
- **Makefile**: Enhanced with development mode support and version management

### Testing Environment

- **Multiple Python Versions**: 3.11, 3.12, 3.13 support
- **Dual Testing Modes**: Separate environments for basic and full functionality
- **Development Mode Testing**: Local code testing with `--dev` flag
- **Production Testing**: uvx-based installation validation
- **Cross-Environment Validation**: Testing across isolated and system environments

## Technical Constraints

### Platform Constraints

- **Primary Platform**: macOS (for desktop application and AppleScript integration)
- **Secondary Platforms**: Any platform supporting Python 3.11+ (for CLI functionality)
- **Architecture Support**: Intel and Apple Silicon Macs

### Dependency Constraints

- **Self-contained**: Minimize external dependencies with smart fallbacks
- **uvx Compatibility**: Full support for isolated uvx environments
- **Optional Dependencies**: WeasyPrint and system libraries are optional
- **Library Path Management**: Internal configuration for WeasyPrint in isolated environments
- **Compatibility**: Support for Python 3.11+ with enhanced environment detection

### Performance Constraints

- **Memory Usage**: Efficient handling of large PDF files with smart analysis
- **Processing Speed**: Quick merging with intelligent letterhead detection
- **Algorithmic Efficiency**: ~82% usable page width regardless of letterhead complexity
- **Resource Management**: Optimized file operations and template processing

## Dependencies

### Core Dependencies (v0.9.5)

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
weasyprint==65.0
```

### WeasyPrint Dependencies (Included)

```
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
- **Installation**: `brew install pango cairo fontconfig freetype harfbuzz`

### Development Dependencies

- **uv**: Package management and virtual environments
- **make**: Build automation and testing
- **AppleScript**: macOS integration and droplet creation

## Installation Methods

### Standard Installation (All Features)

```bash
uvx mac-letterhead
```

### System Dependencies Installation

```bash
brew install pango cairo fontconfig freetype harfbuzz
```

### Development Installation

```bash
git clone <repository-url>
cd Mac-letterhead
uv venv
uv pip install -e "."
```

### Droplet Creation

```bash
# Production droplet
uvx mac-letterhead install /path/to/letterhead.pdf --name "Company Letterhead"

# Development droplet  
uvx mac-letterhead install /path/to/letterhead.pdf --name "Dev Test" --dev
```

## Tool Usage Patterns

### Enhanced Makefile (v0.9.5)

The project uses an advanced Makefile for development and release management:

- **test**: Run comprehensive tests with margin analysis
- **test-dev**: Test development mode droplet creation
- **test-all**: Full test suite including edge cases
- **clean**: Clean build artifacts and test files
- **install-dev**: Create development mode droplet for testing
- **bump-patch/minor/major**: Semantic version management
- **tag-release**: Git tagging with version validation
- **publish**: PyPI publication with automated checks

### Testing Strategy

- **Smart Margin Testing**: Real letterhead analysis with before/after comparisons
- **Development Mode Testing**: Local code testing with `--dev` flag
- **Production Testing**: uvx installation validation
- **Cross-Environment Testing**: Isolated and system environment validation
- **Component Testing**: Individual module testing for better debugging

### Version Management

- **Semantic Versioning**: Automated patch, minor, and major version bumps
- **Single Source of Truth**: Version in Makefile propagated to all files
- **Git Integration**: Automated tagging and release notes
- **Validation**: Pre-release checks and testing

### Continuous Integration

- **GitHub Actions**: Automated testing and publishing pipeline
- **Multi-environment Testing**: Validation across different Python and macOS versions
- **Release Automation**: Tag-triggered PyPI publication
- **Quality Gates**: Testing and validation before release

## Development Workflow

1. **Setup**: Clone repository and install dependencies
   ```bash
   git clone <repository-url>
   cd Mac-letterhead
   uv venv
   uv pip install -e "."
   ```

2. **Development**: Make changes and run comprehensive tests
   ```bash
   # Run full test suite with margin analysis
   make test
   
   # Test development mode droplet creation
   make test-dev
   ```

3. **Local Testing**: Create and test development droplets
   ```bash
   # Create development mode droplet for testing
   make install-dev
   
   # Test with real letterhead files
   # Drag and drop documents onto created droplet
   ```

4. **Version Management**: Update version with semantic versioning
   ```bash
   # Patch version (bug fixes)
   make bump-patch
   
   # Minor version (new features)
   make bump-minor
   
   # Major version (breaking changes)
   make bump-major
   ```

5. **Release**: Tag and publish to PyPI
   ```bash
   # Create git tag and push
   make tag-release
   
   # Publish to PyPI (triggered by tag)
   make publish
   ```

### Enhanced Development Features

- **Component Testing**: Test individual installation modules
- **Smart Analysis Testing**: Validate margin detection algorithms
- **Cross-mode Testing**: Verify both development and production modes
- **Real-world Validation**: Test with actual letterhead designs
- **Environment Compatibility**: Validate uvx and system environments

## Technical Debt and Considerations

### Resolved in v0.9.x

- **✅ WeasyPrint Environment Issues**: Fixed library path management in uvx isolated environments
- **✅ Margin Detection Problems**: Resolved critical bugs in letterhead position analysis
- **✅ Monolithic Architecture**: Replaced with modular, testable component design
- **✅ Development Workflow**: Enhanced local testing and debugging capabilities

### Current Considerations

- **Cross-Platform Expansion**: Desktop application currently macOS-only
- **Performance Optimization**: Opportunity for large document processing improvements
- **Advanced Features**: Complex letterhead layouts and batch processing
- **User Experience**: Feedback collection and workflow optimization

### Future Technical Challenges

- **Windows/Linux Support**: Adapting droplet functionality for other platforms
- **Web Integration**: Browser-based processing capabilities
- **API Development**: RESTful services for integration
- **Machine Learning**: Advanced letterhead analysis and optimization

### Maintenance Areas

- **Documentation**: Comprehensive guides and troubleshooting resources
- **Testing Coverage**: Continued expansion of test scenarios and edge cases
- **Performance Monitoring**: Benchmarking and optimization opportunities
- **User Feedback Integration**: Real-world usage insights and improvements
