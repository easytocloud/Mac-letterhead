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
import re
import sys


# Match a bare `${user_config.<name>}` placeholder — nothing else. The `<name>`
# is the manifest field key. Anything outside this exact shape (embedded
# placeholders, other `${...}` schemes like `${HOME}`, real strings) passes
# through unchanged.
_USER_CONFIG_PLACEHOLDER = re.compile(r'^\$\{user_config\.[^}]+\}$')


def _cleaned(val):
    """
    Normalise a user_config-derived env var to `None` when the DXT host didn't
    substitute a resolved value.

    Two cases produce a placeholder value at runtime:
      1. The user left the field blank and the manifest has no `default` — some
         DXT hosts pass `""` (falsy), others pass the literal template string
         `${user_config.<field>}` (truthy!). We need to catch both.
      2. The DXT host is a version that doesn't expand `${user_config.*}` at
         all — same literal-string outcome.

    We deliberately only strip `${user_config.*}` — other shell-style
    placeholders such as `${HOME}/Desktop` (which appears as the manifest
    default for the output directory) pass through untouched, and the calling
    code expands them via os.path.expanduser / expandvars.
    """
    if not val:
        return None
    if _USER_CONFIG_PLACEHOLDER.match(val):
        return None
    return val


def main() -> int:
    # Read user_config values injected by the DXT host as environment variables.
    # Both empty strings and unresolved `${user_config.*}` placeholders count as
    # "not configured" — the latter shows up when the user leaves the field
    # blank in Claude Desktop and the manifest has no default.
    style = _cleaned(os.environ.get("LETTERHEAD_STYLE"))
    output_dir = _cleaned(os.environ.get("LETTERHEAD_OUTPUT_DIR"))
    # Expand shell-style placeholders (e.g. `${HOME}/Desktop`) that some DXT
    # hosts leave for downstream expansion. os.path.expandvars is a no-op for
    # values that don't reference env vars, so this is safe when the value is
    # already an absolute path.
    if output_dir:
        output_dir = os.path.expandvars(os.path.expanduser(output_dir))

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
