# MCP Directory Submission Template

Use this template when submitting Mac-letterhead to community MCP directories like mcp.so.

---

## Server Information

**Server Name**: Mac-letterhead

**Package Name**: Mac-letterhead

**Installation Command**:
```bash
uvx mac-letterhead[mcp]
```

**Basic Usage**:
```bash
# Generic multi-style server
uvx mac-letterhead mcp

# Style-specific server
uvx mac-letterhead mcp --style easytocloud
```

## Description

Professional letterhead PDF generator for macOS with Model Context Protocol (MCP) integration. Mac-letterhead enables AI assistants to create letterheaded PDFs from Markdown content and apply letterheads to existing PDFs through natural language commands.

### Key Features

- **Markdown to PDF**: Convert Markdown to professionally formatted PDFs with letterhead overlay
- **PDF Merging**: Apply letterhead templates to existing PDF documents
- **Smart Margin Detection**: Automatically analyzes letterhead layouts to calculate optimal content margins
- **Dual Rendering Pipeline**: WeasyPrint for high-quality rendering, ReportLab for fallback
- **GitHub Flavored Markdown**: Full support for GFM features (tables, task lists, strikethrough)
- **Custom Styling**: Apply custom CSS to control document appearance
- **Multi-Page Letterheads**: Support for different first page, even/odd pages
- **Convention-Based**: Auto-resolves letterhead and CSS files from `~/.letterhead/` directory
- **Flexible Configuration**: Generic multi-style or dedicated single-style servers

### Platform Requirements

- **macOS**: Required (uses native Quartz/CoreGraphics for PDF processing)
- **Python**: ≥3.10
- **System Dependencies** (optional for high-quality rendering):
  ```bash
  brew install pango cairo fontconfig freetype harfbuzz
  ```

## MCP Tools

Mac-letterhead provides 4 MCP tools:

1. **`create_letterhead_pdf`**: Create letterheaded PDF from Markdown content
   - Converts Markdown to PDF with smart margin detection
   - Supports GFM, tables, code blocks, custom CSS
   - Multiple merge strategies (darken, multiply, overlay, transparency)

2. **`merge_letterhead_pdf`**: Apply letterhead to existing PDF
   - Preserves original document formatting
   - Multiple blend strategies for different letterhead designs
   - Quality preservation during merge

3. **`analyze_letterhead`**: Analyze letterhead template margins
   - Smart content detection (headers, footers, logos)
   - Calculates optimal printable areas
   - Reports margin recommendations

4. **`list_letterhead_templates`**: List available letterhead templates
   - Shows all templates in `~/.letterhead/` directory
   - Displays associated CSS files
   - Template paths and names

## Configuration Examples

### Generic Multi-Style Server
Users specify style per request:
```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Generic letterhead PDF generator"
    }
  }
}
```

**Usage**: *"Using the letterhead server, create an easytocloud style PDF about..."*

### Style-Specific Server
Pre-configured for specific letterhead:
```json
{
  "mcpServers": {
    "easytocloud": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "easytocloud"],
      "description": "EasyToCloud letterhead PDF generator"
    }
  }
}
```

**Usage**: *"Create an easytocloud letterheaded PDF about..."*

### Custom Configuration
With output directory and prefix:
```json
{
  "mcpServers": {
    "company-docs": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "company",
        "--output-dir", "~/Documents/generated-pdfs",
        "--output-prefix", "CompanyDocs"
      ],
      "description": "Company documentation generator"
    }
  }
}
```

## Setup Instructions

1. **Install Mac-letterhead with MCP support**:
   ```bash
   uvx install "mac-letterhead[mcp]"
   ```

2. **Create letterhead directory**:
   ```bash
   mkdir -p ~/.letterhead
   ```

3. **Add letterhead templates**:
   ```bash
   # Place PDF templates in ~/.letterhead/
   ~/.letterhead/
   ├── company.pdf        # Letterhead template
   ├── company.css        # Optional custom styling
   ├── personal.pdf       # Another letterhead
   └── personal.css       # Its styling
   ```

4. **Configure MCP client** (Claude Code, Claude Desktop, etc.):
   Add server configuration to MCP settings file

5. **Start using**:
   Ask your AI assistant to create letterheaded PDFs!

## Documentation

- **Main README**: https://github.com/easytocloud/Mac-letterhead/blob/main/README.md
- **MCP Guide**: https://github.com/easytocloud/Mac-letterhead/blob/main/README_MCP.md
- **LLM Installation**: https://github.com/easytocloud/Mac-letterhead/blob/main/llms-install.md
- **Contributing**: https://github.com/easytocloud/Mac-letterhead/blob/main/CONTRIBUTING.md

## Repository

**GitHub**: https://github.com/easytocloud/Mac-letterhead

**License**: MIT

**PyPI**: https://pypi.org/project/Mac-letterhead/

## Category

Document Generation / PDF Tools / Productivity

## Tags

`pdf`, `letterhead`, `markdown`, `document-generation`, `macos`, `branding`, `professional-documents`, `pdf-merge`, `markdown-to-pdf`, `github-flavored-markdown`, `mcp-server`

## Support

- **Issues**: https://github.com/easytocloud/Mac-letterhead/issues
- **Discussions**: https://github.com/easytocloud/Mac-letterhead/discussions

## Example Use Cases

- **Corporate Communications**: Apply company branding to business correspondence
- **Legal Documents**: Add firm letterhead to contracts and legal papers
- **Technical Documentation**: Convert Markdown docs to branded PDFs
- **Proposals & Reports**: Create professional client deliverables
- **AI-Generated Content**: Use Claude or other AI tools to create branded documents through natural language

---

## Submission Checklist

- [ ] Server name: Mac-letterhead
- [ ] Installation command: `uvx mac-letterhead[mcp]`
- [ ] Platform: macOS (Python ≥3.10)
- [ ] MCP extra package: `mac-letterhead[mcp]`
- [ ] Documentation links provided
- [ ] Configuration examples included
- [ ] Category: Document Generation / PDF Tools
- [ ] Tags added
- [ ] License: MIT
- [ ] Repository: https://github.com/easytocloud/Mac-letterhead
