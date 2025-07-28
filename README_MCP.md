# Mac-letterhead MCP Server

The Mac-letterhead MCP (Model Context Protocol) server enables LLMs to create letterheaded PDFs from Markdown content automatically.

## Installation

```bash
# Install Mac-letterhead with MCP support
uvx install "mac-letterhead[mcp]"
```

## MCP Configuration

Add to your MCP client configuration:

### Basic Configuration
```json
{
  "mcpServers": {
    "mcp-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Mac Letterhead PDF Generator"
    }
  }
}
```

### Named Letterhead Servers (Recommended)

**Convention-Based Configuration:**
The server automatically resolves letterhead and CSS files from `~/.letterhead/` based on the server name.

First, organize your letterhead files:
```bash
mkdir -p ~/.letterhead
# Place your letterhead files like:
# ~/.letterhead/easytocloud.pdf
# ~/.letterhead/easytocloud.css  (optional)
# ~/.letterhead/isc.pdf  
# ~/.letterhead/isc.css  (optional)
# ~/.letterhead/personal.pdf
```

Then configure multiple servers with various options:

```json
{
  "mcpServers": {
    "easytocloud": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--name", "easytocloud"
      ],
      "description": "EasyToCloud letterhead PDF generator (uses ~/.letterhead/easytocloud.pdf and .css)"
    },
    "isc": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp", 
        "--name", "isc",
        "--css", "~/Documents/corporate-styles/isc-branding.css"
      ],
      "description": "ISC letterhead with custom CSS from corporate folder"
    },
    "personal": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--name", "personal",
        "--letterhead", "~/Dropbox/letterheads/erik-personal.pdf"
      ],
      "description": "Personal letterhead from Dropbox, auto-CSS from ~/.letterhead/personal.css"
    },
    "client-acme": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--name", "client-acme",
        "--letterhead", "~/Documents/clients/acme/letterhead.pdf",
        "--css", "~/Documents/clients/acme/brand-guidelines.css"
      ],
      "description": "ACME Corp client letterhead with full custom paths"
    }
  }
}
```

**File Resolution Examples:**
- `easytocloud`: Uses convention-based files `~/.letterhead/easytocloud.pdf` + `~/.letterhead/easytocloud.css`
- `isc`: Uses `~/.letterhead/isc.pdf` + custom CSS from `~/Documents/corporate-styles/isc-branding.css`
- `personal`: Uses custom letterhead from `~/Dropbox/letterheads/erik-personal.pdf` + auto-resolves CSS from `~/.letterhead/personal.css`
- `client-acme`: Uses fully custom paths for both letterhead and CSS files

### Configuration Flexibility

**Mix and Match Approach:**
- **Convention + Override**: Use standard location for letterhead, custom location for CSS
- **Partial Override**: Override just the letterhead or just the CSS
- **Full Override**: Specify both letterhead and CSS paths explicitly
- **Pure Convention**: Let everything auto-resolve from `~/.letterhead/`

**Example Use Cases:**
```json
{
  "mcpServers": {
    "shared-branding": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--name", "shared-branding",
        "--css", "/Volumes/SharedDrive/brand-assets/company.css"
      ],
      "description": "Company letterhead with shared network CSS"
    },
    "project-alpha": {
      "command": "uvx", 
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--name", "project-alpha",
        "--letterhead", "~/Projects/alpha/deliverables/letterhead.pdf"
      ],
      "description": "Project-specific letterhead, auto-CSS from ~/.letterhead/project-alpha.css"
    }
  }
}
```

### Configuration Parameters
- `--name`: Server name (auto-resolves `~/.letterhead/<name>.pdf` and `~/.letterhead/<name>.css`)
- `--letterhead`: (Optional) Override letterhead PDF path
- `--css`: (Optional) Override CSS file path

## Available Tools

### `create_letterhead_pdf`
Creates a letterheaded PDF from Markdown content.

**Parameters:**
- `markdown_content` (required): Markdown text to convert
- `letterhead_template` (optional): Template name or path (uses default if configured)
- `output_path` (optional): Where to save the PDF (temp file if not specified)
- `title` (optional): Document title for metadata
- `css_path` (optional): Custom CSS file path (uses default if configured)
- `strategy` (optional): Merge strategy (`darken`, `multiply`, `overlay`, etc.)

### `merge_letterhead_pdf`
Merges an existing PDF with a letterhead template.

**Parameters:**
- `input_pdf_path` (required): Path to the input PDF
- `letterhead_template` (optional): Template name or path (uses default if configured)
- `output_path` (optional): Where to save the merged PDF
- `strategy` (optional): Merge strategy

### `analyze_letterhead`
Analyzes a letterhead template to determine margins and printable areas.

**Parameters:**
- `letterhead_template` (optional): Template to analyze (uses default if configured)

### `list_letterhead_templates`
Lists available letterhead templates in the templates directory.

## Usage Examples

### With Claude Code
Once configured with named servers, you can ask Claude to create specific letterheaded documents:

```
Please create an easytocloud letterheaded PDF for a business proposal with the following content:
[your markdown content here]
```

```
Write an ISC letterheaded document about network security best practices.
```

```
Create a personal letterheaded PDF for my consulting contract.
```

Claude will automatically:
1. Identify which letterhead server to use based on your request
2. Generate the appropriate content
3. Use the correct MCP server to create the letterheaded PDF
4. Apply the associated letterhead template and CSS styling

## File Organization

### Convention-Based Setup (Recommended)
```bash
# Create the letterhead directory
mkdir -p ~/.letterhead

# Organize your files by name:
~/.letterhead/
├── easytocloud.pdf     # Letterhead template
├── easytocloud.css     # Optional custom CSS
├── isc.pdf             # Letterhead template  
├── isc.css             # Optional custom CSS
├── personal.pdf        # Letterhead template
└── personal.css        # Optional custom CSS
```

### Legacy Template Directory
Templates can also be placed in:
```
~/Documents/letterhead-templates/
```

Templates can be referenced by name (without .pdf extension) or full path.

## CSS Styling

Create custom CSS files to control the appearance of your Markdown content. The CSS will be applied before merging with the letterhead template.

Example CSS structure:
```css
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
}

h1 { font-size: 16pt; color: #333; }
h2 { font-size: 14pt; color: #666; }
```

## Requirements

- macOS (uses Quartz/CoreGraphics for PDF processing)  
- Python ≥3.10
- MCP client (like Claude Code)