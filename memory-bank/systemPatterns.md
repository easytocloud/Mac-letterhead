# Mac-letterhead System Patterns

## System Architecture

Mac-letterhead follows a highly modular architecture with enhanced component separation:

```
Mac-letterhead
├── letterhead_pdf/             # Main package
│   ├── __init__.py             # Package initialization and version management
│   ├── main.py                 # Entry point and CLI handling with CSS support
│   ├── pdf_merger.py           # PDF merging functionality
│   ├── pdf_utils.py            # PDF utility functions with smart analysis
│   ├── markdown_processor.py   # Markdown to PDF conversion with CSS support
│   ├── exceptions.py           # Custom exceptions
│   ├── log_config.py           # Logging configuration
│   ├── installation/           # Modular installation system (v0.9.6)
│   │   ├── __init__.py         # Installation package initialization
│   │   ├── droplet_builder.py  # Core droplet creation orchestration
│   │   ├── resource_manager.py # Stationery and resource bundling
│   │   ├── applescript_generator.py # Template processing and generation
│   │   ├── macos_integration.py # Platform-specific macOS operations
│   │   ├── validator.py        # Input validation and error handling
│   │   └── templates/          # AppleScript templates by execution context
│   │       ├── production_droplet.applescript  # uvx production template
│   │       └── development_droplet.applescript # Local development template
│   └── resources/              # Application resources and defaults
│       ├── icon.png            # Application icon
│       ├── Mac-letterhead.icns # macOS application icon
│       ├── defaults.css        # Default CSS for Markdown processing
│       ├── droplet_template.applescript        # Legacy production template
│       └── droplet_template_local.applescript  # Legacy development template
├── tests/                      # Test suite
│   ├── utils/                  # Test utilities
│   └── files/                  # Test files and generated test data
├── memory-bank/                # Documentation and context
└── Makefile                    # Build, test, and release automation (version management)
```

## Key Technical Decisions

### 1. Smart Letterhead Analysis

- **PyMuPDF (fitz)**: Used for PDF manipulation and intelligent letterhead analysis
- **Position Detection Algorithm**: Geometric analysis using page center thresholds to detect left/right/center letterhead positioning
- **Adaptive Margin Calculation**: Different margin strategies based on letterhead position:
  - Left-positioned: 72pt left margin, 36pt right margin
  - Right-positioned: 36pt left margin, 72pt right margin  
  - Center-positioned: 54pt symmetric margins
- **Usable Area Optimization**: Provides ~82% usable page width regardless of letterhead design

### 2. Modular Installation Architecture

- **Component Separation**: Discrete modules for different installation responsibilities
- **Enhanced Debugging**: Each component can be tested and troubleshot independently
- **Execution Context Support**: Separate templates for production vs development modes
- **Validation Layer**: Input validation and error handling separated from core logic

### 3. Markdown Processing

- **Smart Environment Detection**: Runtime detection and adaptation to uvx isolated environments
- **Library Path Management**: Internal configuration of WeasyPrint library paths
- **Tiered Rendering**:
  - **Primary**: WeasyPrint for high-quality PDF generation
  - **Fallback**: ReportLab for environments where WeasyPrint cannot be installed
- **Consistent API**: Same interface regardless of the underlying rendering engine

### 4. Development & Production Modes

- **Development Mode**: `--dev` flag creates local test droplets using development code
- **Production Mode**: Uses uvx-installed packages for stable deployment
- **Template Separation**: Different AppleScript templates for different execution contexts
- **Enhanced Diagnostics**: Better logging and debugging capabilities in development mode

## Design Patterns

### 1. Strategy Pattern

Used for implementing different PDF merging strategies:

```python
# Conceptual representation
class MergeStrategy:
    def merge(self, letterhead_page, content_page):
        pass

class DarkenStrategy(MergeStrategy):
    def merge(self, letterhead_page, content_page):
        # Implementation for darken strategy
        pass

class MultiplyStrategy(MergeStrategy):
    def merge(self, letterhead_page, content_page):
        # Implementation for multiply strategy
        pass
```

### 2. Factory Pattern

Used for creating the appropriate PDF processor based on input type:

