# Mac-letterhead System Patterns

## System Architecture

Mac-letterhead follows a modular architecture with clear separation of concerns:

```
Mac-letterhead
├── letterhead_pdf/             # Main package
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # Entry point and CLI handling
│   ├── pdf_merger.py           # PDF merging functionality
│   ├── pdf_utils.py            # PDF utility functions
│   ├── markdown_processor.py   # Markdown to PDF conversion
│   ├── installer.py            # Desktop app installation
│   ├── exceptions.py           # Custom exceptions
│   ├── log_config.py           # Logging configuration
│   └── resources/              # Application resources
│       ├── icon.png            # Application icon
│       └── Mac-letterhead.icns # macOS application icon
├── tests/                      # Test suite
│   ├── utils/                  # Test utilities
│   └── files/                  # Test files
└── Makefile                    # Build and test automation
```

## Key Technical Decisions

### 1. PDF Processing

- **PyMuPDF (fitz)**: Used for PDF manipulation due to its comprehensive feature set and performance
- **Custom Merging Strategies**: Implemented various blending modes (darken, multiply, overlay) to handle different letterhead designs
- **Page Analysis**: Automatic detection of letterhead regions to avoid content overlap

### 2. Markdown Processing

- **Tiered Approach**:
  - **Primary**: WeasyPrint for high-quality PDF generation
  - **Fallback**: ReportLab for environments where WeasyPrint cannot be installed
- **Feature Detection**: Runtime detection of available libraries to determine rendering approach
- **Consistent API**: Same interface regardless of the underlying rendering engine

### 3. Installation and Packaging

- **Self-contained Package**: Minimal external dependencies
- **Desktop Integration**: Creates a macOS application for drag-and-drop functionality
- **Command-line Interface**: Full functionality available through CLI for automation

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

### 3. Adapter Pattern

Used to provide a consistent interface for different Markdown rendering engines:

```python
# Conceptual representation
class MarkdownRenderer:
    def render(self, markdown_content, output_path):
        pass

class WeasyPrintRenderer(MarkdownRenderer):
    def render(self, markdown_content, output_path):
        # WeasyPrint implementation
        pass

class ReportLabRenderer(MarkdownRenderer):
    def render(self, markdown_content, output_path):
        # ReportLab implementation
        pass
```

### 4. Command Pattern

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
```

## Critical Implementation Paths

### 1. PDF Merging Process

1. Load letterhead PDF and content PDF
2. Analyze letterhead to detect regions (header, footer, etc.)
3. For each page in content PDF:
   - Determine which letterhead page to use (first or subsequent)
   - Apply selected merging strategy
   - Add to output document
4. Save merged document

### 2. Markdown to PDF Conversion

1. Parse Markdown to HTML
2. Determine available rendering engine (WeasyPrint or ReportLab)
3. If WeasyPrint:
   - Apply CSS styling
   - Render HTML to PDF
4. If ReportLab:
   - Convert HTML elements to ReportLab flowables
   - Build PDF document
5. Apply letterhead to generated PDF

### 3. Desktop Application Installation

1. Create application directory structure
2. Copy letterhead template to application resources
3. Create executable script
4. Register file associations for drag-and-drop functionality
5. Create application icon and metadata

## Component Relationships

- **main.py**: Coordinates overall flow and dispatches to appropriate processors
- **pdf_merger.py**: Handles PDF-to-PDF merging operations
- **markdown_processor.py**: Converts Markdown to PDF before merging
- **pdf_utils.py**: Provides utility functions used by both merging processes
- **installer.py**: Creates desktop application for drag-and-drop functionality
