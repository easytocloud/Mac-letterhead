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

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

from letterhead_pdf.main import LetterheadPDF
from letterhead_pdf.markdown_processor import MarkdownProcessor, MARKDOWN_AVAILABLE
from letterhead_pdf.markdown.pdf_analyzer import analyze_letterhead as _analyze_letterhead_margins
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

    # Initialize the MCP server with the parsed name and handlers (MCP 2.0 constructor API)
    global server
    server = Server(
        SERVER_NAME,
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )

async def handle_list_tools(ctx, params) -> types.ListToolsResult:
    """List available tools"""
    tools = _build_tools()
    return types.ListToolsResult(tools=tools)


def _build_tools() -> List[types.Tool]:
    """Build the tool schemas based on current server configuration."""
    # Determine if style parameter should be required based on server configuration
    has_server_style = SERVER_NAME != "mcp-letterhead"

    # Base properties for create_letterhead_pdf - ordered with mandatory parameters first
    create_pdf_properties = {
        "markdown_content": {
            "type": "string",
            "description": "Markdown content to convert to PDF"
        }
    }

    if not has_server_style:
        create_pdf_properties["style"] = {
            "type": "string",
            "description": "Style name (resolves ~/.letterhead/<style>.pdf and ~/.letterhead/<style>.css)"
        }

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

    if has_server_style:
        create_pdf_properties["letterhead_template"] = {
            "type": "string",
            "description": "Letterhead template name (without .pdf) or full path to template PDF (optional, uses configured style if not provided)"
        }

    create_pdf_required = ["markdown_content"]
    if not has_server_style:
        create_pdf_required.append("style")

    return [
        types.Tool(
            name="create_letterhead_pdf",
            description=(
                f"Create a letterheaded PDF from Markdown content"
                f"{' using the configured ' + SERVER_NAME + ' style' if has_server_style else ' with specified style'}."
                "\n\n"
                "# Optional: YAML front matter\n"
                "The `markdown_content` MAY begin with a YAML front-matter block — three "
                "dashes on their own line, key/value pairs, three dashes again — declaring "
                "per-document options. Example:\n"
                "\n"
                "```\n"
                "---\n"
                "title: Q3 Investor Update\n"
                "page-numbers: alternate\n"
                "author: Erik\n"
                "---\n"
                "\n"
                "# Q3 Investor Update\n"
                "\n"
                "Executive summary...\n"
                "```\n"
                "\n"
                "## When to include front matter\n"
                "Default to NOT including front matter. Add it only when a specific field "
                "materially improves the document. Rules of thumb:\n"
                "- `title` — helpful when the tool call's title parameter is not set, since it "
                "  drives the PDF metadata and the auto-generated filename.\n"
                "- `page-numbers` — omit for short documents (1–2 pages, memos, letters). "
                "  Include only when the document is long enough that a reader will need to "
                "  reference a page (multi-page reports, printed proposals). Use `alternate` "
                "  ONLY for booklet-style output where the letterhead has a distinct title / "
                "  left-hand / right-hand page design.\n"
                "- `blend-strategy` — omit unless the default `darken` produces poor "
                "  contrast with the letterhead in question and the user has asked for a "
                "  different strategy.\n"
                "- `author`, `subject` — include when the user's request contains a clear "
                "  author name or subject line worth preserving in the PDF metadata.\n"
                "- `style` — normally not needed; the tool's `style` parameter is the right "
                "  place to specify a letterhead style. Front-matter `style:` is silently "
                "  ignored on style-bound servers.\n"
                "\n"
                "## Field reference\n"
                "- `title` (string) — PDF title + filename generation\n"
                "- `output-dir` (path, supports `~`) — where to write the PDF\n"
                "- `page-numbers` — one of: `bottom-right`, `bottom-center`, `bottom-left`, "
                "`alternate`. Omit to disable page numbers entirely (the default).\n"
                "- `blend-strategy` — one of: `darken`, `multiply`, `overlay`, "
                "`transparency`, `reverse`\n"
                "- `style` (string) — letterhead style; server-bound value wins when the "
                "server was started with `--style`.\n"
                "- `author`, `subject` (string) — PDF metadata\n"
                "\n"
                "Explicit tool parameters ALWAYS override the corresponding front-matter "
                "field, so it is safe to include front matter even when the user also "
                "passes the value as an argument — the argument wins."
            ),
            inputSchema={
                "type": "object",
                "properties": create_pdf_properties,
                "required": create_pdf_required
            },
            annotations=types.ToolAnnotations(
                title="Print Markdown onto Letterhead",
                read_only_hint=False,
                destructive_hint=False,
                idempotent_hint=False,
                open_world_hint=False,
            ),
        ),
        types.Tool(
            name="merge_letterhead_pdf",
            description=f"Merge an existing PDF with a letterhead template{' using the configured ' + SERVER_NAME + ' style' if has_server_style else ' with specified style'}",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_pdf_path": {
                        "type": "string",
                        "description": "Path to the input PDF file"
                    },
                    **({
                        "style": {
                            "type": "string",
                            "description": "Style name (resolves ~/.letterhead/<style>.pdf and ~/.letterhead/<style>.css)"
                        }
                    } if not has_server_style else {}),
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
                    },
                    **({
                        "letterhead_template": {
                            "type": "string",
                            "description": "Letterhead template name (without .pdf) or full path to template PDF (optional, uses configured style if not provided)"
                        }
                    } if has_server_style else {})
                },
                "required": ["input_pdf_path"] + (["style"] if not has_server_style else [])
            },
            annotations=types.ToolAnnotations(
                title="Print PDF onto Letterhead",
                read_only_hint=False,
                destructive_hint=False,
                idempotent_hint=False,
                open_world_hint=False,
            ),
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
            },
            annotations=types.ToolAnnotations(
                title="Analyze Letterhead Template",
                read_only_hint=True,
                idempotent_hint=True,
                open_world_hint=False,
            ),
        ),
        types.Tool(
            name="list_letterhead_templates",
            description="List all available letterhead templates in the templates directory",
            inputSchema={
                "type": "object",
                "properties": {}
            },
            annotations=types.ToolAnnotations(
                title="List Letterhead Templates",
                read_only_hint=True,
                idempotent_hint=True,
                open_world_hint=False,
            ),
        )
    ]


