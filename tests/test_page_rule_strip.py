"""
Regression tests for the CSS `@page` sanitiser in the WeasyPrint backend.

Backstory: the sanitiser used to be a naive regex that stripped *every*
`@page { ... }` rule from user CSS to prevent margin conflicts with the
letterhead-derived margins we apply later. That regex also chewed up
`@page { @bottom-right { content: counter(page); } }` — the block front-
matter `page-numbers:` injects — and had trouble with nested braces to
boot.

The new sanitiser keeps `@page` blocks whose body contains only margin-
boxes (`@bottom-right`, `@top-left`, etc.) and drops the ones that carry
`margin-*` declarations. These tests pin that behaviour so we don't
accidentally regress if the sanitiser gets rewritten.
"""

from letterhead_pdf.markdown.backends.weasyprint_backend import (
    _build_page_margin_css,
    _strip_page_rules_with_margins,
)


# ---- multi-page margin emission ----------------------------------------


def test_build_page_margin_css_two_page_template_emits_first_and_default():
    """
    2-page letterhead → CSS must map document page 1 to letterhead page 1's
    safe area and every subsequent document page to letterhead page 2's.
    Regression: through 0.24.1 the backend only emitted margins for
    `first_page`, so continuation pages inherited page-1 margins and content
    overflowed the real safe area. Especially visible when a user drew a
    tight Preview.app rectangle on page 2 of the letterhead.
    """
    margins = {
        'first_page':  {'top': 100, 'right': 50, 'bottom': 120, 'left': 60},
        'other_pages': {'top': 40,  'right': 70, 'bottom': 90,  'left': 200},
    }
    css = _build_page_margin_css(margins)

    # Four blocks now: :first, :left, :right, and default @page fallback.
    assert "@page :first" in css
    assert "@page :left"  in css
    assert "@page :right" in css
    # Default block matches the last "@page {" (no selector between @page and {).
    # For 2-page templates :left/:right also carry other_pages margins so
    # WeasyPrint applies page 2's margins to every non-first page regardless
    # of even/odd.
    first_section  = css.split("@page :left")[0]
    left_section   = css.split("@page :left")[1].split("@page :right")[0]
    right_section  = css.split("@page :right")[1].split("@page {")[0]
    assert "margin-top: 100pt" in first_section
    assert "margin-left: 60pt" in first_section
    for section, name in [(left_section, "left"), (right_section, "right")]:
        assert "margin-top: 40pt" in section, f"{name} block should use other_pages top"
        assert "margin-left: 200pt" in section, f"{name} block should use other_pages left"


def test_build_page_margin_css_three_page_template_uses_left_right_split():
    """
    3-page letterhead → letterhead page 1 goes to `:first`, page 2 to `:left`
    (even document pages), page 3 to `:right` (odd document pages > 1).
    """
    margins = {
        'first_page':  {'top': 100, 'right': 50, 'bottom': 120, 'left': 60},
        'other_pages': {'top': 40,  'right': 70, 'bottom': 90,  'left': 200},   # legacy back-compat
        'even_pages':  {'top': 40,  'right': 70, 'bottom': 90,  'left': 200},
        'odd_pages':   {'top': 55,  'right': 85, 'bottom': 65,  'left': 45},
    }
    css = _build_page_margin_css(margins)

    left_section  = css.split("@page :left")[1].split("@page :right")[0]
    right_section = css.split("@page :right")[1].split("@page {")[0]

    # :left carries even_pages margins
    assert "margin-top: 40pt"  in left_section
    assert "margin-left: 200pt" in left_section

    # :right carries odd_pages margins (distinct from :left)
    assert "margin-top: 55pt"  in right_section
    assert "margin-left: 45pt" in right_section


def test_build_page_margin_css_single_page_all_selectors_share_margins():
    """1-page letterhead → every selector applies the same margins so all
    document pages get consistent letterhead treatment."""
    margins = {
        'first_page':  {'top': 80, 'right': 60, 'bottom': 80, 'left': 60},
        'other_pages': {'top': 80, 'right': 60, 'bottom': 80, 'left': 60},
    }
    css = _build_page_margin_css(margins)
    # 4 blocks × 4 margin lines = 16 occurrences of "80pt" / "60pt" combined
    assert css.count("margin-top: 80pt") == 4
    assert css.count("margin-left: 60pt") == 4


def test_build_page_margin_css_uses_important():
    """Margins must win over any user @page rules that survived sanitisation."""
    margins = {'first_page': {'top': 100, 'right': 50, 'bottom': 100, 'left': 50}}
    css = _build_page_margin_css(margins)
    # 4 margins per block × 4 blocks (:first, :left, :right, default) = 16
    assert css.count("!important") == 16


def test_page_with_margin_declaration_is_stripped():
    css = "@page { margin-top: 20pt; margin-left: 30pt; } body { color: red; }"
    out = _strip_page_rules_with_margins(css)
    assert "@page" not in out
    assert "margin-top" not in out
    assert "body { color: red; }" in out


def test_page_with_only_bottom_right_survives():
    """Front-matter page-numbers injects exactly this shape — must not be stripped."""
    css = "@page { @bottom-right { content: counter(page); } }"
    out = _strip_page_rules_with_margins(css)
    assert "@bottom-right" in out
    assert "counter(page)" in out
    assert "@page" in out


def test_page_alternate_left_right_first_all_survive():
    """The `alternate` mode produces three @page rules with margin-boxes only."""
    css = (
        "@page :left { @bottom-left { content: counter(page); } }\n"
        "@page :right { @bottom-right { content: counter(page); } }\n"
        "@page :first { @bottom-left { content: \"\"; } @bottom-right { content: \"\"; } }"
    )
    out = _strip_page_rules_with_margins(css)
    assert "@page :left" in out
    assert "@page :right" in out
    assert "@page :first" in out


def test_mixed_page_block_drops_the_one_with_margins_keeps_the_other():
    css = (
        "@page { margin-top: 40pt; }\n"
        "@page :right { @bottom-right { content: counter(page); } }\n"
    )
    out = _strip_page_rules_with_margins(css)
    # First block is dropped (has margin declaration)
    assert "margin-top" not in out
    # Second block is preserved (only has margin-box)
    assert "@page :right" in out
    assert "counter(page)" in out


def test_nested_braces_do_not_break_the_sanitiser():
    """The naive `@page\\s*{[^}]*}` regex broke on nested braces; ours must not."""
    css = "@page { @bottom-right { content: counter(page); } } body { color: blue; }"
    out = _strip_page_rules_with_margins(css)
    # Body rule must remain complete — not truncated by mid-block brace matching
    assert "body { color: blue; }" in out
    # And @page (with only margin-box) survives
    assert "@page" in out


def test_no_page_rules_no_change():
    css = "body { color: red; }\nh1 { font-size: 20pt; }"
    assert _strip_page_rules_with_margins(css) == css


def test_empty_css_returns_empty():
    assert _strip_page_rules_with_margins("") == ""
