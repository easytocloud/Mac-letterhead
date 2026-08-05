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
    _strip_page_rules_with_margins,
)


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
