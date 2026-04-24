"""
MarkdownProcessor — public API, unchanged from the original monolith.

Orchestrates: markdown parsing → HTML → margin analysis → PDF backend.
"""

import importlib.util
import logging
import os
import tempfile
from typing import Dict, Optional

import fitz  # PyMuPDF

from letterhead_pdf.markdown.html_cleaner import preprocess_markdown_indentation
from letterhead_pdf.markdown.pdf_analyzer import analyze_letterhead, analyze_page_regions
from letterhead_pdf.markdown.flowable_builder import build_styles, markdown_to_flowables
from letterhead_pdf.markdown import backends

# ---------------------------------------------------------------------------
# Module-level capability flags (evaluated once at import time)
# ---------------------------------------------------------------------------

try:
    import markdown as _markdown_mod
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logging.warning("Standard markdown module not available.")

PYCMARKGFM_AVAILABLE = importlib.util.find_spec("pycmarkgfm") is not None
if PYCMARKGFM_AVAILABLE:
    logging.info("pycmarkgfm available for GitHub Flavored Markdown support")

WEASYPRINT_AVAILABLE = False
if importlib.util.find_spec("weasyprint") is not None:
    try:
        dyld = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
        homebrew_lib = '/opt/homebrew/lib'
        if homebrew_lib not in dyld:
            os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = f"{homebrew_lib}:{dyld}" if dyld else homebrew_lib

        from weasyprint import HTML as _WP_HTML
        _WP_HTML(string="<html><body>Test</body></html>")
        WEASYPRINT_AVAILABLE = True
        logging.info("WeasyPrint is available and functional")
    except Exception as e:
        logging.warning(f"WeasyPrint installed but not functional: {e}. Using ReportLab fallback.")

PYGMENTS_AVAILABLE = False
if importlib.util.find_spec("pygments") is not None:
    try:
        from pygments import highlight  # noqa: F401
        from pygments.lexers import get_lexer_by_name  # noqa: F401
        from pygments.formatters import HtmlFormatter  # noqa: F401
        PYGMENTS_AVAILABLE = True
        logging.info("Pygments available for syntax highlighting")
    except ImportError:
        logging.warning("Pygments import failed — no syntax highlighting.")


# ---------------------------------------------------------------------------
# MarkdownProcessor
# ---------------------------------------------------------------------------