```python
# Conceptual representation
def create_processor(input_file):
    if input_file.endswith('.pdf'):
        return PDFProcessor()
    elif input_file.endswith('.md'):
        return MarkdownProcessor()
    else:
        raise UnsupportedFileTypeError()
```

### 3. Module Pattern

Used for organizing the installation system into discrete, testable components:

```python
# Conceptual representation
class DropletBuilder:
    def build(self, letterhead_path, name, dev_mode=False):
        # Core droplet creation logic
        pass

class ResourceManager:
    def copy_resources(self, source, destination):
        # File and resource handling
        pass

class AppleScriptGenerator:
    def generate(self, template_path, context):
        # Template processing and customization
        pass
```

### 4. Adapter Pattern

Used to provide a consistent interface for different Markdown rendering engines:

```python
# Conceptual representation
class MarkdownRenderer:
    def render(self, markdown_content, output_path):
        pass

class WeasyPrintRenderer(MarkdownRenderer):
    def render(self, markdown_content, output_path):
        # WeasyPrint implementation with library path management
        pass

class ReportLabRenderer(MarkdownRenderer):
    def render(self, markdown_content, output_path):
        # ReportLab implementation
        pass
```

### 5. Command Pattern

Used for CLI command handling:

```python
# Conceptual representation
class Command:
    def execute(self):
        pass

class MergeCommand(Command):
    def __init__(self, letterhead, title, output_dir, input_file):
        self.letterhead = letterhead
        self.title = title
        self.output_dir = output_dir
        self.input_file = input_file
    
    def execute(self):
        # Implementation for merge command
        pass

class InstallCommand(Command):
    def __init__(self, letterhead, name, dev_mode=False):
        self.letterhead = letterhead
        self.name = name
        self.dev_mode = dev_mode
    
    def execute(self):
        # Implementation for install command with dev mode support
        pass
```

### 6. Template Method Pattern

Used for different execution contexts in droplet creation:

```python
# Conceptual representation
class DropletTemplate:
    def create_droplet(self):
        self.validate_inputs()
        self.prepare_resources()
        self.generate_script()
        self.create_application()
    
    def generate_script(self):
        # Abstract method implemented by subclasses
        pass

class ProductionDropletTemplate(DropletTemplate):
    def generate_script(self):
        # Use uvx-installed packages
        pass

class DevelopmentDropletTemplate(DropletTemplate):
    def generate_script(self):
        # Use local development code
        pass
```

## Critical Implementation Paths

### 1. Smart PDF Merging Process

1. **Load and Analyze**: Load letterhead PDF and analyze letterhead positioning
2. **Position Detection**: 
   - Calculate page center and letterhead element positions
   - Determine letterhead type (left/right/center positioned)
   - Calculate optimal margins based on position
3. **Content Processing**: Load content PDF and apply appropriate margins
4. **Page Merging**: For each page in content PDF:
   - Determine which letterhead page to use (first or subsequent)
   - Apply selected merging strategy with position-aware margins
   - Add to output document
5. **Output Generation**: Save merged document with preserved metadata

### 2. Intelligent Markdown to PDF Conversion

1. **Environment Detection**: Detect uvx isolation and configure library paths
2. **Letterhead Analysis**: Analyze letterhead PDF for smart margin calculation
3. **Rendering Engine Selection**: 
   - Attempt WeasyPrint with proper library path configuration
   - Fall back to ReportLab if WeasyPrint unavailable
4. **Content Rendering**:
   - Parse Markdown to HTML
   - Apply position-aware CSS styling with calculated margins
   - Render HTML to PDF with optimal content area
5. **Letterhead Application**: Apply letterhead to generated PDF

### 3. Modular Desktop Application Installation

1. **Input Validation**: Validate letterhead file and installation parameters
2. **Resource Management**: 
   - Copy letterhead template to application resources
   - Manage application icons and metadata
3. **Template Processing**:
   - Select appropriate template (production vs development)
   - Generate AppleScript with context-specific configuration
4. **Application Creation**:
   - Create macOS application bundle structure
   - Configure drag-and-drop functionality
   - Set up logging and error handling
5. **Integration**: Register application and create desktop shortcuts