async def handle_call_tool(ctx, params) -> types.CallToolResult:
    """Handle tool calls (MCP 2.0 constructor-based dispatcher)"""
    name = params.name
    arguments = params.arguments or {}
    try:
        if name == "create_letterhead_pdf":
            content = await create_letterhead_pdf(**arguments)
        elif name == "merge_letterhead_pdf":
            content = await merge_letterhead_pdf(**arguments)
        elif name == "analyze_letterhead":
            content = await analyze_letterhead(**arguments)
        elif name == "list_letterhead_templates":
            content = await list_letterhead_templates(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        return types.CallToolResult(content=content)
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}", exc_info=True)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Error: {str(e)}")],
            is_error=True,
        )

# Don't call setup_server_config() here - it needs to be called with proper arguments
# after run_mcp_server() is invoked. This avoids premature server initialization.

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

    _MAX_MARKDOWN_BYTES = 10 * 1024 * 1024  # 10 MB
    if len(markdown_content.encode()) > _MAX_MARKDOWN_BYTES:
        return [types.TextContent(
            type="text",
            text=f"Error: markdown_content exceeds the 10 MB limit ({len(markdown_content.encode()):,} bytes)."
        )]

    if not MARKDOWN_AVAILABLE:
        return [types.TextContent(
            type="text",
            text="Error: Markdown processing not available. Please install Mac-letterhead with Markdown support."
        )]
    
    try:
        # Parse any YAML front matter at the top of `markdown_content` and resolve
        # per-document overrides. `explicit` tool arguments always win; anything
        # not passed by the caller falls through to front matter, then to server
        # defaults. `style` obeys the dedicated-server-wins rule: if this MCP
        # server was launched with --style, front-matter `style:` is ignored.
        from letterhead_pdf.markdown.front_matter import parse as parse_fm, resolve as resolve_fm, page_numbers_css
        fm_dict, body = parse_fm(markdown_content)
        # `strategy` has a default of "darken" in the MCP tool signature — treat
        # that as "not explicitly passed" so front-matter blend-strategy can win.
        strategy_was_default = (strategy == "darken")
        server_bound = SERVER_NAME  # non-None on style-specific servers
        resolved = resolve_fm(
            fm_dict,
            explicit={
                "title":          title,
                "output-dir":     None,                # not directly exposed as MCP arg; deferred
                "blend-strategy": None if strategy_was_default else strategy,
                "style":          style,               # explicit style trumps front matter
                "author":         None,
                "subject":        None,
            },
            server_bound_style=server_bound,
        )

        # Determine which style/letterhead to use — front matter can now steer it,
        # bounded by the server-bound rule above.
        effective_style = resolved.style if not server_bound else server_bound
        style_or_template = effective_style or letterhead_template
        logger.info(
            f"Using style/template: {style_or_template} "
            f"(from style param: {style is not None}, from front matter: {'style' in fm_dict})"
        )

        # Resolve letterhead template path
        letterhead_path = resolve_letterhead_path(style_or_template)

        # title falls back to front matter → filename generation
        effective_title = resolved.title or title

        # Generate output path (front-matter output-dir would override the server
        # default here in a future iteration; deferred for now to keep this change
        # focused on formatting, not filesystem routing.)
        letterhead_name = effective_style or letterhead_template or SERVER_NAME
        output_path = generate_output_path(output_path, output_filename, effective_title, letterhead_name)

        # Merge strategy: front-matter blend-strategy overrides the default; explicit tool arg wins.
        effective_strategy = resolved.blend_strategy or strategy

        # TemporaryDirectory covers both the markdown temp file and the converted PDF;
        # cleanup is guaranteed even if an exception is raised during conversion.
        with tempfile.TemporaryDirectory() as temp_dir:
            md_file_path = os.path.join(temp_dir, "input.md")
            with open(md_file_path, 'w', encoding='utf-8') as md_file:
                md_file.write(body)   # front-matter-stripped body only

            # Convert markdown to PDF
            md_processor = MarkdownProcessor()
            temp_pdf = os.path.join(temp_dir, "converted.pdf")

            # CSS resolution: explicit > style-specific > server default
            if css_path:
                css_to_use = css_path
            elif effective_style and not DEFAULT_CSS:
                style_css_path = os.path.join(LETTERHEAD_DIR, f"{effective_style}.css")
                css_to_use = style_css_path if os.path.exists(style_css_path) else None
            else:
                css_to_use = DEFAULT_CSS

            css_path_expanded = os.path.expanduser(css_to_use) if css_to_use else None

            # Front-matter page-numbers → CSS injection (WeasyPrint only).
            injected_css = page_numbers_css(resolved.page_numbers)
            if injected_css:
                user_css_text = ""
                if css_path_expanded and os.path.exists(css_path_expanded):
                    with open(css_path_expanded, 'r', encoding='utf-8') as f:
                        user_css_text = f.read()
                effective_css_path = os.path.join(temp_dir, "effective.css")
                with open(effective_css_path, 'w', encoding='utf-8') as f:
                    f.write(injected_css + "\n" + user_css_text)
                css_path_expanded = effective_css_path

            md_processor.md_to_pdf(md_file_path, temp_pdf, letterhead_path, css_path_expanded)

            # Merge with letterhead
            letterhead_pdf = LetterheadPDF(letterhead_path)
            letterhead_pdf.merge_pdfs(temp_pdf, output_path, effective_strategy)

        result_text = f"Successfully created letterheaded PDF: {output_path}"
        if title:
            result_text += f"\nDocument title: {effective_title}"
        if effective_style:
            result_text += f"\nStyle used: {effective_style}"
        else:
            result_text += f"\nLetterhead template: {letterhead_template or 'default'}"
        if css_to_use:
            result_text += f"\nCSS used: {css_to_use}"
        result_text += f"\nMerge strategy: {effective_strategy}"
        if resolved.sources:
            fm_sourced = [f"{k}={fm_dict[k]}" for k in resolved.sources if resolved.sources[k] == "front-matter"]
            if fm_sourced:
                result_text += f"\nFrom front matter: {', '.join(fm_sourced)}"
        if resolved.page_numbers:
            result_text += f"\nPage numbers: {resolved.page_numbers}"

        logger.info(f"Created letterheaded PDF: {output_path}")

        return [types.TextContent(type="text", text=result_text)]

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
        
        # Analyze letterhead margins — uses pdf_analyzer directly, no markdown stack needed
        if True:
            margins = _analyze_letterhead_margins(letterhead_path)
            
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
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
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