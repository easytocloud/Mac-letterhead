# Mac-letterhead Active Context

## Current Work Focus

The project has achieved enhanced production-ready status with version 0.9.6, featuring complete architectural restructuring and improved component separation. Current focus areas include:

1. **Component Separation**: Complete modular restructuring for better troubleshooting
2. **Enhanced Resource Management**: Improved CSS support and bundled resource handling  
3. **Development Workflow**: Advanced local testing with development droplets
4. **Semantic Versioning**: Single source of truth version management in Makefile

## Recent Changes

### Version 0.9.6 Final CSS Architecture Implementation

**COMPLETED**: Clean CSS Architecture with Cross-Environment Compatibility

#### 1. **CSS Loading System Redesign**
   - **Problem Resolved**: Eliminated hardcoded CSS from Python code as requested
   - **Clean Architecture**: Implemented proper CSS cascade order:
     1. `defaults.css` (from package) - comprehensive baseline styling
     2. `custom.css` (optional, if provided) - user customizations  
     3. **Only hardcoded page margins** - smart letterhead margins with `!important`
   - **Resource Loading Fix**: Replaced deprecated `pkg_resources` with modern `importlib.resources` + fallbacks
   - **Cross-Environment Support**: Multiple fallback mechanisms for Python 3.9+ compatibility

#### 2. **AppleScript CSS Integration**
   - **Template Enhancement**: Development and production templates now properly detect bundled CSS
   - **Automatic CSS Passing**: Droplets automatically include `--css` parameter for merge-md commands
   - **Smart CSS Filtering**: @page rules automatically removed from custom CSS to preserve smart margins
   - **Variable Substitution Fix**: Resolved "python_path is not defined" errors in development templates

#### 3. **Validated Complete Workflow**
   - **Development Droplet**: Successfully created with custom stationery (~/Stationery/easy.pdf + easy.css)
   - **CSS Customization**: Color and styling changes properly applied while preserving letterhead margins
   - **Smart Margin Preservation**: Letterhead printable areas honored despite custom CSS
   - **Cross-Environment Testing**: Works in both development and uvx production environments

### Version 0.9.6 Complete Project Restructuring

**Major Architectural Overhaul Completed**: The entire installation system has been completely restructured into discrete, specialized modules for better maintainability and troubleshooting capabilities.

#### 1. **Complete Installation System Restructuring**
   - **New Modular Structure**: Created `letterhead_pdf/installation/` directory with specialized modules:
     - `droplet_builder.py`: Core droplet creation orchestration
     - `resource_manager.py`: Stationery files and resource bundling
     - `applescript_generator.py`: Template processing and AppleScript generation  
     - `macos_integration.py`: Platform-specific macOS operations
     - `validator.py`: Input validation and error handling
   - **Enhanced Separation**: Each component has single responsibility for better troubleshooting
   - **Template System**: Separate production and development AppleScript templates
   - **Resource Bundling**: Improved handling of icons, CSS, and letterhead files

#### 2. **Enhanced CSS Support for Markdown Processing**
   - **Bundled CSS**: Default `defaults.css` file included in package resources
   - **Custom CSS Support**: 
     - Install command: `--css` parameter for custom CSS files
     - CLI command: `merge-md --css` parameter for custom styling
     - Droplet bundling: CSS files included in app bundle resources
   - **AppleScript Integration**: Droplets automatically pass bundled CSS to merge-md commands
   - **Fallback Mechanism**: Automatic fallback to minimal CSS if custom CSS unavailable

#### 3. **Improved Development Workflow**
   - **Local Test Droplets**: Enhanced `make test-dev-droplet` for local development testing
   - **Development vs Production**: Clear separation between development and production droplet modes
   - **Template Flexibility**: AppleScript generator supports both embedded templates and legacy fallbacks
   - **Better Error Handling**: Enhanced error reporting and diagnostic capabilities

#### 4. **Enhanced Semantic Versioning**
   - **Makefile Version Management**: Single source of truth for version numbers
   - **Automatic Updates**: Version synchronization across all project files
   - **Development Testing**: Local droplets use current development version
   - **Production Consistency**: uvx installations use tagged production versions

