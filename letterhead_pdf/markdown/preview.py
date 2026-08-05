"""
Safe-area visualization for letterhead PDFs.

Given a letterhead PDF, produce a preview PDF that overlays cut marks + a
subtle tint + a source label around each page's safe area. Purely a design-time
aid — the actual letterhead used for merging is unchanged.

Colour code:
  - Green (annotation)   — user drew an explicit safe-area rectangle
  - Slate blue (heuristic) — auto-detected from letterhead content layout
  - Amber (fallback)     — heuristic found no content; using 1-inch defaults

Users normally invoke this via `mac-letterhead preview <letterhead.pdf>`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import fitz  # PyMuPDF

from .pdf_analyzer import analyze_page_safe_area, SafeAreaSource

# RGB in 0-1 space; PyMuPDF conventions.
RGB = Tuple[float, float, float]

# Palette per source. `tint` gets applied to the safe area fill (very low alpha
# so the letterhead artwork underneath stays legible). `stroke` is used for
# the cut marks and label; more saturated so it reads at any zoom.
SOURCE_STYLES = {
    SafeAreaSource.ANNOTATION.value: {
        'tint':          (0.13, 0.77, 0.37),   # forest green
        'tint_opacity':  0.06,
        'stroke':        (0.03, 0.47, 0.22),
        'label':         'from annotation',
    },
    SafeAreaSource.HEURISTIC.value: {
        'tint':          (0.36, 0.51, 0.71),   # slate blue
        'tint_opacity':  0.06,
        'stroke':        (0.19, 0.29, 0.44),
        'label':         'auto-detected',
    },
    SafeAreaSource.FALLBACK.value: {
        'tint':          (0.96, 0.62, 0.04),   # amber
        'tint_opacity':  0.08,
        'stroke':        (0.55, 0.35, 0.02),
        'label':         'fallback default',
    },
}

# Cut mark geometry.
CUT_MARK_LENGTH = 12.0    # points; ~4mm at 72 DPI
CUT_MARK_WEIGHT = 0.75    # line width
LABEL_FONT_SIZE = 8.0
LABEL_OFFSET_Y = 12.0     # points below the safe-area bottom edge


def _draw_cut_marks(shape: fitz.Shape, rect: fitz.Rect, colour: RGB) -> None:
    """Draw four L-shaped cut marks, one at each corner of `rect`."""
    L = CUT_MARK_LENGTH
    for corner, dx, dy in [
        (rect.tl, +1, +1),   # top-left: extend right and down
        (rect.tr, -1, +1),   # top-right: extend left and down
        (rect.bl, +1, -1),   # bottom-left: extend right and up
        (rect.br, -1, -1),   # bottom-right: extend left and up
    ]:
        # Horizontal leg
        shape.draw_line(fitz.Point(corner.x, corner.y),
                        fitz.Point(corner.x + dx * L, corner.y))
        # Vertical leg
        shape.draw_line(fitz.Point(corner.x, corner.y),
                        fitz.Point(corner.x, corner.y + dy * L))
    shape.finish(color=colour, width=CUT_MARK_WEIGHT)


def _draw_tint_fill(shape: fitz.Shape, rect: fitz.Rect, colour: RGB, opacity: float) -> None:
    """Draw a subtle translucent fill over the safe area."""
    shape.draw_rect(rect)
    shape.finish(color=None, fill=colour, fill_opacity=opacity, width=0)


def _draw_label(page: fitz.Page, rect: fitz.Rect, text: str, colour: RGB) -> None:
    """Write a compact source label just below the safe-area bottom-left corner."""
    page.insert_text(
        fitz.Point(rect.x0, min(rect.y1 + LABEL_OFFSET_Y, page.rect.height - 4)),
        text,
        fontsize=LABEL_FONT_SIZE,
        fontname="helv",
        color=colour,
    )


def render_safe_area_preview(letterhead_path: str | Path,
                              output_path: str | Path | None = None) -> Path:
    """
    Render a preview PDF that overlays safe-area cut marks + tint + label on
    every page of `letterhead_path`.

    If `output_path` is None, writes to `<letterhead_stem>-preview.pdf` next to
    the source. Returns the resolved output path.
    """
    letterhead_path = Path(letterhead_path).expanduser().resolve()
    if not letterhead_path.exists():
        raise FileNotFoundError(f"Letterhead not found: {letterhead_path}")

    if output_path is None:
        output_path = letterhead_path.with_name(f"{letterhead_path.stem}-preview.pdf")
    else:
        output_path = Path(output_path).expanduser().resolve()

    logging.info(f"Rendering safe-area preview: {letterhead_path} -> {output_path}")

    doc = fitz.open(letterhead_path)
    try:
        for page_index, page in enumerate(doc):
            info = analyze_page_safe_area(page)
            rect = info['rect']
            source = info['source']
            style = SOURCE_STYLES[source]

            # Order matters: draw the tint first (behind), then cut marks, then label.
            shape = page.new_shape()
            _draw_tint_fill(shape, rect, style['tint'], style['tint_opacity'])
            shape.commit()

            shape = page.new_shape()
            _draw_cut_marks(shape, rect, style['stroke'])
            shape.commit()

            label = f"SAFE AREA · {style['label']}  ({rect.width:.0f} × {rect.height:.0f} pt)"
            _draw_label(page, rect, label, style['stroke'])

            logging.info(f"  page {page_index + 1}: {source} rect={rect}")

        doc.save(str(output_path))
    finally:
        doc.close()

    return output_path
