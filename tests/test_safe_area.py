"""
Tests for safe-area detection and preview rendering.

Covers the three-tier resolution introduced by pdf_analyzer:
  1. explicit annotation (highest priority)
  2. heuristic layout analysis
  3. fallback 1-inch margins

Plus a smoke test for the preview PDF renderer.
"""

from __future__ import annotations

import os
import tempfile

import fitz
import pytest

from letterhead_pdf.markdown.pdf_analyzer import (
    SAFE_AREA_LABELS,
    SafeAreaSource,
    analyze_letterhead,
    analyze_letterhead_detailed,
    analyze_page_safe_area,
    find_safe_area_annotation,
)
from letterhead_pdf.markdown.preview import render_safe_area_preview


# ---------- helpers -------------------------------------------------------


def _blank_page_pdf(path: str, page_count: int = 1, with_content: bool = False) -> str:
    """A minimal A4 PDF, optionally with some text so the heuristic detects content."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page(width=595, height=842)
        if with_content:
            # Text near the top → treated as a header region by the heuristic
            page.insert_text(fitz.Point(72, 60), f"COMPANY HEADER (page {i + 1})", fontsize=14)
            # Text near the bottom → footer region
            page.insert_text(fitz.Point(72, 800), f"footer line — page {i + 1}", fontsize=8)
    doc.save(path)
    doc.close()
    return path


def _annotated_page_pdf(path: str, label: str, rect: fitz.Rect) -> str:
    """A minimal A4 PDF with a single Square annotation carrying `label` as its contents."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    annot = page.add_rect_annot(rect)
    annot.set_info(content=label)
    annot.update()
    doc.save(path)
    doc.close()
    return path


# ---------- annotation lookup --------------------------------------------


@pytest.mark.parametrize("label", ["safe-area", "safe area", "Printable", "content area"])
def test_find_safe_area_annotation_detects_labels(label, tmp_path):
    """Any label from SAFE_AREA_LABELS (case-insensitive substring) is a match."""
    target = fitz.Rect(100, 200, 400, 700)
    pdf = _annotated_page_pdf(str(tmp_path / "annotated.pdf"), label, target)
    doc = fitz.open(pdf)
    try:
        found = find_safe_area_annotation(doc[0])
    finally:
        doc.close()
    assert found is not None
    # PyMuPDF's add_rect_annot inflates the stored rect by the border width
    # (defaults to ~1pt), so the readback differs by up to ~1pt in each direction.
    assert abs(found.x0 - target.x0) <= 1.5
    assert abs(found.y0 - target.y0) <= 1.5
    assert abs(found.x1 - target.x1) <= 1.5
    assert abs(found.y1 - target.y1) <= 1.5


def test_find_safe_area_annotation_non_matching_label_still_treated_as_single_square(tmp_path):
    """
    Even when the label doesn't match a SAFE_AREA_LABELS marker, a *lone* Square
    on the page is still treated as the safe area (rule 2 — Preview.app path).
    To avoid this treatment for a non-safe-area rectangle, the user needs to
    add a second Square (or delete the one they have).
    """
    pdf = _annotated_page_pdf(
        str(tmp_path / "irrelevant.pdf"),
        "review comment: check this",
        fitz.Rect(10, 20, 50, 60),
    )
    doc = fitz.open(pdf)
    try:
        found = find_safe_area_annotation(doc[0])
    finally:
        doc.close()
    # Single-square rule kicks in; the rect is returned.
    assert found is not None


def test_find_safe_area_annotation_single_unlabeled_square_is_used(tmp_path):
    """
    Preview.app can't write labeled annotations — it only draws Squares. When a
    page has exactly ONE Square annotation and none matches a safe-area label,
    treat it as the safe area anyway. This is the primary Preview.app workflow.
    """
    target = fitz.Rect(58, 117, 525, 694)  # roughly the ISC-safe.pdf rectangle
    pdf = _annotated_page_pdf(str(tmp_path / "preview-app.pdf"),
                              "",  # empty content, like Preview.app does
                              target)
    doc = fitz.open(pdf)
    try:
        found = find_safe_area_annotation(doc[0])
    finally:
        doc.close()
    assert found is not None
    assert abs(found.x0 - target.x0) <= 1.5
    assert abs(found.y1 - target.y1) <= 1.5


def test_find_safe_area_annotation_multiple_unlabeled_squares_are_ambiguous(tmp_path):
    """
    Two or more Square annotations without matching labels → ambiguous.
    Don't guess which is the safe area; fall through to the heuristic.
    """
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    for i in range(2):
        a = page.add_rect_annot(fitz.Rect(50 + 100 * i, 100, 100 + 100 * i, 200))
        a.update()
    pdf_path = str(tmp_path / "ambiguous.pdf")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    try:
        assert find_safe_area_annotation(doc[0]) is None
    finally:
        doc.close()


