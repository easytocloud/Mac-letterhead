"""
ReportLab PDF backend — fallback renderer when WeasyPrint is unavailable.
"""

import logging

from reportlab.platypus import SimpleDocTemplate

from letterhead_pdf.markdown.flowable_builder import build_styles, markdown_to_flowables


def render(html_content: str, output_path: str, margins: dict, page_size) -> None:
    """Render html_content to output_path as PDF using ReportLab."""
    logging.info("Using ReportLab for PDF generation")

    styles = build_styles()

    fp = margins['first_page']
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=fp['left'],
        rightMargin=fp['right'],
        topMargin=fp['top'],
        bottomMargin=fp['bottom'],
        allowSplitting=True,
        displayDocTitle=True,
        pageCompression=0,
    )

    flowables = markdown_to_flowables(html_content, styles)
    doc.build(flowables)
    logging.info(f"ReportLab wrote PDF: {output_path}")