### 4. Development Mode Workflow

1. **Mode Detection**: Recognize `--dev` flag and configure development context
2. **Local Code Integration**: Configure droplet to use local development code
3. **Enhanced Debugging**: Enable detailed logging and diagnostic capabilities
4. **Testing Support**: Create isolated test environment for safe development
5. **Validation**: Verify functionality before production deployment

## Component Relationships

### Core Processing Components
- **main.py**: Coordinates overall flow and dispatches to appropriate processors
- **pdf_merger.py**: Handles PDF-to-PDF merging operations with smart positioning
- **markdown_processor.py**: Converts Markdown to PDF with intelligent margin detection
- **pdf_utils.py**: Provides letterhead analysis and smart margin calculation utilities

### Installation System Components
- **droplet_builder.py**: Orchestrates the entire droplet creation process
- **resource_manager.py**: Handles file operations, copying, and resource management
- **applescript_generator.py**: Processes templates and generates execution scripts
- **macos_integration.py**: Handles platform-specific operations and app bundle creation
- **validator.py**: Input validation, error handling, and prerequisite checking

### Template System
- **production_droplet.applescript**: Template for uvx-based production installations
- **development_droplet.applescript**: Template for local development testing
- **droplet_template.applescript**: Legacy template for backward compatibility

### Interaction Flow
1. **main.py** → **installation/droplet_builder.py** (for install commands)
2. **droplet_builder.py** → **validator.py** (input validation)
3. **droplet_builder.py** → **resource_manager.py** (resource handling)
4. **droplet_builder.py** → **applescript_generator.py** (script generation)
5. **droplet_builder.py** → **macos_integration.py** (app bundle creation)
6. **Generated droplets** → **pdf_merger.py** or **markdown_processor.py** (document processing)
7. **pdf_utils.py** provides smart analysis for both merger and processor components

### Key Dependencies
- **Smart margin detection** (pdf_utils.py) is used by both PDF and Markdown processors
- **Template system** supports both production and development execution contexts
- **Resource management** ensures consistent file handling across installation and processing
- **Validation layer** provides error handling and input checking across all components

## CSS Architecture System (v0.9.6)

### Clean CSS Loading Strategy

**Design Decision**: Eliminate hardcoded CSS from Python code, implementing a clean cascade:
1. **defaults.css** (from package resources) - comprehensive baseline styling
2. **custom.css** (optional user file) - user customizations
3. **hardcoded page margins only** - smart letterhead margins with `!important`

### Resource Loading Implementation

```python
# Cross-environment resource loading with fallbacks
def load_default_css():
    try:
        # Modern approach (Python 3.9+)
        from importlib import resources
        with resources.open_text('letterhead_pdf.resources', 'defaults.css') as f:
            return f.read()
    except (ImportError, AttributeError):
        # Backport fallback
        import importlib_resources
        with importlib_resources.open_text('letterhead_pdf.resources', 'defaults.css') as f:
            return f.read()
    except ImportError:
        # File path fallback
        current_dir = os.path.dirname(__file__)
        with open(os.path.join(current_dir, 'resources', 'defaults.css'), 'r') as f:
            return f.read()
```

### CSS Processing Pattern

1. **Load Base Styling**: Read defaults.css from package resources
2. **Load Custom Styling**: Read user-provided CSS file if specified
3. **Filter Conflicting Rules**: Remove @page rules from custom CSS to preserve smart margins
4. **Apply Cascade Order**: defaults → custom → hardcoded margins
5. **Generate Final CSS**: Combine all CSS with smart margins taking precedence

### AppleScript Integration

- **CSS Detection**: Templates automatically detect bundled CSS files in app resources
- **Parameter Passing**: Droplets automatically include `--css` parameter for merge-md commands
- **Fallback Handling**: Graceful operation when CSS files are missing or invalid

### Benefits

- **Clean Architecture**: Only page margins hardcoded in Python, all styling externalized
- **User Customization**: Full CSS customization while preserving letterhead functionality
- **Cross-Environment**: Compatible with Python 3.9+ and older versions
- **Smart Precedence**: Letterhead margins always preserved regardless of custom CSS
