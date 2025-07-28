# LLM Installation Guide for Mac-letterhead

This guide provides installation instructions for using Mac-letterhead with various Large Language Models (LLMs) and AI assistants that support the Model Context Protocol (MCP).

## Supported LLMs and AI Assistants

Mac-letterhead's MCP server works with any AI assistant that supports the Model Context Protocol, including:

- **Claude Code** (Anthropic) - Full MCP support with JSON configuration
- **Claude Desktop** (Anthropic) - MCP integration through settings
- **OpenAI ChatGPT** - Through MCP-compatible clients
- **Other MCP-compatible LLMs** - Any client supporting Model Context Protocol

## Prerequisites

### System Requirements
- **macOS**: Required for PDF processing and droplet applications
- **Python**: 3.10 or higher
- **uv package manager**: Install with `pip install uv` if not available

### Install Mac-letterhead with MCP Support
```bash
# Install Mac-letterhead with MCP server capabilities
uvx install "mac-letterhead[mcp]"
```

### Optional: System Dependencies for Enhanced Rendering
For optimal Markdown-to-PDF conversion quality:
```bash
brew install pango cairo fontconfig freetype harfbuzz
```

## Setup Your Letterhead Files

### Organize Letterhead Templates
Create and organize your letterhead files in the standard directory:

```bash
# Create the letterhead directory
mkdir -p ~/.letterhead

# Example organization:
~/.letterhead/
├── company.pdf        # Corporate letterhead template
├── company.css        # Optional custom styling for company docs
├── personal.pdf       # Personal letterhead template
├── personal.css       # Optional styling for personal docs
├── client-acme.pdf    # Client-specific letterhead
└── technical.pdf      # Technical documentation letterhead
```

### Quick Setup Script
Use the provided setup script to create sample letterhead files:
```bash
# From the Mac-letterhead repository
./setup_letterheads.sh
```

## LLM-Specific Configuration

### Claude Code Configuration

Add the following to your Claude Code MCP configuration file (typically `~/.claude/mcp_settings.json`):

#### Option 1: Generic Multi-Style Server (Recommended)
```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Generic letterhead PDF generator - specify style per request"
    }
  }
}
```

**Usage with Claude Code:**
```
Using the letterhead server, create a company style PDF about our quarterly business report.
```

#### Option 2: Multiple Style-Specific Servers
```json
{
  "mcpServers": {
    "company-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "company"],
      "description": "Company letterhead PDF generator"
    },
    "personal-letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp", "--style", "personal"],
      "description": "Personal letterhead PDF generator"
    },
    "technical-docs": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp", 
        "--style", "technical",
        "--output-dir", "~/Documents/technical-docs"
      ],
      "description": "Technical documentation with custom output directory"
    }
  }
}
```

**Usage with Claude Code:**
```
Create a company letterheaded PDF about our new product launch.
Generate a personal letterheaded document for my consulting proposal.
Write technical documentation about our API integration.
```

### Claude Desktop Configuration

