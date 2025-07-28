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

#### Generic Multi-Style Server
```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Generic letterhead PDF generator - style specified per tool call"
    }
  }
}
```

#### Single-Style Server  
```json
{
  "mcpServers": {
    "easytocloud-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "easytocloud"],
      "description": "EasyToCloud-specific letterhead PDF generator"
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
        "--style", "easytocloud",
        "--output-dir", "~/Documents/generated-pdfs"
      ],
      "description": "EasyToCloud letterhead PDF generator with auto-resolved style files"
    },
    "isc": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp", 
        "--style", "isc"
      ],
      "description": "ISC letterhead with auto-resolved PDF and CSS files"
    },
    "personal": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "personal",
        "--output-prefix", "Personal"
      ],
      "description": "Personal letterhead with custom prefix for output filenames"
    },
    "client-acme": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "client-acme"
      ],
      "description": "ACME Corp client letterhead with auto-resolved style files"
    }
  }
}
```

**Style File Resolution Examples:**
- `easytocloud`: Uses convention-based files `~/.letterhead/easytocloud.pdf` + `~/.letterhead/easytocloud.css`
- `isc`: Uses convention-based files `~/.letterhead/isc.pdf` + `~/.letterhead/isc.css` (if exists)
- `personal`: Uses convention-based files `~/.letterhead/personal.pdf` + `~/.letterhead/personal.css` (if exists)
- `client-acme`: Uses convention-based files `~/.letterhead/client-acme.pdf` + `~/.letterhead/client-acme.css` (if exists)

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
- `--style`: Style name (auto-resolves both `~/.letterhead/<style>.pdf` and `~/.letterhead/<style>.css`)
- `--output-dir`: (Optional) Default output directory (default: ~/Desktop)
- `--output-prefix`: (Optional) Prefix for auto-generated filenames

## Available Tools

### `create_letterhead_pdf`
Creates a letterheaded PDF from Markdown content.

**Parameters (vary based on server configuration):**

#### When server has NO style configured (generic server):
- `markdown_content` (required): Markdown text to convert
- `style` (required): Style name (resolves ~/.letterhead/<style>.pdf and .css)
- `output_path` (optional): Output directory or full path
- `output_filename` (optional): Specific filename (auto-generated with timestamp if not provided)
- `title` (optional): Document title for metadata and filename generation
- `css_path` (optional): Custom CSS file path (overrides style CSS)
- `strategy` (optional): Merge strategy (`darken`, `multiply`, `overlay`, etc.)

#### When server has style configured (dedicated server):
- `markdown_content` (required): Markdown text to convert
- `letterhead_template` (optional): Override template name or path (uses configured style if not provided)
- `output_path` (optional): Output directory or full path
- `output_filename` (optional): Specific filename (auto-generated with timestamp if not provided)
- `title` (optional): Document title for metadata and filename generation
- `css_path` (optional): Custom CSS file path (uses configured style CSS if not provided)
- `strategy` (optional): Merge strategy (`darken`, `multiply`, `overlay`, etc.)

### `merge_letterhead_pdf`
Merges an existing PDF with a letterhead template.

**Parameters (vary based on server configuration):**

#### When server has NO style configured (generic server):
- `input_pdf_path` (required): Path to the input PDF
- `style` (required): Style name (resolves ~/.letterhead/<style>.pdf)
- `output_path` (optional): Output directory or full path
- `output_filename` (optional): Specific filename (auto-generated with timestamp if not provided)
- `strategy` (optional): Merge strategy

#### When server has style configured (dedicated server):
- `input_pdf_path` (required): Path to the input PDF
- `letterhead_template` (optional): Override template name or path (uses configured style if not provided)
- `output_path` (optional): Output directory or full path
- `output_filename` (optional): Specific filename (auto-generated with timestamp if not provided)
- `strategy` (optional): Merge strategy

### `analyze_letterhead`
Analyzes a letterhead template to determine margins and printable areas.

**Parameters (vary based on server configuration):**

#### When server has NO style configured (generic server):
- `style` (required): Style name (resolves ~/.letterhead/<style>.pdf to analyze)

#### When server has style configured (dedicated server):
- `letterhead_template` (optional): Template to analyze (uses configured style if not provided)

### `list_letterhead_templates`
Lists available letterhead templates in the templates directory.

## Usage Examples

### With Generic Multi-Style Server
If you configured a generic server (no `--style` parameter), you can ask Claude to create documents with any available style:

```
Using the letterhead server, create a PDF with easytocloud style about cloud migration strategies.
```

```
Create a document using isc style about network security best practices.
```

```
Generate a personal style letterheaded PDF for my consulting contract.
```

### With Style-Specific Servers  
If you configured dedicated servers (with `--style` parameter), you can ask Claude to use specific servers:

```
Create an easytocloud letterheaded PDF about cloud migration strategies.
```

```
Write an ISC letterheaded document about network security best practices.
```

```
Create a personal letterheaded PDF for my consulting contract.
```

### How It Works
Claude will automatically:
1. **Generic Server**: Extract the style from your request and pass it as a parameter to the tools
2. **Dedicated Server**: Identify which letterhead server to use based on your request
3. Generate the appropriate content
4. Use the correct MCP server and style to create the letterheaded PDF
5. Apply the associated letterhead template and CSS styling

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