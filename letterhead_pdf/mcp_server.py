#!/usr/bin/env python3
"""
MCP Server for Mac-letterhead
Provides tools for creating letterheaded PDFs from Markdown content and merging PDFs with letterheads.
"""

import asyncio
import os
import sys
import tempfile
import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from letterhead_pdf.main import LetterheadPDF
from letterhead_pdf.markdown_processor import MarkdownProcessor, MARKDOWN_AVAILABLE
from letterhead_pdf.pdf_merger import PDFMerger
from letterhead_pdf.exceptions import PDFMergeError, PDFCreationError, MarkdownProcessingError
from letterhead_pdf.log_config import configure_logging, get_logger

# Disable console logging for MCP server to avoid interfering with JSON-RPC protocol
def configure_mcp_logging():
    """Configure logging for MCP server with file-only output"""
    # Remove all existing handlers that might write to stdout/stderr
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add only file handler
    try:
        from letterhead_pdf.log_config import LOG_FILE
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - MCP - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.INFO)
    except Exception:
        # If file logging fails, disable all logging to avoid stdout/stderr interference
        root_logger.setLevel(logging.CRITICAL + 1)

# Configure MCP-specific logging after all imports
configure_mcp_logging()
logger = get_logger(__name__)

# Suppress warnings that might interfere with MCP JSON-RPC protocol
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Initialize the MCP server - will be updated with actual name after parsing args
server = None

# Get letterhead, CSS, name, and output settings from command line arguments
DEFAULT_LETTERHEAD = None
DEFAULT_CSS = None
SERVER_NAME = "mcp-letterhead"
DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Desktop")
DEFAULT_OUTPUT_PREFIX = ""
LETTERHEAD_DIR = os.path.expanduser("~/.letterhead")

def setup_server_config(server_args=None):
    """Setup server configuration from provided arguments"""
    global DEFAULT_LETTERHEAD, DEFAULT_CSS, SERVER_NAME, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_PREFIX, server
    
    if server_args:
        # Use provided arguments
        if server_args.get('style'):
            SERVER_NAME = server_args['style']
            logger.info(f"Using style name: {SERVER_NAME}")
        if server_args.get('output_dir'):
            DEFAULT_OUTPUT_DIR = os.path.expanduser(server_args['output_dir'])
            logger.info(f"Using default output directory: {DEFAULT_OUTPUT_DIR}")
        if server_args.get('output_prefix'):
            DEFAULT_OUTPUT_PREFIX = server_args['output_prefix']
            logger.info(f"Using default output prefix: {DEFAULT_OUTPUT_PREFIX}")
    else:
        # Parse from sys.argv for backwards compatibility
        args = sys.argv[1:]
        for i, arg in enumerate(args):
            if arg == "--style" and i + 1 < len(args):
                SERVER_NAME = args[i + 1]
                logger.info(f"Using style name: {SERVER_NAME}")
            elif arg == "--output-dir" and i + 1 < len(args):
                DEFAULT_OUTPUT_DIR = os.path.expanduser(args[i + 1])
                logger.info(f"Using default output directory: {DEFAULT_OUTPUT_DIR}")
            elif arg == "--output-prefix" and i + 1 < len(args):
                DEFAULT_OUTPUT_PREFIX = args[i + 1]
                logger.info(f"Using default output prefix: {DEFAULT_OUTPUT_PREFIX}")

    # Resolve default files based on style name
    if SERVER_NAME != "mcp-letterhead":
        letterhead_path = os.path.join(LETTERHEAD_DIR, f"{SERVER_NAME}.pdf")
        if os.path.exists(letterhead_path):
            DEFAULT_LETTERHEAD = letterhead_path
            logger.info(f"Auto-resolved letterhead: {DEFAULT_LETTERHEAD}")
        else:
            logger.warning(f"Letterhead not found at: {letterhead_path}")
        
        css_path = os.path.join(LETTERHEAD_DIR, f"{SERVER_NAME}.css")
        if os.path.exists(css_path):
            DEFAULT_CSS = css_path
            logger.info(f"Auto-resolved CSS: {DEFAULT_CSS}")
        else:
            logger.info(f"No CSS file found at: {css_path} (optional)")

    # Initialize the MCP server with the parsed name
    global server
    server = Server(SERVER_NAME)
    
    # Re-register handlers with the new server instance
    register_handlers()