class MarkdownProcessor:
    """Convert Markdown files to PDF, respecting letterhead margins."""

    def __init__(self, use_gfm: Optional[bool] = None):
        if use_gfm is None:
            self.use_gfm = PYCMARKGFM_AVAILABLE
        else:
            self.use_gfm = bool(use_gfm) and PYCMARKGFM_AVAILABLE

        if self.use_gfm:
            logging.info("Using GitHub Flavored Markdown (pycmarkgfm) backend")
            self.md = None
        else:
            if not MARKDOWN_AVAILABLE:
                from letterhead_pdf.exceptions import MarkdownProcessingError
                raise MarkdownProcessingError(
                    "No markdown module available. Install with: uvx mac-letterhead[markdown]"
                )
            logging.info("Using standard markdown backend")
            import markdown as _md
            extensions = ['tables', 'fenced_code', 'footnotes', 'attr_list',
                          'def_list', 'abbr', 'sane_lists']
            if PYGMENTS_AVAILABLE:
                extensions.append('codehilite')
            self.md = _md.Markdown(extensions=extensions)

        self.styles = build_styles()
        self.temp_dir = None  # kept for API compatibility

    # ------------------------------------------------------------------
    # Public helpers (preserved for callers that use them directly)
    # ------------------------------------------------------------------

    def md_to_html(self, md_content: str) -> str:
        if self.use_gfm:
            import pycmarkgfm
            return pycmarkgfm.gfm_to_html(md_content)
        return self.md.convert(md_content)

    def analyze_page_regions(self, page) -> Dict:
        return analyze_page_regions(page)

    def analyze_letterhead(self, letterhead_path: str) -> Dict:
        return analyze_letterhead(letterhead_path)

    def setup_styles(self):
        self.styles = build_styles()

    # Expose lower-level helpers so existing tests that call them directly still work
    def preprocess_markdown_indentation(self, md_content: str) -> str:
        return preprocess_markdown_indentation(md_content)

    def markdown_to_flowables(self, html_content: str) -> list:
        return markdown_to_flowables(html_content, self.styles)

    def clean_html_for_reportlab(self, html_content: str) -> str:
        from letterhead_pdf.markdown.html_cleaner import clean_html_for_reportlab
        return clean_html_for_reportlab(html_content)

    def _enhance_gfm_task_lists_for_weasyprint(self, html_content: str) -> str:
        from letterhead_pdf.markdown.backends.weasyprint_backend import enhance_gfm_task_lists
        return enhance_gfm_task_lists(html_content)

    def _md_to_pdf_weasyprint(self, html_content, output_path, margins, page_size, css_path=None):
        backends.weasyprint_backend.render(html_content, output_path, margins, page_size, css_path)

    def _md_to_pdf_reportlab(self, html_content, output_path, margins, page_size):
        backends.reportlab_backend.render(html_content, output_path, margins, page_size)

    # ------------------------------------------------------------------
    # Core conversion
    # ------------------------------------------------------------------

    def md_to_pdf(self, md_path: str, output_path: str, letterhead_path: str,
                  css_path: str = None, save_html: str = None,
                  pdf_backend: str = 'auto') -> str:
        """Convert a Markdown file to PDF with margins derived from the letterhead."""
        logging.info(f"Converting markdown to PDF: {md_path} -> {output_path}")

        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            md_content = preprocess_markdown_indentation(md_content)
            html_content = self.md_to_html(md_content)
            logging.info("HTML generated using %s",
                         "GitHub Flavored Markdown" if self.use_gfm else "standard markdown")

            if save_html:
                with open(save_html, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logging.info(f"Saved intermediate HTML: {save_html}")

            doc = fitz.open(letterhead_path)
            try:
                regions = analyze_page_regions(doc[0])
                margins = analyze_letterhead(letterhead_path)
                page_size = regions['page_size']
            finally:
                doc.close()

            # Validate css_path before any backend dispatch so ValueError propagates clearly.
            if css_path is not None:
                home = os.path.realpath(os.path.expanduser("~"))
                resolved = os.path.realpath(os.path.abspath(css_path))
                if not resolved.startswith(home + os.sep) and resolved != home:
                    raise ValueError(
                        f"CSS path must be within the home directory: "
                        f"'{css_path}' resolves to '{resolved}'"
                    )

            # Resolve backend
            from letterhead_pdf.exceptions import PDFCreationError
            use_weasyprint = False
            if pdf_backend == 'weasyprint':
                if not WEASYPRINT_AVAILABLE:
                    raise PDFCreationError("WeasyPrint backend requested but not available")
                use_weasyprint = True
            elif pdf_backend == 'reportlab':
                use_weasyprint = False
            else:  # auto
                use_weasyprint = WEASYPRINT_AVAILABLE

            logging.info("Using %s for PDF generation", "WeasyPrint" if use_weasyprint else "ReportLab")

            with tempfile.TemporaryDirectory() as _tmpdir:
                tmp_pdf = os.path.join(_tmpdir, "converted.pdf")

                if use_weasyprint:
                    try:
                        self._md_to_pdf_weasyprint(html_content, tmp_pdf, margins, page_size, css_path)
                    except Exception as e:
                        logging.warning(f"WeasyPrint failed, falling back to ReportLab: {e}")
                        self._md_to_pdf_reportlab(html_content, tmp_pdf, margins, page_size)
                else:
                    self._md_to_pdf_reportlab(html_content, tmp_pdf, margins, page_size)

                pdf = fitz.open(tmp_pdf)
                try:
                    pdf.set_metadata({
                        'title': os.path.basename(md_path),
                        'author': 'Mac-letterhead',
                        'creator': 'Mac-letterhead',
                        'producer': 'Mac-letterhead',
                    })
                    pdf.save(output_path)
                finally:
                    pdf.close()

            return output_path

        except Exception as e:
            from letterhead_pdf.exceptions import MarkdownProcessingError
            error_msg = f"Error converting markdown to PDF: {e}"
            logging.error(error_msg)
            raise MarkdownProcessingError(error_msg) from e
