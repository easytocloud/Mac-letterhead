"""
letterhead_pdf.markdown — modular markdown-to-PDF pipeline.

Public re-exports so that ``from letterhead_pdf.markdown import MarkdownProcessor``
works, and capability flags are accessible from the package root.
"""

from letterhead_pdf.markdown.processor import (  # noqa: F401
    MarkdownProcessor,
    MARKDOWN_AVAILABLE,
    PYCMARKGFM_AVAILABLE,
    WEASYPRINT_AVAILABLE,
    PYGMENTS_AVAILABLE,
)

from letterhead_pdf.markdown import backends  # noqa: F401