### Previous Version 0.9.5 Achievements

1. **Complete Architecture Overhaul**
   - Created modular installation system (`letterhead_pdf/installation/`)
   - Separated components: droplet_builder, resource_manager, applescript_generator, macos_integration, validator
   - Enhanced component isolation for better troubleshooting and maintenance
   - Replaced monolithic installer with clean, testable modules

2. **Smart Margin Detection Algorithm**
   - **Critical Bug Fix**: Fixed margin calculation for right-positioned letterheads
   - **Intelligent Position Detection**: Automatically detects left/right/center letterhead positioning
   - **Adaptive Margins**: 
     - Left-positioned: Wider left margin (72pts), minimal right margin (36pts)
     - Right-positioned: Minimal left margin (36pts), wider right margin (72pts)
     - Center-positioned: Symmetric margins for balanced layout
   - **Optimal Layout**: Provides ~82% usable page width regardless of letterhead design
   - **Before/After**: Fixed easy.pdf from -52.4% unusable to +81.8% usable page width

3. **Enhanced Development & Testing**
   - **Development Mode**: `--dev` flag creates local test droplets using development code
   - **Production vs Development Templates**: Separated AppleScript templates for different use cases
   - **Enhanced Debugging**: Better error handling and diagnostic capabilities
   - **Semantic Versioning**: Improved Makefile with single source of truth for versions

4. **uvx Environment Compatibility**
   - **Library Path Fixes**: Resolved WeasyPrint library path issues in isolated uvx environments
   - **Environment Detection**: Better handling of different Python execution contexts
   - **Fallback Mechanisms**: Improved ReportLab fallback when WeasyPrint unavailable
   - **Cross-Environment Testing**: Validated functionality across development and production environments

## Next Steps

1. **Performance Optimization**
   - **Large Document Handling**: Optimize processing for large PDF files
   - **Memory Management**: Improve resource utilization during processing
   - **Caching**: Implement smart caching for frequently used letterheads
   - **Parallel Processing**: Multi-threaded document processing capabilities

2. **Cross-Platform Expansion**
   - **Windows Support**: Adapt droplet functionality for Windows platforms
   - **Linux Support**: Create Linux-compatible desktop applications
   - **Web Interface**: Browser-based document processing capabilities
   - **API Development**: RESTful API for integration with other systems

3. **Advanced Features**
   - **Complex Letterhead Support**: Multi-region letterhead layouts
   - **Batch Processing**: Multiple document processing workflows
   - **Preview Functionality**: Live preview before merging
   - **Custom CSS Support**: User-defined styling for Markdown processing

4. **Enhanced User Experience**
   - **Real-world Testing**: Gather feedback from production users
   - **Usability Improvements**: Streamline common workflows
   - **Error Recovery**: Better handling of edge cases and errors
   - **Documentation Expansion**: More comprehensive user guides and examples

## Active Decisions and Considerations

### 1. Smart Margin Detection Algorithm

**Decision**: Implement intelligent letterhead position detection with adaptive margins.

**Rationale**:
- Previous algorithm incorrectly used header position as margins, causing unusable layouts
- Different letterhead designs require different margin strategies
- Users need consistent, professional document layout regardless of letterhead style

**Implementation**:
- Analyze letterhead position using page center thresholds
- Left-positioned: Wider left margin to avoid logo, minimal right margin
- Right-positioned: Minimal left margin, wider right margin to avoid logo
- Center-positioned: Symmetric margins for balanced appearance
- Provide ~82% usable page width across all letterhead designs

### 2. Modular Architecture Design

**Decision**: Complete restructuring of installation system into discrete, testable modules.

**Rationale**:
- Monolithic installer was difficult to debug and maintain
- Better component separation enables targeted troubleshooting
- Modular design supports different deployment scenarios (development vs production)

**Implementation**:
- `droplet_builder.py`: Core droplet creation logic
- `resource_manager.py`: File and resource handling
- `applescript_generator.py`: Template processing and customization
- `macos_integration.py`: Platform-specific operations
- `validator.py`: Input validation and error handling
- Separate production/development AppleScript templates