def register_handlers():
    """Register MCP server handlers"""
    global server
    if not server:
        return
    
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """List available tools"""
        # Determine if style parameter should be required based on server configuration
        has_server_style = SERVER_NAME != "mcp-letterhead"
        
        # Base properties for create_letterhead_pdf - ordered with mandatory parameters first
        create_pdf_properties = {
            "markdown_content": {
                "type": "string",
                "description": "Markdown content to convert to PDF"
            }
        }
        
        # Add style parameter as second parameter if no server style is configured (mandatory)
        if not has_server_style:
            create_pdf_properties["style"] = {
                "type": "string",
                "description": "Style name (resolves ~/.letterhead/<style>.pdf and ~/.letterhead/<style>.css)"
            }
        else:
            # For style-specific servers, letterhead_template is optional so add after optional params
            pass
        
        # Add optional parameters
        create_pdf_properties.update({
            "output_path": {
                "type": "string",
                "description": "Output path for the generated PDF (optional, defaults to configured output directory)"
            },
            "output_filename": {
                "type": "string",
                "description": "Output filename (optional, auto-generated if not provided)"
            },
            "title": {
                "type": "string",
                "description": "Document title for metadata (optional)"
            },
            "css_path": {
                "type": "string",
                "description": "Path to custom CSS file for styling (optional, uses style CSS if available)"
            },
            "strategy": {
                "type": "string",
                "enum": ["multiply", "reverse", "overlay", "transparency", "darken"],
                "description": "PDF merge strategy (optional, defaults to 'darken')"
            }
        })
        
        # For style-specific servers, add letterhead_template as optional parameter at the end
        if has_server_style:
            create_pdf_properties["letterhead_template"] = {
                "type": "string", 
                "description": "Letterhead template name (without .pdf) or full path to template PDF (optional, uses configured style if not provided)"
            }
        
        # Determine required fields
        create_pdf_required = ["markdown_content"]
        if not has_server_style:
            create_pdf_required.append("style")
        
        return [
            types.Tool(
                name="create_letterhead_pdf",
                description=f"Create a letterheaded PDF from Markdown content{' using the configured ' + SERVER_NAME + ' style' if has_server_style else ' with specified style'}",
                inputSchema={
                    "type": "object",
                    "properties": create_pdf_properties,
                    "required": create_pdf_required
                }
            ),
            types.Tool(
                name="merge_letterhead_pdf", 
                description=f"Merge an existing PDF with a letterhead template{' using the configured ' + SERVER_NAME + ' style' if has_server_style else ' with specified style'}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        **{
                            # Mandatory parameters first
                            "input_pdf_path": {
                                "type": "string",
                                "description": "Path to the input PDF file"
                            }
                        },
                        **({
                            # Style parameter as second mandatory parameter for generic servers
                            "style": {
                                "type": "string",
                                "description": "Style name (resolves ~/.letterhead/<style>.pdf and ~/.letterhead/<style>.css)"
                            }
                        } if not has_server_style else {}),
                        **{
                            # Optional parameters
                            "output_path": {
                                "type": "string", 
                                "description": "Output path for the merged PDF (optional, defaults to configured output directory)"
                            },
                            "output_filename": {
                                "type": "string",
                                "description": "Output filename (optional, auto-generated if not provided)"
                            },
                            "strategy": {
                                "type": "string",
                                "enum": ["multiply", "reverse", "overlay", "transparency", "darken"],
                                "description": "PDF merge strategy (optional, defaults to 'darken')"
                            }
                        },
                        **({
                            # For style-specific servers, letterhead_template is optional so add at the end
                            "letterhead_template": {
                                "type": "string",
                                "description": "Letterhead template name (without .pdf) or full path to template PDF (optional, uses configured style if not provided)"
                            }
                        } if has_server_style else {})
                    },
                    "required": ["input_pdf_path"] + (["style"] if not has_server_style else [])
                }
            ),
            types.Tool(
                name="analyze_letterhead",
                description=f"Analyze a letterhead template to determine margins and printable areas{' for the configured ' + SERVER_NAME + ' style' if has_server_style else ' for specified style'}",
                inputSchema={
                    "type": "object", 
                    "properties": ({
                        "style": {
                            "type": "string",
                            "description": "Style name (resolves ~/.letterhead/<style>.pdf) to analyze"
                        }
                    } if not has_server_style else {
                        "letterhead_template": {
                            "type": "string",
                            "description": "Letterhead template name (without .pdf) or full path to template PDF (optional, uses configured style if not provided)"
                        }
                    }),
                    "required": ["style"] if not has_server_style else []
                }
            ),
            types.Tool(
                name="list_letterhead_templates",
                description="List all available letterhead templates in the templates directory",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle tool calls"""
        try:
            if name == "create_letterhead_pdf":
                return await create_letterhead_pdf(**arguments)
            elif name == "merge_letterhead_pdf":
                return await merge_letterhead_pdf(**arguments)
            elif name == "analyze_letterhead":
                return await analyze_letterhead(**arguments)
            elif name == "list_letterhead_templates":
                return await list_letterhead_templates(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

# Setup server configuration
setup_server_config()

# Legacy templates directory - kept for backwards compatibility only
LEGACY_TEMPLATES_DIR = os.path.expanduser("~/Documents/letterhead-templates")

def ensure_templates_dir():
    """Ensure the letterhead directory exists"""
    os.makedirs(LETTERHEAD_DIR, exist_ok=True)
    return LETTERHEAD_DIR

def find_letterhead_templates() -> List[Dict[str, str]]:
    """Find available letterhead templates in ~/.letterhead"""
    templates = []
    letterhead_dir = ensure_templates_dir()
    
    if os.path.exists(letterhead_dir):
        for file in os.listdir(letterhead_dir):
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(letterhead_dir, file)
                templates.append({
                    "name": os.path.splitext(file)[0],
                    "path": full_path,
                    "filename": file
                })
    
    return templates

def generate_output_path(output_path: Optional[str] = None, output_filename: Optional[str] = None, 
                        title: Optional[str] = None, letterhead_name: Optional[str] = None) -> str:
    """Generate output path based on provided parameters and defaults"""
    
    logger.info(f"generate_output_path called with: output_path={output_path}, output_filename={output_filename}, title={title}, letterhead_name={letterhead_name}")
    logger.info(f"DEFAULT_OUTPUT_DIR={DEFAULT_OUTPUT_DIR}")
    
    # If full path provided, use it directly
    if output_path and os.path.isabs(output_path):
        logger.info(f"Using absolute output path: {output_path}")
        return os.path.expanduser(output_path)
    
    # Determine output directory
    if output_path:
        # output_path is treated as directory if not absolute
        output_dir = os.path.expanduser(output_path)
        logger.info(f"Using provided output directory: {output_dir}")
    else:
        # Use default output directory
        output_dir = DEFAULT_OUTPUT_DIR
        logger.info(f"Using default output directory: {output_dir}")
        
    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory created/verified: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise
    
    # Determine filename
    if output_filename:
        filename = output_filename
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
    else:
        # Auto-generate filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Build filename components
        components = []
        if DEFAULT_OUTPUT_PREFIX:
            components.append(DEFAULT_OUTPUT_PREFIX)
        if title:
            # Sanitize title for filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            components.append(safe_title)
        if letterhead_name:
            components.append(f"letterhead_{letterhead_name}")
        
        if not components:
            components.append("document")
            
        components.append(timestamp)
        filename = "_".join(components) + ".pdf"
    
    final_path = os.path.join(output_dir, filename)
    logger.info(f"Generated final output path: {final_path}")
    return final_path

def resolve_letterhead_path(letterhead_input: Optional[str] = None) -> str:
    """Resolve letterhead path from name, full path, or use default"""
    # Use default letterhead if no input provided
    if not letterhead_input:
        if DEFAULT_LETTERHEAD:
            if os.path.exists(DEFAULT_LETTERHEAD):
                return DEFAULT_LETTERHEAD
            else:
                raise FileNotFoundError(f"Default letterhead not found: {DEFAULT_LETTERHEAD}")
        else:
            raise ValueError("No letterhead specified and no default letterhead configured")
    
    # If it's already a full path, validate and return
    if os.path.isabs(letterhead_input) and os.path.exists(letterhead_input):
        return letterhead_input
    
    # If it's a template name, look for it in the letterhead directory
    letterhead_dir = ensure_templates_dir()
    
    # Try exact match first
    template_path = os.path.join(letterhead_dir, f"{letterhead_input}.pdf")
    if os.path.exists(template_path):
        return template_path
    
    # Try with the input as filename (with extension)
    if letterhead_input.lower().endswith('.pdf'):
        template_path = os.path.join(letterhead_dir, letterhead_input)
        if os.path.exists(template_path):
            return template_path
    
    # If nothing found, raise error
    available_templates = find_letterhead_templates()
    template_names = [t["name"] for t in available_templates]
    raise FileNotFoundError(
        f"Letterhead template '{letterhead_input}' not found. "
        f"Available templates: {', '.join(template_names) if template_names else 'None'}\n"
        f"Letterhead directory: {letterhead_dir}"
    )


async def create_letterhead_pdf(
    markdown_content: str, 
    letterhead_template: Optional[str] = None,
    output_path: Optional[str] = None,
    output_filename: Optional[str] = None,
    title: Optional[str] = None,
    css_path: Optional[str] = None,
    strategy: str = "darken",
    style: Optional[str] = None
) -> List[types.TextContent]:
    """Create a letterheaded PDF from Markdown content"""
    
    if not MARKDOWN_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Error: Markdown processing not available. Please install Mac-letterhead with Markdown support."
        )]
    
    try:
        # Determine which style/letterhead to use
        style_or_template = style or letterhead_template
        logger.info(f"Using style/template: {style_or_template} (from style param: {style is not None})")
        
        # Resolve letterhead template path
        letterhead_path = resolve_letterhead_path(style_or_template)
        
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as md_file:
            md_file.write(markdown_content)
            md_file_path = md_file.name
        
        # Generate output path
        letterhead_name = style or letterhead_template or SERVER_NAME
        output_path = generate_output_path(output_path, output_filename, title, letterhead_name)
        
        try:
            # Create the letterheaded PDF
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert markdown to PDF
                md_processor = MarkdownProcessor()
                temp_pdf = os.path.join(temp_dir, "converted.pdf")
                
                # Convert with proper CSS path handling - use style CSS, custom CSS, or default CSS
                if css_path:
                    css_to_use = css_path
                elif style and not DEFAULT_CSS:
                    # If style is provided but no server-level CSS, try to find style-specific CSS
                    style_css_path = os.path.join(LETTERHEAD_DIR, f"{style}.css")
                    css_to_use = style_css_path if os.path.exists(style_css_path) else None
                else:
                    css_to_use = DEFAULT_CSS
                
                css_path_expanded = os.path.expanduser(css_to_use) if css_to_use else None
                md_processor.md_to_pdf(md_file_path, temp_pdf, letterhead_path, css_path_expanded)
                
                # Merge with letterhead
                letterhead_pdf = LetterheadPDF(letterhead_path)
                letterhead_pdf.merge_pdfs(temp_pdf, output_path, strategy)
            
            result_text = f"Successfully created letterheaded PDF: {output_path}"
            if title:
                result_text += f"\nDocument title: {title}"
            if style:
                result_text += f"\nStyle used: {style}"
            else:
                result_text += f"\nLetterhead template: {letterhead_template or 'default'}"
            if css_to_use:
                result_text += f"\nCSS used: {css_to_use}"
            result_text += f"\nMerge strategy: {strategy}"
            
            logger.info(f"Created letterheaded PDF: {output_path}")
            
            return [types.TextContent(type="text", text=result_text)]
            
        finally:
            # Clean up temporary markdown file
            if os.path.exists(md_file_path):
                os.unlink(md_file_path)
                
    except FileNotFoundError as e:
        return [types.TextContent(type="text", text=f"File not found: {str(e)}")]
    except MarkdownProcessingError as e:
        return [types.TextContent(type="text", text=f"Markdown processing error: {str(e)}")]
    except PDFMergeError as e:
        return [types.TextContent(type="text", text=f"PDF merge error: {str(e)}")]
    except Exception as e:
        logger.error(f"Unexpected error in create_letterhead_pdf: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Unexpected error: {str(e)}")]

async def merge_letterhead_pdf(
    input_pdf_path: str,
    letterhead_template: Optional[str] = None, 
    output_path: Optional[str] = None,
    output_filename: Optional[str] = None,
    strategy: str = "darken",
    style: Optional[str] = None
) -> List[types.TextContent]:
    """Merge an existing PDF with a letterhead template"""
    
    try:
        # Expand and validate input path
        input_pdf_path = os.path.expanduser(input_pdf_path)
        if not os.path.exists(input_pdf_path):
            return [types.TextContent(
                type="text", 
                text=f"Input PDF not found: {input_pdf_path}"
            )]
        
        # Determine which style/letterhead to use
        style_or_template = style or letterhead_template
        logger.info(f"merge_letterhead_pdf using style/template: {style_or_template} (from style param: {style is not None})")
        
        # Resolve letterhead template path
        letterhead_path = resolve_letterhead_path(style_or_template)
        
        # Generate output path
        letterhead_name = style or letterhead_template or SERVER_NAME
        input_basename = os.path.splitext(os.path.basename(input_pdf_path))[0]
        output_path = generate_output_path(output_path, output_filename, input_basename, letterhead_name)
        
        # Merge PDFs
        letterhead_pdf = LetterheadPDF(letterhead_path)
        letterhead_pdf.merge_pdfs(input_pdf_path, output_path, strategy)
        
        result_text = f"Successfully merged PDF with letterhead: {output_path}"
        result_text += f"\nInput PDF: {input_pdf_path}"
        if style:
            result_text += f"\nStyle used: {style}"
        else:
            result_text += f"\nLetterhead template: {letterhead_template or 'default'}"
        result_text += f"\nMerge strategy: {strategy}"
        
        logger.info(f"Merged PDF with letterhead: {output_path}")
        
        return [types.TextContent(type="text", text=result_text)]
        
    except FileNotFoundError as e:
        return [types.TextContent(type="text", text=f"File not found: {str(e)}")]
    except PDFMergeError as e:
        return [types.TextContent(type="text", text=f"PDF merge error: {str(e)}")]
    except Exception as e:
        logger.error(f"Unexpected error in merge_letterhead_pdf: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Unexpected error: {str(e)}")]

async def analyze_letterhead(letterhead_template: Optional[str] = None, style: Optional[str] = None) -> List[types.TextContent]:
    """Analyze a letterhead template to determine margins and printable areas"""
    
    try:
        # Determine which style/letterhead to use
        style_or_template = style or letterhead_template
        logger.info(f"analyze_letterhead using style/template: {style_or_template} (from style param: {style is not None})")
        
        # Resolve letterhead template path
        letterhead_path = resolve_letterhead_path(style_or_template)
        
        # Analyze letterhead margins
        if MARKDOWN_AVAILABLE:
            md_processor = MarkdownProcessor()
            margins = md_processor.analyze_letterhead(letterhead_path)
            
            result = {
                "letterhead_template": style_or_template,
                "letterhead_path": letterhead_path,
                "margins": margins,
                "analysis": "Smart margin analysis completed using letterhead content detection"
            }
            
            result_text = f"Letterhead Analysis Results:\n"
            if style:
                result_text += f"Style: {style}\n"
            else:
                result_text += f"Template: {letterhead_template or 'default'}\n"
            result_text += f"Path: {letterhead_path}\n\n"
            result_text += f"First Page Margins:\n"
            result_text += f"  Top: {margins['first_page']['top']:.1f}pt\n"
            result_text += f"  Right: {margins['first_page']['right']:.1f}pt\n"
            result_text += f"  Bottom: {margins['first_page']['bottom']:.1f}pt\n"
            result_text += f"  Left: {margins['first_page']['left']:.1f}pt\n\n"
            result_text += f"Other Pages Margins:\n"
            result_text += f"  Top: {margins['other_pages']['top']:.1f}pt\n"
            result_text += f"  Right: {margins['other_pages']['right']:.1f}pt\n"
            result_text += f"  Bottom: {margins['other_pages']['bottom']:.1f}pt\n"
            result_text += f"  Left: {margins['other_pages']['left']:.1f}pt\n"
            
        else:
            result_text = f"Letterhead template found: {letterhead_path}\n"
            result_text += "Note: Detailed margin analysis requires Markdown support to be installed."
        
        logger.info(f"Analyzed letterhead template: {letterhead_path}")
        
        return [types.TextContent(type="text", text=result_text)]
        
    except FileNotFoundError as e:
        return [types.TextContent(type="text", text=f"File not found: {str(e)}")]
    except Exception as e:
        logger.error(f"Error analyzing letterhead: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Analysis error: {str(e)}")]

async def list_letterhead_templates(**kwargs) -> List[types.TextContent]:
    """List all available letterhead templates"""
    
    try:
        templates = find_letterhead_templates()
        templates_dir = ensure_templates_dir()
        
        if not templates:
            result_text = f"No letterhead templates found.\n"
            result_text += f"Templates directory: {templates_dir}\n"
            result_text += f"To add templates, place PDF files in the templates directory."
        else:
            result_text = f"Available Letterhead Templates ({len(templates)} found):\n"
            result_text += f"Templates directory: {templates_dir}\n\n"
            
            for template in templates:
                result_text += f"• {template['name']}\n"
                result_text += f"  File: {template['filename']}\n"
                result_text += f"  Path: {template['path']}\n\n"
        
        logger.info(f"Listed {len(templates)} letterhead templates")
        
        return [types.TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error listing templates: {str(e)}")]

async def main():
    """Main function to run the MCP server"""
    # Initialize the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

def run_mcp_server(server_args=None):
    """Run MCP server with provided arguments"""
    # Reset global state to ensure clean configuration
    global DEFAULT_LETTERHEAD, DEFAULT_CSS, SERVER_NAME, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_PREFIX, server
    DEFAULT_LETTERHEAD = None
    DEFAULT_CSS = None
    SERVER_NAME = "mcp-letterhead"
    DEFAULT_OUTPUT_DIR = os.path.expanduser("~/Desktop")
    DEFAULT_OUTPUT_PREFIX = ""
    server = None
    
    # Configure with new arguments
    setup_server_config(server_args)
    
    # Run the server
    try:
        asyncio.run(main())
        return 0
    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"MCP server error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(run_mcp_server())