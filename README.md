# Mac-letterhead

![PyPI Version](https://img.shields.io/pypi/v/Mac-letterhead.svg)
![Build Status](https://github.com/easytocloud/Mac-letterhead/actions/workflows/publish.yml/badge.svg)
![License](https://img.shields.io/github/license/easytocloud/Mac-letterhead.svg)

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
uvx mac-letterhead install /path/to/your/letterhead.pdf
```

This creates a macOS application that you can drag documents onto to apply your letterhead.

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
# Create a letterhead droplet with default name
uvx mac-letterhead install /path/to/company-letterhead.pdf
```

#### Custom Application Name
```bash
# Specify a custom name for your letterhead application  
uvx mac-letterhead install /path/to/letterhead.pdf --name "Company Correspondence"
```

#### Advanced Markdown Styling
```bash
# Create a letterhead application with custom CSS styling
uvx mac-letterhead install /path/to/letterhead.pdf --name "Technical Reports" --css /path/to/custom-styles.css
```

The `--css` option allows you to customize the appearance of rendered Markdown documents:
- **Typography**: Custom fonts, sizes, colors, and spacing
- **Layout**: Table styling, code block formatting, list appearance
- **Branding**: Consistent styling that complements your letterhead design
- **Responsiveness**: Ensures content fits properly within the detected printable area

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

## Use Cases

- **Corporate Communications**: Apply company branding to business correspondence
- **Legal Documents**: Add firm letterhead and disclaimers to contracts and legal papers
- **Financial Documents**: Brand invoices, statements, and financial reports
- **Technical Documentation**: Convert Markdown documentation to branded PDFs
- **Academic Papers**: Add institutional letterhead to research papers and reports
- **Proposals & Reports**: Create professional client deliverables from Markdown sources

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