"""
PDF letterhead analysis — safe-area detection.

Extracted from MarkdownProcessor so the MCP server can call analyze_letterhead
without importing the full markdown/ReportLab stack.

Three-tier safe-area resolution (used by analyze_letterhead_detailed):

1. **Annotation** — a Square annotation the user drew in Preview.app (or any
   PDF editor) whose title/contents/subject contains one of SAFE_AREA_LABELS
   (case-insensitive). Highest priority — treated as explicit user intent.
2. **Heuristic** — the content-region layout analysis. Looks at text blocks,
   drawings, and images to identify header/footer/logo zones and derive a
   safe rectangle that avoids them.
3. **Fallback** — 1-inch margins on every side. Used when the heuristic finds
   no content regions at all (rare — a blank letterhead).

analyze_letterhead() preserves its existing return shape (just margins) so
existing callers (MCP server, merge command) keep working unchanged.
analyze_letterhead_detailed() surfaces the extra info (source + rect) needed
by the safe-area preview renderer.
"""

import logging
from enum import Enum
from typing import Dict, Optional

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4, LETTER


class SafeAreaSource(str, Enum):
    """Where the safe-area rectangle came from."""
    ANNOTATION = "annotation"
    HEURISTIC = "heuristic"
    FALLBACK = "fallback"


# Substrings that identify a safe-area annotation. Case-insensitive; matched
# against the annotation's title, contents, and subject. Users can label their
# rectangle with any of these.
SAFE_AREA_LABELS = (
    "safe-area", "safe area",
    "printable-area", "printable area", "printable",
    "content-area", "content area",
)


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

    # Header/footer bands. Widened to top/bottom third (was quarter) so that
    # wordmarks rendered *below* a logo — common on continuation-page
    # letterheads that render text as vector paths — still get classified as
    # header content rather than "middle" (i.e., inside the safe area).
    top_third = height / 3
    bottom_third = height * 2 / 3
    content_regions = []

    for block in page.get_text("dict")["blocks"]:
        if "lines" in block:
            rect = fitz.Rect(block["bbox"])
            cy = (rect.y0 + rect.y1) / 2
            region = "header" if cy < top_third else ("footer" if cy > bottom_third else "middle")
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
        region = "header" if cy < top_third else ("footer" if cy > bottom_third else "middle")
        content_regions.append((region, rect))
        logging.info(f"Drawing {region}: {rect}")

    for img in page.get_images():
        for image_rect in page.get_image_rects(img[0]):
            cy = (image_rect.y0 + image_rect.y1) / 2
            region = "header" if cy < top_third else ("footer" if cy > bottom_third else "middle")
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


def find_safe_area_annotation(page) -> Optional[fitz.Rect]:
    """
    Look for a Square annotation on this page marking the user's safe area.

    Two rules, in order:

    1. Labeled — any Square annotation whose title/contents/subject contains
       one of SAFE_AREA_LABELS wins. This is the explicit, unambiguous case.
    2. Single unlabeled Square — if the page has exactly ONE Square annotation
       and none matched rule 1, we treat it as the safe area regardless of
       label. This accommodates macOS Preview.app, which lets users draw a
       rectangle but only exposes an "annotation author" field (auto-filled
       with the macOS user name) — there is no way to type an arbitrary label
       in Preview. Two or more unlabeled squares are ambiguous, so we fall
       through to the heuristic and log a warning; if the user wants a
       specific one used they can add a matching label using a proper PDF
       editor, or delete the others.

    Returns the rect if found, else None.
    """
    try:
        annots = list(page.annots() or [])
    except Exception:
        annots = []

    squares = []
    for annot in annots:
        try:
            type_name = annot.type[1] if isinstance(annot.type, tuple) else str(annot.type)
        except Exception:
            continue
        if type_name.lower() != "square":
            continue
        squares.append(annot)

    if not squares:
        return None

    # Rule 1: any Square whose label matches SAFE_AREA_LABELS wins.
    for annot in squares:
        info = annot.info or {}
        label = " ".join(filter(None, [
            info.get("title", ""),
            info.get("content", ""),
            info.get("subject", ""),
        ])).lower()
        if any(marker in label for marker in SAFE_AREA_LABELS):
            logging.info(f"Found labeled safe-area annotation: {annot.rect}")
            return fitz.Rect(annot.rect)

    # Rule 2: exactly one Square, no matching label → treat as safe area
    # (Preview.app workflow: no way to type a label there).
    if len(squares) == 1:
        logging.info(
            f"Found single unlabeled Square annotation, treating as safe area "
            f"(Preview.app convention): {squares[0].rect}"
        )
        return fitz.Rect(squares[0].rect)

    # Multiple unlabeled squares — ambiguous, don't guess.
    logging.warning(
        f"Found {len(squares)} unlabeled Square annotations on this page; "
        f"none matched a safe-area label. Ignoring all — add a label containing "
        f"one of {list(SAFE_AREA_LABELS)}, or leave only one rectangle on the "
        f"page. Falling back to layout heuristic."
    )
    return None