### 3. Development vs Production Modes

**Decision**: Support both local development testing and production installations.

**Rationale**:
- Developers need to test changes without affecting production installations
- Different deployment scenarios require different configurations
- Enhanced debugging capabilities improve development workflow

**Implementation**:
- `--dev` flag creates droplets using local development code
- Production mode uses uvx-installed packages
- Separate template files for different execution contexts
- Enhanced logging and diagnostic capabilities in development mode

### 4. uvx Environment Compatibility

**Decision**: Ensure robust operation in uvx isolated environments.

**Rationale**:
- uvx provides user-friendly installation but creates isolated environments
- Library path issues can prevent WeasyPrint from functioning
- Need reliable fallback mechanisms for different system configurations

**Implementation**:
- Internal library path configuration before WeasyPrint imports
- Enhanced environment detection and adaptation
- Improved error handling and fallback to ReportLab
- Clear documentation of system dependencies and troubleshooting steps

## Important Patterns and Preferences

### Architecture Principles

- **Modular Design**: Discrete, testable components with single responsibilities
- **Clear Separation**: Distinct boundaries between installation, processing, and UI logic
- **Smart Defaults**: Intelligent behavior that works well without configuration
- **Graceful Degradation**: Robust fallback mechanisms for different environments

### Algorithm Design

- **Position-Aware Processing**: Letterhead analysis drives margin calculation
- **Adaptive Behavior**: Different strategies for different letterhead types
- **Data-Driven Decisions**: Threshold-based detection using geometric analysis
- **Optimization Focus**: Maximize usable content area while avoiding letterhead overlap

### Development Standards

- **Local Testing**: Development mode for safe testing without affecting production
- **Component Isolation**: Each module can be tested and debugged independently
- **Enhanced Diagnostics**: Comprehensive logging and error reporting
- **Version Consistency**: Single source of truth for version management

### User Experience Principles

- **Invisible Intelligence**: Smart behavior that doesn't require user configuration
- **Consistent Results**: Reliable, professional output regardless of letterhead design
- **Clear Feedback**: Informative messages and troubleshooting guidance
- **Flexible Installation**: Support for both simple and advanced use cases

## Learnings and Project Insights

1. **Smart Algorithm Development**
   - **Geometric Analysis**: Using page center thresholds enables reliable letterhead position detection
   - **Adaptive Strategies**: Different letterhead positions require completely different margin approaches
   - **User Impact**: Algorithm improvements can transform unusable layouts (-52% page width) into excellent ones (+82% page width)
   - **Testing Critical**: Real letterhead analysis revealed bugs that unit tests missed

2. **Architecture Evolution**
   - **Modular Benefits**: Component separation dramatically improves debugging and maintenance
   - **Development Workflow**: Local testing capabilities accelerate development and reduce deployment risks
   - **Template Separation**: Different execution contexts (dev vs prod) require different configurations
   - **Error Isolation**: Better component boundaries enable targeted troubleshooting

3. **Environment Compatibility**
   - **uvx Challenges**: Isolated environments can break library dependencies in unexpected ways
   - **Path Management**: Python library paths require careful handling in different execution contexts
   - **Fallback Strategies**: Multiple rendering engines provide resilience across system configurations
   - **Documentation Importance**: Clear troubleshooting guides reduce user friction

4. **Production Readiness**
   - **Real-world Testing**: Production usage reveals edge cases not found in development
   - **User Feedback**: Actual letterhead designs expose algorithm limitations and improvements
   - **Cross-environment Validation**: Development and production environments behave differently
   - **Semantic Versioning**: Clear version management enables confident releases and rollbacks

5. **User Experience Design**
   - **Invisible Intelligence**: Best algorithms work without user configuration or awareness
   - **Consistent Behavior**: Users expect reliable results regardless of letterhead complexity
   - **Error Recovery**: Graceful handling of edge cases maintains user confidence
   - **Documentation Quality**: Comprehensive guides reduce support burden and improve adoption
