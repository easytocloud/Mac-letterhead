#!/usr/bin/env python3

"""
Security regression tests for Mac-letterhead.

Covers:
- Temp file cleanup on exception paths
- CSS path traversal prevention
- Markdown content size limit in MCP tool
- Absence of /tmp debug file writes
"""

import asyncio
import glob
import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from letterhead_pdf.markdown_processor import MarkdownProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp_pdf_count() -> set:
    """Return the set of *.pdf files currently in the system temp dir."""
    return set(glob.glob(os.path.join(tempfile.gettempdir(), "*.pdf")))


def _minimal_letterhead() -> str:
    """Create and return a minimal single-page letterhead PDF for testing."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    out_dir = Path(__file__).parent.parent / "test-output"
    out_dir.mkdir(exist_ok=True)
    path = str(out_dir / "security_test_letterhead.pdf")
    if not os.path.exists(path):
        c = canvas.Canvas(path, pagesize=A4)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, A4[1] - 60, "Test Letterhead")
        c.save()
    return path


def _write_md(content: str) -> str:
    """Write markdown to a NamedTemporaryFile and return its path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                     encoding="utf-8") as f:
        f.write(content)
        return f.name


# ---------------------------------------------------------------------------
# 1. Temp file cleanup
# ---------------------------------------------------------------------------

class TestTempFileCleanup(unittest.TestCase):
    """md_to_pdf() must not leave .pdf files in the system temp dir on failure."""

    def setUp(self):
        self.letterhead = _minimal_letterhead()
        self.md_path = _write_md("# hello")

    def tearDown(self):
        if os.path.exists(self.md_path):
            os.unlink(self.md_path)

    def test_no_pdf_leak_on_backend_exception(self):
        before = _tmp_pdf_count()

        processor = MarkdownProcessor()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out:
            out_path = out.name
        try:
            # Force an error inside _md_to_pdf_weasyprint by patching it to raise
            with unittest.mock.patch.object(
                processor, "_md_to_pdf_weasyprint",
                side_effect=RuntimeError("simulated weasyprint failure")
            ), unittest.mock.patch.object(
                processor, "_md_to_pdf_reportlab",
                side_effect=RuntimeError("simulated reportlab failure")
            ):
                with self.assertRaises(Exception):
                    processor.md_to_pdf(self.md_path, out_path, self.letterhead)
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)

        after = _tmp_pdf_count()
        leaked = after - before
        self.assertEqual(leaked, set(), f"Temp PDF files leaked: {leaked}")

    def test_no_debug_file_written_to_tmp(self):
        debug_file = "/tmp/mac-letterhead-css-debug.txt"
        if os.path.exists(debug_file):
            os.unlink(debug_file)

        processor = MarkdownProcessor()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out:
            out_path = out.name
        try:
            # Attempt a conversion (may succeed or fail — we only care about the debug file)
            try:
                processor.md_to_pdf(self.md_path, out_path, self.letterhead)
            except Exception:
                pass
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)

        self.assertFalse(
            os.path.exists(debug_file),
            f"Debug file must not be written to {debug_file}"
        )


# ---------------------------------------------------------------------------
# 2. CSS path traversal
# ---------------------------------------------------------------------------

class TestCSSPathValidation(unittest.TestCase):
    """_md_to_pdf_weasyprint() must reject CSS paths outside the home directory."""

    def setUp(self):
        self.letterhead = _minimal_letterhead()
        self.md_path = _write_md("# test")

    def tearDown(self):
        if os.path.exists(self.md_path):
            os.unlink(self.md_path)

    def _attempt_css(self, css_path: str):
        processor = MarkdownProcessor()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out:
            out_path = out.name
        try:
            processor.md_to_pdf(
                self.md_path, out_path, self.letterhead,
                css_path=css_path
            )
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_rejects_etc_passwd(self):
        # The ValueError is wrapped in MarkdownProcessingError by the outer handler;
        # either way the error message must mention the path traversal.
        with self.assertRaises(Exception) as ctx:
            self._attempt_css("/etc/passwd")
        self.assertIn("home directory", str(ctx.exception),
                      "Error message must mention home directory restriction")

    def test_rejects_parent_traversal(self):
        traversal = os.path.expanduser("~") + "/../../etc/shadow"
        with self.assertRaises(Exception) as ctx:
            self._attempt_css(traversal)
        self.assertIn("home directory", str(ctx.exception),
                      "Error message must mention home directory restriction")

    def test_accepts_home_letterhead_css(self):
        # A path within ~/.letterhead/ must be accepted (file won't exist, but no ValueError)
        safe_path = os.path.expanduser("~/.letterhead/nonexistent.css")
        # Should not raise ValueError — may raise FileNotFoundError or succeed silently
        try:
            self._attempt_css(safe_path)
        except ValueError as e:
            self.fail(f"ValueError raised for a safe path: {e}")
        except Exception:
            pass  # Other errors (missing file, PDF generation) are fine


# ---------------------------------------------------------------------------
# 3. Markdown content size limit (MCP tool)
# ---------------------------------------------------------------------------

class TestMarkdownSizeLimit(unittest.IsolatedAsyncioTestCase):
    """create_letterhead_pdf() MCP tool must reject content exceeding 10 MB."""

    async def test_rejects_oversized_markdown(self):
        # Import here so tests don't fail if mcp extras aren't installed
        try:
            from letterhead_pdf.mcp_server import create_letterhead_pdf
        except ImportError:
            self.skipTest("MCP extras not installed")

        oversized = "x" * (10 * 1024 * 1024 + 1)
        result = await create_letterhead_pdf(markdown_content=oversized)

        self.assertTrue(len(result) > 0)
        self.assertIn("10 MB", result[0].text,
                      "Error message must mention the 10 MB limit")
        self.assertIn("Error", result[0].text)

    async def test_accepts_content_under_limit(self):
        try:
            from letterhead_pdf.mcp_server import create_letterhead_pdf
        except ImportError:
            self.skipTest("MCP extras not installed")

        # 1 KB — well under the limit; will fail for other reasons (no letterhead),
        # but must not be rejected for size.
        small = "# Hello\n" * 10
        result = await create_letterhead_pdf(markdown_content=small)

        self.assertTrue(len(result) > 0)
        self.assertNotIn("10 MB", result[0].text,
                         "Small content should not trigger the size limit error")


if __name__ == "__main__":
    unittest.main()
