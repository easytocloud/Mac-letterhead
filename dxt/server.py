#!/usr/bin/env python3
"""
Desktop Extension (DXT) entry point for the Mac-letterhead MCP server.

The DXT host sets environment variables from user_config defined in manifest.json:
  LETTERHEAD_STYLE       → maps to --style (optional, enables style-specific mode)
  LETTERHEAD_OUTPUT_DIR  → maps to --output-dir (optional, defaults to ~/Desktop)

This script reads those env vars and delegates to the existing MCP server
implementation in mac-letterhead, which handles all tool registration,
letterhead resolution, and PDF generation.
"""

import os
import sys


def main() -> int:
    # Read user_config values injected by the DXT host as environment variables.
    # Empty string from unset user_config fields is treated as "not configured".
    style = os.environ.get("LETTERHEAD_STYLE") or None
    output_dir = os.environ.get("LETTERHEAD_OUTPUT_DIR") or None

    server_args: dict = {}
    if style:
        server_args["style"] = style
    if output_dir:
        server_args["output_dir"] = output_dir

    try:
        from letterhead_pdf.mcp_server import run_mcp_server
    except ImportError as exc:
        # Emit to stderr only — stdout is reserved for MCP JSON-RPC
        print(
            f"Failed to import mac-letterhead: {exc}\n"
            "Ensure mac-letterhead[mcp] is installed in this environment.",
            file=sys.stderr,
        )
        return 1

    return run_mcp_server(server_args if server_args else None)


if __name__ == "__main__":
    sys.exit(main())
