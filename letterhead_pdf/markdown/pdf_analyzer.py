"""
PDF letterhead analysis — margin and printable-area detection.

Extracted from MarkdownProcessor so the MCP server can call analyze_letterhead
without importing the full markdown/ReportLab stack.
"""

import logging
from typing import Dict

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4, LETTER


def analyze_page_regions(page) -> Dict:
    """Analyze a page to detect all content regions and page size."""
    page_rect = page.rect
    width = page_rect.width
    height = page_rect.height

    if abs(width - 595) <= 1 and abs(height - 842) <= 1:
        page_size = A4
    elif abs(width - 612) <= 1 and abs(height - 792) <= 1:
        page_size = LETTER
    else:
        page_size = A4
        logging.info(f"Non-standard page size ({width}x{height}), defaulting to A4")

    top_quarter = height / 4
    bottom_quarter = height * 3 / 4
    content_regions = []

    for block in page.get_text("dict")["blocks"]:
        if "lines" in block:
            rect = fitz.Rect(block["bbox"])
            cy = (rect.y0 + rect.y1) / 2
            region = "header" if cy < top_quarter else ("footer" if cy > bottom_quarter else "middle")
            content_regions.append((region, rect))
            logging.info(f"Text {region}: {rect}")

    page_area = width * height
    for drawing in page.get_drawings():
        rect = fitz.Rect(drawing["rect"])
        if rect.width < 5 or rect.height < 5:
            continue
        area_pct = (rect.width * rect.height / page_area) * 100
        if area_pct > 80:
            logging.info(f"Skipping large background drawing ({area_pct:.1f}%): {rect}")
            continue
        if (rect.width / width) * 100 > 90 and (rect.height / height) * 100 > 90:
            logging.info(f"Skipping full-page drawing: {rect}")
            continue
        cy = (rect.y0 + rect.y1) / 2
        region = "header" if cy < top_quarter else ("footer" if cy > bottom_quarter else "middle")
        content_regions.append((region, rect))
        logging.info(f"Drawing {region}: {rect}")

    for img in page.get_images():
        for image_rect in page.get_image_rects(img[0]):
            cy = (image_rect.y0 + image_rect.y1) / 2
            region = "header" if cy < top_quarter else ("footer" if cy > bottom_quarter else "middle")
            content_regions.append((region, image_rect))
            logging.info(f"Image {region}: {image_rect}")

    header_rect = footer_rect = middle_rect = None
    for region, rect in content_regions:
        if region == "header":
            header_rect = header_rect.include_rect(rect) if header_rect else rect
        elif region == "footer":
            footer_rect = footer_rect.include_rect(rect) if footer_rect else rect
        elif region == "middle":
            middle_rect = middle_rect.include_rect(rect) if middle_rect else rect

    return {
        'header': header_rect,
        'footer': footer_rect,
        'middle': middle_rect,
        'content_regions': content_regions,
        'page_rect': page_rect,
        'page_size': page_size,
        'width': width,
        'height': height,
    }


def _adjust_printable_area(printable_rect: fitz.Rect, content_rect: fitz.Rect,
                            page_rect: fitz.Rect) -> fitz.Rect:
    """Nudge printable_rect to avoid content_rect, preserving the largest area."""
    safe_padding = 20
    adjustments = []

    if content_rect.x1 + safe_padding < page_rect.width * 0.8:
        r = fitz.Rect(max(printable_rect.x0, content_rect.x1 + safe_padding),
                      printable_rect.y0, printable_rect.x1, printable_rect.y1)
        if r.width > 0:
            adjustments.append(r)

    if content_rect.x0 - safe_padding > page_rect.width * 0.2:
        r = fitz.Rect(printable_rect.x0, printable_rect.y0,
                      min(printable_rect.x1, content_rect.x0 - safe_padding), printable_rect.y1)
        if r.width > 0:
            adjustments.append(r)

    if content_rect.y1 + safe_padding < page_rect.height * 0.8:
        r = fitz.Rect(printable_rect.x0, max(printable_rect.y0, content_rect.y1 + safe_padding),
                      printable_rect.x1, printable_rect.y1)
        if r.height > 0:
            adjustments.append(r)

    if content_rect.y0 - safe_padding > page_rect.height * 0.2:
        r = fitz.Rect(printable_rect.x0, printable_rect.y0,
                      printable_rect.x1, min(printable_rect.y1, content_rect.y0 - safe_padding))
        if r.height > 0:
            adjustments.append(r)

    if adjustments:
        best = max(adjustments, key=lambda r: r.width * r.height)
        logging.info(f"Adjusted printable area: {printable_rect} -> {best}")
        return best
    return printable_rect