def _margins_from_rect(rect: fitz.Rect, page_rect: fitz.Rect) -> Dict[str, float]:
    """Convert a safe-area rect into the {top,right,bottom,left} margin format."""
    return {
        'top':    max(0.0, rect.y0),
        'left':   max(0.0, rect.x0),
        'right':  max(0.0, page_rect.width - rect.x1),
        'bottom': max(0.0, page_rect.height - rect.y1),
    }


def _rect_from_margins(margins: Dict[str, float], page_rect: fitz.Rect) -> fitz.Rect:
    """Inverse of _margins_from_rect."""
    return fitz.Rect(
        margins['left'],
        margins['top'],
        page_rect.width - margins['right'],
        page_rect.height - margins['bottom'],
    )


# Heuristic safety padding — added to top and bottom of the heuristic-detected
# safe area. 40pt gives visible breathing room between letterhead content and
# the safe area even when the boundary analysis under-corrects (e.g. on
# continuation pages where wordmarks render as many tiny vector paths that
# individually fall under the ≥5×5-pt content threshold). Annotation-sourced
# areas are trusted verbatim — no padding applied.
HEURISTIC_TOP_BOTTOM_PADDING = 40


def analyze_page_safe_area(page) -> Dict:
    """
    Resolve the safe area for a single page. Returns:
        {'source': SafeAreaSource value,
         'rect':   fitz.Rect,
         'margins': {'top', 'right', 'bottom', 'left'}}

    Three tiers:
      1. explicit annotation drawn by the user (highest priority, no padding)
      2. heuristic layout analysis (with HEURISTIC_TOP_BOTTOM_PADDING applied)
      3. fallback default margins (only if the heuristic finds no content at all)
    """
    page_rect = page.rect

    # 1. Explicit annotation
    annot_rect = find_safe_area_annotation(page)
    if annot_rect is not None:
        return {
            'source': SafeAreaSource.ANNOTATION.value,
            'rect':   annot_rect,
            'margins': _margins_from_rect(annot_rect, page_rect),
        }

    # 2/3. Heuristic (or fallback if no content regions)
    regions = analyze_page_regions(page)
    margins = _calculate_smart_margins(regions, page_rect)
    source = (SafeAreaSource.HEURISTIC
              if regions.get('content_regions')
              else SafeAreaSource.FALLBACK)

    # Apply safety padding to heuristic results only. Fallback margins are the
    # generous 1-inch defaults already; no further padding needed there.
    if source == SafeAreaSource.HEURISTIC:
        margins['top']    += HEURISTIC_TOP_BOTTOM_PADDING
        margins['bottom'] += HEURISTIC_TOP_BOTTOM_PADDING

    rect = _rect_from_margins(margins, page_rect)
    return {
        'source': source.value,
        'rect':   rect,
        'margins': margins,
    }