def test_find_safe_area_annotation_labeled_wins_over_unlabeled(tmp_path):
    """When both a labeled and an unlabeled Square exist, the labeled one wins."""
    labeled = fitz.Rect(100, 200, 400, 500)
    unlabeled = fitz.Rect(50, 50, 200, 200)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    a1 = page.add_rect_annot(labeled)
    a1.set_info(content="safe-area")
    a1.update()
    a2 = page.add_rect_annot(unlabeled)
    a2.update()
    pdf_path = str(tmp_path / "both.pdf")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    try:
        found = find_safe_area_annotation(doc[0])
    finally:
        doc.close()
    assert found is not None
    # Should be the labeled one, not the smaller unlabeled one
    assert abs(found.x0 - labeled.x0) <= 1.5
    assert abs(found.x1 - labeled.x1) <= 1.5


def test_find_safe_area_annotation_ignores_non_square_annots(tmp_path):
    """A text/note annotation labelled 'safe-area' isn't a rectangle — don't treat it as one."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text_annot = page.add_text_annot(fitz.Point(100, 100), "safe-area")
    text_annot.update()
    pdf_path = str(tmp_path / "text-note.pdf")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    try:
        assert find_safe_area_annotation(doc[0]) is None
    finally:
        doc.close()


def test_all_documented_labels_are_actually_matched(tmp_path):
    """Every SAFE_AREA_LABELS entry should be detected — guards against typos in the tuple."""
    for label in SAFE_AREA_LABELS:
        pdf = _annotated_page_pdf(
            str(tmp_path / f"lbl_{hash(label)}.pdf"),
            label,
            fitz.Rect(50, 50, 500, 800),
        )
        doc = fitz.open(pdf)
        try:
            assert find_safe_area_annotation(doc[0]) is not None, f"label '{label}' not detected"
        finally:
            doc.close()


# ---------- three-tier resolution ----------------------------------------


def test_analyze_page_safe_area_prefers_annotation_over_heuristic(tmp_path):
    """When both an annotation and content regions exist, annotation wins."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(72, 60), "HEADER", fontsize=14)
    page.insert_text(fitz.Point(72, 800), "footer", fontsize=8)
    annot_rect = fitz.Rect(80, 250, 500, 600)
    annot = page.add_rect_annot(annot_rect)
    annot.set_info(content="safe-area")
    annot.update()
    pdf_path = str(tmp_path / "both.pdf")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    try:
        info = analyze_page_safe_area(doc[0])
    finally:
        doc.close()
    assert info["source"] == SafeAreaSource.ANNOTATION.value
    assert abs(info["rect"].x0 - annot_rect.x0) <= 1.5
    assert abs(info["rect"].y0 - annot_rect.y0) <= 1.5


def test_analyze_page_safe_area_uses_heuristic_when_no_annotation(tmp_path):
    """Content present but no annotation → heuristic path."""
    pdf = _blank_page_pdf(str(tmp_path / "content.pdf"), with_content=True)
    doc = fitz.open(pdf)
    try:
        info = analyze_page_safe_area(doc[0])
    finally:
        doc.close()
    assert info["source"] == SafeAreaSource.HEURISTIC.value


def test_analyze_page_safe_area_falls_back_when_nothing_detected(tmp_path):
    """Truly blank page → fallback source."""
    pdf = _blank_page_pdf(str(tmp_path / "blank.pdf"), with_content=False)
    doc = fitz.open(pdf)
    try:
        info = analyze_page_safe_area(doc[0])
    finally:
        doc.close()
    assert info["source"] == SafeAreaSource.FALLBACK.value


# ---------- backwards compatibility --------------------------------------


def test_analyze_letterhead_still_returns_margin_only_shape(tmp_path):
    """Existing callers (MCP server, merge) expect {first_page, other_pages} with margin floats."""
    pdf = _blank_page_pdf(str(tmp_path / "compat.pdf"), page_count=2, with_content=True)
    result = analyze_letterhead(pdf)
    assert set(result.keys()) == {"first_page", "other_pages"}
    for page_type in ("first_page", "other_pages"):
        assert set(result[page_type].keys()) == {"top", "right", "bottom", "left"}
        for v in result[page_type].values():
            assert isinstance(v, (int, float))


def test_analyze_letterhead_detailed_surfaces_source_and_rect(tmp_path):
    """Detailed variant carries source + rect on top of the existing margin shape."""
    pdf = _blank_page_pdf(str(tmp_path / "detailed.pdf"), page_count=2, with_content=True)
    result = analyze_letterhead_detailed(pdf)
    for page_type in ("first_page", "other_pages"):
        info = result[page_type]
        assert info["source"] in {s.value for s in SafeAreaSource}
        assert isinstance(info["rect"], fitz.Rect)
        assert set(info["margins"].keys()) == {"top", "right", "bottom", "left"}


# ---- multi-page template semantics --------------------------------------


def test_analyze_letterhead_detailed_single_page_mirrors_other_pages(tmp_path):
    """1-page letterhead → other_pages is a copy of first_page. even/odd absent."""
    pdf = _blank_page_pdf(str(tmp_path / "1p.pdf"), page_count=1, with_content=True)
    result = analyze_letterhead_detailed(pdf)
    assert set(result.keys()) == {"first_page", "other_pages"}
    # Same values, but not the same object (deep-copied to avoid shared-mutation bugs).
    assert result["first_page"]["margins"] == result["other_pages"]["margins"]
    assert result["first_page"]["margins"] is not result["other_pages"]["margins"]