def _calculate_smart_margins(regions: Dict, page_rect) -> Dict[str, float]:
    """Derive safe document margins from the letterhead content layout."""
    content_regions = regions.get('content_regions', [])
    default_margin = 72   # 1 inch
    min_margin = 36       # 0.5 inch
    page_width = page_rect.width
    page_height = page_rect.height

    printable_rect = fitz.Rect(default_margin, default_margin,
                                page_width - default_margin, page_height - default_margin)
    logging.info(f"Initial printable area: {printable_rect}")

    for region_type, content_rect in content_regions:
        if printable_rect.intersects(content_rect):
            logging.info(f"Content overlaps printable area: {region_type} at {content_rect}")
            printable_rect = _adjust_printable_area(printable_rect, content_rect, page_rect)

    min_width = page_width * 0.3
    min_height = page_height * 0.3
    if printable_rect.width < min_width or printable_rect.height < min_height:
        logging.warning(f"Printable area too small ({printable_rect.width:.0f}x{printable_rect.height:.0f}), using centred fallback")
        cx, cy = page_width / 2, page_height / 2
        printable_rect = fitz.Rect(cx - min_width / 2, cy - min_height / 2,
                                    cx + min_width / 2, cy + min_height / 2)

    left   = max(min_margin, printable_rect.x0)
    top    = max(min_margin, printable_rect.y0)
    right  = max(min_margin, page_width  - printable_rect.x1)
    bottom = max(min_margin, page_height - printable_rect.y1)

    pw = page_width - left - right
    ph = page_height - top - bottom
    pct = pw * ph / (page_width * page_height) * 100
    logging.info(f"Final printable area: {pw:.1f}x{ph:.1f}pt ({pct:.1f}%)")
    logging.info(f"Margins: top={top:.1f}, right={right:.1f}, bottom={bottom:.1f}, left={left:.1f}")

    return {'top': top, 'right': right, 'bottom': bottom, 'left': left}


def analyze_letterhead(letterhead_path: str) -> Dict[str, Dict[str, float]]:
    """Analyze a letterhead PDF and return safe printable margins for first/other pages."""
    logging.info(f"Analyzing letterhead margins: {letterhead_path}")
    doc = None
    try:
        doc = fitz.open(letterhead_path)
        margins = {
            'first_page':  {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
            'other_pages': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
        }
        if doc.page_count > 0:
            regions = analyze_page_regions(doc[0])
            page_rect = regions['page_rect']
            margins['first_page'] = _calculate_smart_margins(regions, page_rect)
            if doc.page_count > 1:
                regions2 = analyze_page_regions(doc[1])
                margins['other_pages'] = _calculate_smart_margins(regions2, page_rect)
            else:
                margins['other_pages'] = margins['first_page'].copy()

        for page_type in margins:
            margins[page_type]['top']    += 20
            margins[page_type]['bottom'] += 20

        logging.info(f"First-page margins: {margins['first_page']}")
        logging.info(f"Other-page margins: {margins['other_pages']}")
        return margins

    except Exception as e:
        from letterhead_pdf.exceptions import MarkdownProcessingError
        raise MarkdownProcessingError(f"Error analyzing letterhead margins: {e}") from e
    finally:
        if doc is not None:
            doc.close()
