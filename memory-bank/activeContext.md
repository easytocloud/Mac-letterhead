# Mac-letterhead Active Context

## Current Work Focus

The current focus is on finalizing the Markdown processing functionality with a tiered approach:

1. **Primary Renderer**: WeasyPrint for high-quality PDF generation
2. **Fallback Renderer**: ReportLab for environments where WeasyPrint cannot be installed

This approach allows users to choose between:
- A basic installation with PDF-only functionality
- A full installation with both PDF and Markdown support

## Recent Changes

### Version 0.8.0 Updates

1. **Tiered Installation Approach**
   - Moved Markdown-related dependencies to an optional dependency group
   - Added WeasyPrint 65.0 as a dependency in the markdown group
   - Added all required WeasyPrint dependencies to the markdown group
   - Kept core PDF functionality dependencies in the main dependencies

2. **Enhanced Testing in Makefile**
   - Added separate test targets for basic and full installations
   - Added a dedicated test target for WeasyPrint testing
   - Updated the test-all target to run basic, full, and WeasyPrint tests
   - Updated the clean target to clean up all virtual environments
   - Fixed issues with the Markdown module import in test environments
   - Added --output option to test targets to avoid save dialog
   - Created a simple test Markdown file for Markdown testing
   - Created a test PDF document for basic PDF testing

3. **Code Improvements**
   - Updated error messages to reflect the new installation instructions
   - Fixed version inconsistencies in uv.lock file
   - Updated warning message in markdown_processor.py to reference the correct version
   - Modified main.py to dynamically add site-packages directory to Python path
   - Added PYTHONPATH environment variable setting in Makefile for Markdown tests
   - Restructured markdown_processor.py to always import ReportLab dependencies
   - Added DYLD_LIBRARY_PATH environment variable for WeasyPrint system libraries

## Next Steps

1. **Testing**
   - Comprehensive testing of both basic and full installations
   - Testing across all supported Python versions (3.11, 3.12, 3.13)
   - Verify proper fallback to ReportLab when WeasyPrint is not available
   - Fix compatibility issues with Python 3.12 and 3.13 (PyObjC circular import)

2. **Documentation**
   - Update README with clear installation instructions for both basic and full installations
   - Document the tiered approach and its benefits
   - Provide troubleshooting guidance for WeasyPrint installation issues

3. **Release**
   - Finalize version 0.8.0
   - Publish to PyPI
   - Create GitHub release with detailed release notes

4. **Future Enhancements**
   - Improve WeasyPrint CSS styling for better Markdown rendering
   - Add more merging strategies for different letterhead types
   - Consider cross-platform desktop application support

## Active Decisions and Considerations

### 1. Tiered Installation Approach

**Decision**: Implement a tiered installation approach with optional Markdown support.

**Rationale**:
- WeasyPrint has complex dependencies that can be challenging to install
- Many users only need the PDF merging functionality
- This approach provides flexibility while maintaining all features for those who need them

**Implementation**:
- Core package: PDF functionality only
- Optional extras: Markdown support with WeasyPrint

### 2. Dual Rendering Engines

**Decision**: Support both WeasyPrint and ReportLab for Markdown rendering.

**Rationale**:
- WeasyPrint provides superior rendering quality
- ReportLab is more widely compatible and has fewer dependencies
- Runtime detection allows for graceful fallback

**Implementation**:
- Check for WeasyPrint availability at runtime
- Use WeasyPrint if available, fall back to ReportLab if not
- Provide clear warning when using fallback renderer
- Document system dependencies required for WeasyPrint:
  ```
  brew install pango cairo fontconfig freetype harfbuzz
  ```

### 3. Testing Strategy

**Decision**: Implement separate testing environments for basic and full functionality.

**Rationale**:
- Ensures both installation types work correctly
- Prevents issues where full functionality tests pass but basic functionality is broken
- Simulates real-world usage scenarios

**Implementation**:
- test-basic target for PDF-only functionality
- test-full target for PDF + Markdown functionality
- test-all target to run both test suites
- Use PYTHONPATH environment variable to ensure Markdown module is found

### 4. Python Path Management

**Decision**: Dynamically manage Python path to ensure optional modules are found.

**Rationale**:
- Virtual environments can have different site-packages locations
- Optional dependencies may be installed in different locations
- Runtime path management ensures modules are found regardless of installation method

**Implementation**:
- Add site-packages directory to sys.path at runtime
- Use PYTHONPATH environment variable in test scripts
- Print detailed import error messages for troubleshooting

## Important Patterns and Preferences

### Code Organization

- **Modular Design**: Keep functionality in separate modules with clear responsibilities
- **Clear Interfaces**: Well-defined interfaces between components
- **Feature Detection**: Runtime detection of available libraries
- **Graceful Degradation**: Fallback to simpler implementations when advanced features are unavailable

### Development Workflow

- **Version Management**: Single source of truth for version in Makefile
- **Automated Testing**: Test both basic and full functionality across multiple Python versions
- **Clean Build Process**: Automated cleaning of build artifacts
- **Continuous Integration**: GitHub Actions for automated testing and publishing

### Documentation Standards

- **Clear Installation Instructions**: Separate instructions for basic and full installations
- **Usage Examples**: Provide examples for all major use cases
- **Troubleshooting Guidance**: Help users resolve common issues
- **API Documentation**: Document all public APIs

## Learnings and Project Insights

1. **Dependency Management**
   - Complex dependencies can be a barrier to adoption
   - Optional dependencies provide flexibility
   - Runtime feature detection allows for graceful fallback
   - Python path management is crucial for finding optional modules

2. **PDF Processing**
   - PyMuPDF provides powerful PDF manipulation capabilities
   - Letterhead detection requires careful analysis of page regions
   - Different merging strategies are needed for different letterhead designs

3. **Markdown Processing**
   - WeasyPrint provides superior rendering quality but has complex dependencies
   - ReportLab is more widely compatible but requires more custom code
   - HTML parsing and conversion requires careful handling of different element types

4. **Testing Complexity**
   - Testing with different Python versions reveals compatibility issues
   - Separate testing environments for different feature sets ensure comprehensive coverage
   - Automated test file generation simplifies testing setup
   - Environment variables can help manage Python path issues