Add to your Claude Desktop settings file (typically `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "description": "Letterhead PDF generator for professional documents"
    }
  }
}
```

### Generic MCP Client Configuration

For other MCP-compatible clients, use this general configuration pattern:

```json
{
  "servers": {
    "letterhead": {
      "command": "uvx",
      "args": ["mac-letterhead[mcp]", "mcp"],
      "env": {},
      "description": "Professional letterhead PDF generation"
    }
  }
}
```

## Advanced Configuration Options

### Server Configuration Parameters

The MCP server supports various configuration options:

```bash
# Basic style-specific server
uvx mac-letterhead mcp --style company

# Server with custom output directory
uvx mac-letterhead mcp --style company --output-dir ~/Documents/generated-pdfs

# Server with custom filename prefix
uvx mac-letterhead mcp --style company --output-prefix "CompanyDocs"
```

### Multiple Servers for Different Use Cases

Configure multiple servers for different workflows:

```json
{
  "mcpServers": {
    "corporate-docs": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "company",
        "--output-dir", "~/Documents/Corporate",
        "--output-prefix", "Corp"
      ],
      "description": "Corporate document generation"
    },
    "client-deliverables": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "client-acme",
        "--output-dir", "~/Documents/Client-ACME",
        "--output-prefix", "ACME"
      ],
      "description": "ACME Corp client deliverables"
    },
    "personal-consulting": {
      "command": "uvx",
      "args": [
        "mac-letterhead[mcp]", "mcp",
        "--style", "personal",
        "--output-dir", "~/Documents/Consulting"
      ],
      "description": "Personal consulting documents"
    }
  }
}
```

## Available MCP Tools

Once configured, your LLM will have access to these tools:

### `create_letterhead_pdf`
- Converts Markdown content to letterheaded PDF
- Automatically applies letterhead template and CSS styling
- Supports custom titles, output paths, and merge strategies

### `merge_letterhead_pdf`
- Applies letterhead to existing PDF files
- Preserves original formatting while adding professional branding
- Multiple merge strategies for different letterhead designs

### `analyze_letterhead`
- Analyzes letterhead templates for margin detection
- Reports printable areas and layout recommendations
- Helps optimize content placement within letterhead design

### `list_letterhead_templates`
- Lists all available letterhead templates
- Shows template paths and associated CSS files
- Helps identify available styles for document generation

## Usage Examples

### With Generic Multi-Style Server

```
# Corporate documents
"Using the letterhead server, create a company style PDF about our Q4 financial results"

# Personal documents  
"Generate a personal style letterheaded PDF for my consulting contract proposal"

# Client-specific documents
"Create a client-acme style letterheaded document about the project timeline"
```

### With Style-Specific Servers

```
# Using dedicated corporate server
"Create a corporate letterheaded PDF summarizing our new product features"

# Using personal consulting server
"Generate a consulting proposal document for the cloud migration project"

# Using client deliverables server
"Write a technical specification document for the ACME integration"
```

### Advanced Usage

```
# Custom output location
"Create a company letterheaded PDF about security policies and save it to ~/Documents/Security/"

# Specific merge strategy
"Generate a personal letterheaded invoice using the overlay merge strategy"

# Analysis and optimization
"Analyze the company letterhead template to show the printable margins"
```

## Troubleshooting

### Common Issues

**Server Not Found**
- Verify Mac-letterhead is installed: `uvx list | grep mac-letterhead`
- Check MCP configuration syntax in your client's settings file
- Restart your LLM client after configuration changes

**Missing Letterhead Templates**
- Ensure PDF files exist in `~/.letterhead/`
- Check file permissions and paths
- Use `uvx mac-letterhead mcp --style <name>` to test server manually

**Permission Errors**
- Verify write permissions for output directories
- Check macOS privacy settings for file access
- Ensure the output directory exists

**PDF Quality Issues**
- Install system dependencies: `brew install pango cairo fontconfig freetype harfbuzz`
- Check CSS file syntax if using custom styling
- Use `analyze_letterhead` tool to verify template margins

### Log Files and Debugging

Monitor server activity:
```bash
# View MCP server logs
tail -f ~/Library/Logs/Mac-letterhead/letterhead.log

# Test server manually
uvx mac-letterhead mcp --style company
```

### Validation

Test your configuration:
```bash
# Test basic functionality
uvx mac-letterhead create_letterhead_pdf "# Test Document\nThis is a test." company ~/Desktop

# Test MCP server directly
uvx mac-letterhead mcp --style company --output-dir ~/Desktop
```

## Best Practices

### File Organization
- Use descriptive names for letterhead styles (`company`, `client-acme`, `technical`)
- Keep CSS files alongside letterhead PDFs with matching names
- Organize output directories by project or client

### LLM Interaction
- Be specific about letterhead styles when using generic servers
- Include context about document type and audience
- Mention preferred output locations when needed

### Security Considerations
- Store letterhead templates in the user directory (`~/.letterhead/`)
- Use appropriate file permissions for sensitive letterhead designs
- Consider separate servers for different security levels (internal vs. client-facing)

## Getting Help

- **Documentation**: See `README_MCP.md` for detailed MCP configuration
- **Issues**: Report problems at the Mac-letterhead GitHub repository
- **Logs**: Check `~/Library/Logs/Mac-letterhead/letterhead.log` for debugging information
- **Testing**: Use command-line tools to verify functionality before LLM integration