def analyze_letterhead_detailed(letterhead_path: str) -> Dict[str, Dict]:
    """
    Rich variant of analyze_letterhead. Returns one entry per applicable page
    position, each with `{'source', 'rect', 'margins'}`.

    Multi-page letterhead template semantics (matches the feature documented in
    the README):

      1-page letterhead → every document page uses the letterhead's page-1
        safe area. Result: `{'first_page': X, 'other_pages': X (copy)}`.
      2-page letterhead → document page 1 uses letterhead page 1, all others
        use letterhead page 2. Result: `{'first_page': X, 'other_pages': Y}`.
      3-page letterhead → document page 1 uses letterhead page 1 (title),
        even document pages (2, 4, 6…) use letterhead page 2, odd document
        pages (3, 5, 7…) use letterhead page 3. Result:
        `{'first_page': X, 'other_pages': Y  (== even_pages, for legacy
          callers), 'even_pages': Y, 'odd_pages': Z}`.

    `other_pages` is always populated for back-compat with the legacy
    `analyze_letterhead()` shape — legacy callers that only understand
    first/other pages will apply the page-2-of-letterhead margins to
    everything after page 1, which is the right degradation.

    'margins' has the same shape as analyze_letterhead()'s return value.
    'rect' is a fitz.Rect for the safe area on the page.
    'source' is one of SafeAreaSource values: 'annotation' | 'heuristic' | 'fallback'.
    """
    logging.info(f"Analyzing letterhead safe areas: {letterhead_path}")
    doc = None
    try:
        doc = fitz.open(letterhead_path)

        # Empty-doc fallback — an all-zero safe area on both positions, so
        # calling code doesn't crash.
        def _zero():
            return {'source': SafeAreaSource.FALLBACK.value,
                    'rect':   fitz.Rect(0, 0, 0, 0),
                    'margins': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}}

        if doc.page_count == 0:
            return {'first_page': _zero(), 'other_pages': _zero()}

        # Deep-copy helper — the rect and margins dict are mutable; sharing
        # the same objects across page-type keys is a subtle-bug generator.
        def _dup(info):
            return {'source':  info['source'],
                    'rect':    fitz.Rect(info['rect']),
                    'margins': dict(info['margins'])}

        first = analyze_page_safe_area(doc[0])
        result = {'first_page': first}

        if doc.page_count == 1:
            # single-page template — everything mirrors page 1
            result['other_pages'] = _dup(first)
        elif doc.page_count == 2:
            # two-page template — page 2 of the template applies to all
            # non-first document pages
            result['other_pages'] = analyze_page_safe_area(doc[1])
        else:
            # three-or-more-page template — page 2 → even document pages,
            # page 3 → odd document pages (page 1 handled by `first_page`).
            # Any pages beyond the third in the letterhead template are
            # ignored (we've never advertised support for that).
            even = analyze_page_safe_area(doc[1])
            odd  = analyze_page_safe_area(doc[2])
            result['other_pages'] = _dup(even)   # legacy back-compat: use page 2 as the "everything after first" bucket
            result['even_pages']  = even
            result['odd_pages']   = odd

        # analyze_page_safe_area already applies HEURISTIC_TOP_BOTTOM_PADDING —
        # no aggregate-level adjustment needed here anymore.
        for page_type, info in result.items():
            logging.info(f"{page_type}: source={info['source']} rect={info['rect']} margins={info['margins']}")
        return result

    except Exception as e:
        from letterhead_pdf.exceptions import MarkdownProcessingError
        raise MarkdownProcessingError(f"Error analyzing letterhead safe areas: {e}") from e
    finally:
        if doc is not None:
            doc.close()


def analyze_letterhead(letterhead_path: str) -> Dict[str, Dict[str, float]]:
    """
    Analyze a letterhead PDF and return safe printable margins for first/other pages.

    Backwards-compatible shim over analyze_letterhead_detailed — returns only the
    margin numbers so existing callers (MCP server, PDF merger) keep working
    unchanged. New callers that need source info or the safe-area rect should
    use analyze_letterhead_detailed() directly.
    """
    detailed = analyze_letterhead_detailed(letterhead_path)
    return {page_type: info['margins'] for page_type, info in detailed.items()}