def test_analyze_letterhead_detailed_two_page_uses_page_two_for_others(tmp_path):
    """2-page letterhead → other_pages reflects letterhead page 2. No even/odd."""
    doc = fitz.open()
    doc.new_page(width=595, height=842)  # letterhead page 1 — blank
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(72, 60), "HEADER on page 2 only", fontsize=14)
    pdf_path = str(tmp_path / "2p.pdf")
    doc.save(pdf_path)
    doc.close()

    result = analyze_letterhead_detailed(pdf_path)
    assert set(result.keys()) == {"first_page", "other_pages"}
    # Page 1 has no content → fallback; page 2 has header → heuristic
    assert result["first_page"]["source"] == SafeAreaSource.FALLBACK.value
    assert result["other_pages"]["source"] == SafeAreaSource.HEURISTIC.value


def test_analyze_letterhead_detailed_three_page_exposes_even_and_odd(tmp_path):
    """
    3-page letterhead → keys include first_page, other_pages (=even_pages,
    for legacy callers), even_pages, and odd_pages. Letterhead page 2 becomes
    even_pages (applied to document pages 2, 4, 6…), page 3 becomes odd_pages
    (applied to 3, 5, 7…).
    """
    doc = fitz.open()
    doc.new_page(width=595, height=842)   # letterhead page 1 (title)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(72, 60), "EVEN-PAGE header", fontsize=14)   # → shifts safe area down
    p3 = doc.new_page(width=595, height=842)
    p3.insert_text(fitz.Point(72, 60), "ODD-PAGE header", fontsize=14)
    p3.insert_text(fitz.Point(72, 800), "odd footer", fontsize=8)          # → also shifts bottom
    pdf_path = str(tmp_path / "3p.pdf")
    doc.save(pdf_path)
    doc.close()

    result = analyze_letterhead_detailed(pdf_path)
    assert {"first_page", "other_pages", "even_pages", "odd_pages"} <= set(result.keys())

    # other_pages is a copy of even_pages (letterhead page 2) for legacy callers
    assert result["other_pages"]["margins"] == result["even_pages"]["margins"]
    # But it's a distinct dict so downstream mutation on one doesn't leak into the other
    assert result["other_pages"]["margins"] is not result["even_pages"]["margins"]

    # odd_pages carries its own margins block — not identity-shared with even_pages
    # (both may happen to produce the same numbers if the heuristic can't tell the
    # pages apart, but the dict is a fresh instance).
    assert result["odd_pages"]["margins"] is not result["even_pages"]["margins"]


def test_analyze_letterhead_legacy_still_returns_two_keys_for_multipage(tmp_path):
    """
    The legacy analyze_letterhead() shim now returns whatever detailed produces.
    For a 3-page letterhead the shim exposes 4 keys, but every dict is
    `{top,right,bottom,left}` floats — the shape existing callers iterate over.
    """
    doc = fitz.open()
    for i in range(3):
        p = doc.new_page(width=595, height=842)
        p.insert_text(fitz.Point(72, 60), f"HEAD {i}", fontsize=12)
    pdf_path = str(tmp_path / "3p-legacy.pdf")
    doc.save(pdf_path)
    doc.close()

    from letterhead_pdf.markdown.pdf_analyzer import analyze_letterhead
    result = analyze_letterhead(pdf_path)
    assert "first_page" in result
    assert "other_pages" in result
    for key, m in result.items():
        assert set(m.keys()) == {"top", "right", "bottom", "left"}
        for v in m.values():
            assert isinstance(v, (int, float))


# ---------- preview renderer smoke test ---------------------------------


def test_render_safe_area_preview_writes_valid_pdf(tmp_path):
    """render_safe_area_preview produces a readable PDF at the expected path."""
    src = _blank_page_pdf(str(tmp_path / "letterhead.pdf"), page_count=2, with_content=True)
    out = tmp_path / "preview.pdf"
    result_path = render_safe_area_preview(src, out)
    assert result_path == out
    assert out.exists()
    assert out.stat().st_size > 0

    # Verify it's a valid PDF with the same page count as the source
    doc = fitz.open(str(out))
    try:
        assert doc.page_count == 2
    finally:
        doc.close()


def test_render_safe_area_preview_defaults_output_path_next_to_source(tmp_path):
    """No output path given → writes <stem>-preview.pdf beside the source."""
    src = _blank_page_pdf(str(tmp_path / "corporate.pdf"), with_content=True)
    result_path = render_safe_area_preview(src, None)
    expected = tmp_path / "corporate-preview.pdf"
    assert result_path == expected
    assert expected.exists()


def test_render_safe_area_preview_rejects_missing_source(tmp_path):
    """Clear error for a source that doesn't exist."""
    with pytest.raises(FileNotFoundError):
        render_safe_area_preview(tmp_path / "does-not-exist.pdf", None)
