# Mac-letterhead

<!-- mcp-name: io.github.easytocloud/mac-letterhead -->

![PyPI Version](https://img.shields.io/pypi/v/Mac-letterhead.svg)
![Build Status](https://github.com/easytocloud/Mac-letterhead/actions/workflows/publish.yml/badge.svg)
![License](https://img.shields.io/github/license/easytocloud/Mac-letterhead.svg)
![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3TDEyIDEyTDIxIDdMMTIgMloiIGZpbGw9IndoaXRlIi8+CjxwYXRoIGQ9Ik0zIDdWMTdMMTIgMjJWMTJMMyA3WiIgZmlsbD0id2hpdGUiLz4KPHBhdGggZD0iTTIxIDdWMTdMMTIgMjJWMTJMMjEgN1oiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=)

<!-- GitHub can't render .icns files directly, so we use HTML to link the icon badge -->
<a href="https://pypi.org/project/Mac-letterhead/" title="Mac-letterhead on PyPI">
  <img src="https://raw.githubusercontent.com/easytocloud/Mac-letterhead/main/letterhead_pdf/resources/icon.png" width="128" height="128" alt="Mac-letterhead Logo" align="right" />
</a>

A professional macOS utility that applies letterhead templates to PDF and Markdown documents. Mac-letterhead creates drag-and-drop applications that automatically merge your company letterhead with documents while preserving formatting and ensuring professional presentation.

## What Mac-letterhead Does

Mac-letterhead transforms your letterhead PDF into a powerful document processing tool:

### For PDF Documents
- **Direct Overlay**: Your letterhead is applied as an overlay to existing PDFs without reformatting the original document
- **Multiple Blend Modes**: Choose from various merging strategies (darken, multiply, overlay, transparency) to suit different letterhead designs
- **Quality Preservation**: All original formatting, fonts, and layout are maintained during the merge process

### For Markdown Documents  
- **Intelligent Layout**: Analyzes your letterhead PDF to identify headers, footers, logos, and text elements
- **Smart Margin Detection**: Automatically calculates the optimal printable area within your letterhead design
- **Professional Rendering**: Converts Markdown to beautifully formatted PDF with proper typography, tables, code blocks, and styling
- **Adaptive Positioning**: Handles left, right, and center-positioned letterheads with appropriate margin adjustments

### Multi-Page Letterhead Support
- **Single Page**: Applied consistently to all document pages
- **Two Pages**: First page template for page 1, second template for subsequent pages  
- **Three Pages**: Distinct templates for first page, even pages, and odd pages

## Requirements

- **macOS**: Required for droplet applications and PDF processing
- **Python**: 3.10 or higher
- **uv package manager**: Install with `pip install uv` if needed

## Installation

Install Mac-letterhead and create your first letterhead application:

```bash
# Quick start - create a letterhead droplet on your desktop  
uvx mac-letterhead install --name "Company"

# For AI integration, install with MCP support
uvx install "mac-letterhead[mcp]"
```

### MCP Registry

Mac-letterhead is published in the [official MCP Registry](https://registry.modelcontextprotocol.io/servers/io.github.easytocloud/mac-letterhead), making it easily discoverable by AI assistants and MCP clients.

**Find Mac-letterhead in**:
- **Official MCP Registry**: https://registry.modelcontextprotocol.io
- **GitHub MCP Registry**: Automatically synced from official registry
- **Community Directories**: mcp.so and other MCP server catalogs

**Quick Install for MCP Clients**:
```bash
uvx mac-letterhead[mcp]
```

For complete MCP configuration and usage, see [README_MCP.md](README_MCP.md).

### Prerequisites

Mac-letterhead expects your letterhead files to be organized in `~/.letterhead/`:

```bash
~/.letterhead/
├── company.pdf        # Your letterhead template
├── company.css        # Optional custom styling
└── personal.pdf       # Additional letterhead templates
```

This creates a macOS application that you can drag documents onto to apply your letterhead. The MCP option adds support for AI tool integration.

### System Dependencies

For optimal Markdown rendering, install the required libraries:

```bash
brew install pango cairo fontconfig freetype harfbuzz
```

These libraries enable high-quality PDF generation with advanced typography support.

## Usage

### Creating Letterhead Applications

#### Basic Application Creation
```bash
# Create a letterhead droplet using ~/.letterhead/company.pdf
uvx mac-letterhead install --name "company"
```

#### Custom Letterhead Override
```bash
# Use a different letterhead file but keep the app name
uvx mac-letterhead install --name "Company Correspondence" --letterhead /path/to/custom-letterhead.pdf
```

#### Advanced Markdown Styling
```bash
# Create a letterhead application with custom CSS styling
uvx mac-letterhead install --name "Technical Reports" --css /path/to/custom-styles.css
```

The `--css` option allows you to customize the appearance of rendered Markdown documents:
- **Typography**: Custom fonts, sizes, colors, and spacing
- **Layout**: Table styling, code block formatting, list appearance
- **Branding**: Consistent styling that complements your letterhead design
- **Responsiveness**: Ensures content fits properly within the detected printable area

#### Install Command Reference

The install command follows this pattern:

```bash
uvx mac-letterhead install --name "AppName" [--letterhead path] [--css path] [--output-dir dir]
```

**Required:**
- `--name`: Sets both the application name and the style. Automatically looks for `~/.letterhead/<name>.pdf` and `~/.letterhead/<name>.css`

**Optional:**
- `--letterhead`: Override the default letterhead PDF path  
- `--css`: Override the default CSS file path
- `--output-dir`: Specify where to create the app (default: Desktop)
- `--dev`: Create a development version using local code

### Using Letterhead Applications

Once created, your letterhead application appears on your desktop:

1. **For PDF Files**: Drag any PDF onto the application icon - the letterhead is applied as an overlay
2. **For Markdown Files**: Drag .md files onto the application - they're converted to PDF with your letterhead and proper formatting
3. **Preview Letterhead**: Double-click the application to view information and preview the letterhead template

### Direct Command-Line Usage

#### PDF Merging
```bash
# Apply letterhead to a PDF document
uvx mac-letterhead merge /path/to/letterhead.pdf "Document Title" ~/Desktop /path/to/document.pdf

# Use a specific blending strategy
uvx mac-letterhead merge /path/to/letterhead.pdf "Report" ~/Desktop /path/to/report.pdf --strategy overlay
```

#### Markdown Processing  
```bash
# Convert Markdown with letterhead
uvx mac-letterhead merge-md /path/to/letterhead.pdf "Technical Guide" ~/Desktop /path/to/guide.md

# With custom CSS styling
uvx mac-letterhead merge-md /path/to/letterhead.pdf "Proposal" ~/Desktop /path/to/proposal.md --css /path/to/styles.css
```

#### AI Integration with MCP Server
Mac-letterhead includes an MCP (Model Context Protocol) server that enables AI tools like Claude to create letterheaded PDFs through natural language commands:

```bash
# Start a generic multi-style server
uvx mac-letterhead mcp

# Start a dedicated single-style server  
uvx mac-letterhead mcp --style easytocloud --output-dir ~/Documents/generated-pdfs
```

**Usage Examples with Claude:**
- *"Using the letterhead server, create an easytocloud style PDF about our new cloud services"*
- *"Generate a personal letterheaded document for my consulting proposal"*

The MCP server automatically:
- Converts Markdown content to professionally formatted PDFs
- Applies appropriate letterhead templates and CSS styling
- Manages output directories and file naming
- Supports both style-specific and generic multi-style configurations

For complete MCP setup and configuration details, see [README_MCP.md](README_MCP.md).

### Blending Strategies

Choose the optimal strategy for your letterhead design:

- **`darken`** (Default): Ideal for light letterheads with dark text/logos - provides excellent readability
- **`multiply`**: Creates watermark-like effects, good for subtle branding
- **`overlay`**: Balances visibility of both document content and letterhead elements  
- **`transparency`**: Smooth blending with semi-transparent effects
- **`reverse`**: Places letterhead elements on top of document content

## Advanced Features

### Custom CSS Styling

Create sophisticated document styling by providing custom CSS:

```css
/* custom-styles.css */
h1 { color: #2c5aa0; border-bottom: 2px solid #2c5aa0; }
table { border: 1px solid #ddd; background: #f9f9f9; }
code { background: #f4f4f4; padding: 2px 4px; }
```

The CSS is automatically integrated with Mac-letterhead's smart margin system to ensure content fits properly within your letterhead design.

### Markdown Features

Mac-letterhead provides professional Markdown rendering with:

- **Typography**: Proper heading hierarchy, paragraph spacing, and font sizing
- **Tables**: Clean borders, consistent padding, and professional appearance  
- **Code Blocks**: Syntax highlighting for multiple programming languages
- **Lists & Quotes**: Proper indentation and formatting for nested content
- **Images & Links**: Full support for embedded images and hyperlinks
- **Math**: LaTeX-style mathematical expressions (when supported)

#### GitHub Flavored Markdown Support

Mac-letterhead includes enhanced support for GitHub Flavored Markdown (GFM) features:

- **Strikethrough**: `~~deleted text~~` renders with proper strikethrough formatting
- **Task Lists**: Interactive-style checkboxes with `- [x] completed` and `- [ ] pending`
- **Enhanced Tables**: Improved table rendering with better alignment and styling
- **Automatic Detection**: GFM features are automatically enabled when the pycmarkgfm library is available

Task lists are rendered with professional Unicode checkboxes (☑ for completed, ☐ for pending) that are properly sized and aligned, including within table cells.

### Dual Rendering Pipeline

Mac-letterhead features a sophisticated dual-backend rendering system that automatically selects the best available technology while providing manual control when needed.

#### PDF Rendering Backends

**WeasyPrint** (Preferred when available):
- **Advantages**: Superior CSS support, advanced typography, precise layout control
- **Features**: Full HTML5/CSS3 support, web fonts, complex layouts, print-specific CSS
- **Requirements**: System libraries (`brew install pango cairo fontconfig freetype harfbuzz`)
- **Use Case**: High-quality documents requiring advanced styling and typography

**ReportLab** (Reliable fallback):
- **Advantages**: Pure Python implementation, no system dependencies, consistent rendering
- **Features**: Professional PDF generation, basic HTML support, reliable cross-platform operation
- **Requirements**: None (included with Python installation)
- **Use Case**: Simple documents, environments without system library access

#### Markdown Processing Backends

**GitHub Flavored Markdown (GFM)** (Enhanced when available):
- **Library**: pycmarkgfm (Python bindings to GitHub's cmark-gfm parser)
- **Features**: Strikethrough, task lists, enhanced tables, autolinks, GitHub-compatible parsing
- **Compatibility**: Full compatibility with GitHub markdown rendering
- **Use Case**: Documents with GFM-specific features, GitHub repository documentation

**Standard Markdown** (Universal fallback):
- **Library**: Python markdown with extensions
- **Features**: CommonMark compliance, basic table support, code highlighting
- **Compatibility**: Works in all Python environments
- **Use Case**: Simple documents, maximum compatibility requirements

#### Backend Selection and Control

**Automatic Selection** (Default behavior):
```bash
# Uses best available backends automatically
uvx mac-letterhead merge-md letterhead.pdf "Document" ~/Desktop document.md
```

**Manual Backend Control**:
```bash
# Force specific PDF backend
uvx mac-letterhead merge-md letterhead.pdf "Report" ~/Desktop report.md --pdf-backend reportlab

# Force specific Markdown backend  
uvx mac-letterhead merge-md letterhead.pdf "Guide" ~/Desktop guide.md --markdown-backend standard

# Combine specific backends
uvx mac-letterhead merge-md letterhead.pdf "Technical" ~/Desktop tech.md --pdf-backend weasyprint --markdown-backend gfm
```

**Available Backend Options**:
- `--pdf-backend`: `weasyprint`, `reportlab`, `auto` (default: `auto`)
- `--markdown-backend`: `gfm`, `standard`, `auto` (default: `auto`)

#### Backend Capabilities Matrix

| Feature | WeasyPrint + GFM | WeasyPrint + Standard | ReportLab + GFM | ReportLab + Standard |
|---------|------------------|----------------------|-----------------|---------------------|
| Basic Markdown | ✅ Excellent | ✅ Excellent | ✅ Good | ✅ Good |
| Advanced CSS | ✅ Full Support | ✅ Full Support | ⚠️ Limited | ⚠️ Limited |
| Strikethrough | ✅ Native | ❌ Not Available | ✅ Unicode | ❌ Not Available |
| Task Lists | ✅ Styled Checkboxes | ❌ Not Available | ✅ Unicode Checkboxes | ❌ Not Available |
| Complex Tables | ✅ Advanced | ✅ Good | ✅ Basic | ✅ Basic |
| Typography | ✅ Professional | ✅ Professional | ✅ Standard | ✅ Standard |
| System Dependencies | ⚠️ Required | ⚠️ Required | ✅ None | ✅ None |

#### Testing and Validation

The project includes comprehensive testing for all backend combinations:

```bash
# Test all combinations across Python versions
make test-backend-combinations

# Test specific combinations
make test-weasyprint-gfm      # WeasyPrint + GitHub Flavored Markdown
make test-weasyprint-standard # WeasyPrint + Standard Markdown  
make test-reportlab-gfm       # ReportLab + GitHub Flavored Markdown
make test-reportlab-standard  # ReportLab + Standard Markdown
```

Each test combination generates output files with naming patterns like `document-py3.11-weasyprint-gfm.pdf` for easy comparison and quality validation.

## Use Cases

- **Corporate Communications**: Apply company branding to business correspondence
- **Legal Documents**: Add firm letterhead and disclaimers to contracts and legal papers
- **Financial Documents**: Brand invoices, statements, and financial reports
- **Technical Documentation**: Convert Markdown documentation to branded PDFs  
- **Academic Papers**: Add institutional letterhead to research papers and reports
- **Proposals & Reports**: Create professional client deliverables from Markdown sources
- **AI-Generated Content**: Use Claude or other AI tools to create branded documents through natural language

## Troubleshooting

### Common Issues

**Library Dependencies**: If you see WeasyPrint warnings, the system automatically falls back to ReportLab - functionality is not affected.

**File Permissions**: If applications request file access, approve the permissions in System Preferences > Security & Privacy > Privacy > Files and Folders.

**Margin Detection**: The system automatically analyzes letterhead positioning. If margins appear incorrect, ensure your letterhead PDF contains clear visual elements (logos, text, graphics) in header/footer areas.

### Log Files
- Application logs: `~/Library/Logs/Mac-letterhead/letterhead.log`
- Droplet logs: `~/Library/Logs/Mac-letterhead/droplet.log`

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing procedures, and pull request guidelines.

## License

MIT License