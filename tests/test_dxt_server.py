"""
Tests for the Desktop Extension (DXT) entry-point at dxt/server.py.

The DXT host in Claude for macOS is supposed to substitute
`${user_config.<field>}` placeholders in `mcp_config.env` before spawning
the process. In practice, when a user leaves a user_config field blank in
the Claude Desktop settings dialog AND the manifest has no `default`, the
placeholder may not be substituted at all — the literal string
`${user_config.style}` shows up in the environment. `_cleaned` in
`dxt/server.py` normalises that back to `None` so the MCP server treats
the field as "unconfigured" instead of trying to resolve
`~/.letterhead/${user_config.style}.pdf`, which obviously doesn't exist.

Regression tests for that normalisation. Not the whole `main()` flow —
just the pure function — so we can run without the mac-letterhead
package fully installed.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest


# dxt/server.py is not a package member — it lives outside letterhead_pdf/.
# Load it by path so the test can exercise it in isolation.
_SERVER_PY = pathlib.Path(__file__).resolve().parents[1] / "dxt" / "server.py"


@pytest.fixture(scope="module")
def dxt_server():
    spec = importlib.util.spec_from_file_location("dxt_server_under_test", _SERVER_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cleaned_returns_none_for_empty_string(dxt_server):
    assert dxt_server._cleaned("") is None


def test_cleaned_returns_none_for_none(dxt_server):
    assert dxt_server._cleaned(None) is None


def test_cleaned_returns_none_for_unresolved_user_config_placeholder(dxt_server):
    """
    Primary regression: some DXT hosts pass the literal template string when
    the user leaves the field blank in the Claude Desktop settings dialog and
    the manifest has no `default`. Treat it as unset.
    """
    assert dxt_server._cleaned("${user_config.style}") is None
    assert dxt_server._cleaned("${user_config.output_directory}") is None


def test_cleaned_passes_through_real_values(dxt_server):
    assert dxt_server._cleaned("easytocloud") == "easytocloud"
    assert dxt_server._cleaned("/Users/erik/Documents") == "/Users/erik/Documents"


def test_cleaned_does_not_strip_home_placeholder(dxt_server):
    """
    `${HOME}/Desktop` is a shell-style placeholder that may legitimately survive
    into the process env — some DXT hosts leave `${HOME}`-shaped placeholders
    for downstream expansion (main() handles that via expandvars). _cleaned's
    job is specifically to catch UNRESOLVED `${user_config.*}` placeholders,
    not every occurrence of `${...}`.
    """
    assert dxt_server._cleaned("${HOME}/Desktop") == "${HOME}/Desktop"


def test_cleaned_does_not_strip_placeholder_with_suffix(dxt_server):
    """
    `${user_config.style}-suffix` isn't the exact placeholder shape; it's user
    text that happens to reference a placeholder. Pass through unchanged so
    weird workflows (users composing values) still work.
    """
    assert dxt_server._cleaned("${user_config.style}-suffix") == "${user_config.style}-suffix"
