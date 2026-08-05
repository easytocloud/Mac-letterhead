"""
Tests for YAML front matter parsing, precedence-aware resolution, and the
page-numbers CSS injection.

Covers the four things a caller can get wrong:

  1. shape: does `---` fence detection work, and does the body come back clean?
  2. validation: are unknown fields / bad values dropped with a warning?
  3. precedence: does explicit > front-matter always hold, and does the
     server-bound-style rule short-circuit correctly?
  4. CSS: do the four page-numbers values produce the expected @page rules?
"""

from __future__ import annotations

import pytest

from letterhead_pdf.markdown.front_matter import (
    KNOWN_FIELDS,
    VALID_BLEND_STRATEGIES,
    VALID_PAGE_NUMBERS,
    page_numbers_css,
    parse,
    resolve,
)


# ---- parser --------------------------------------------------------------


def test_parse_no_front_matter_returns_original():
    src = "# Just a heading\n\nSome text.\n"
    fm, body = parse(src)
    assert fm == {}
    assert body == src


def test_parse_valid_front_matter_returns_body_only():
    src = (
        "---\n"
        "title: Q3 Report\n"
        "page-numbers: bottom-right\n"
        "---\n"
        "# Q3 Report\n\nBody.\n"
    )
    fm, body = parse(src)
    assert fm == {"title": "Q3 Report", "page-numbers": "bottom-right"}
    assert body == "# Q3 Report\n\nBody.\n"


def test_parse_handles_quoted_strings():
    src = "---\ntitle: 'Q3 Report: with colon'\n---\ncontent\n"
    fm, _ = parse(src)
    assert fm["title"] == "Q3 Report: with colon"


def test_parse_handles_double_quoted_strings():
    src = '---\ntitle: "spaces  matter"\n---\nbody\n'
    fm, _ = parse(src)
    assert fm["title"] == "spaces  matter"


def test_parse_missing_close_marker_ignores_front_matter():
    """`---` opens but never closes — treat whole document as body."""
    src = "---\ntitle: X\n\n# heading with no close\nmore text\n"
    fm, body = parse(src)
    assert fm == {}
    assert body == src


def test_parse_ignores_blank_lines_and_comments():
    src = (
        "---\n"
        "# a comment line\n"
        "\n"
        "title: X\n"
        "---\n"
        "body\n"
    )
    fm, _ = parse(src)
    assert fm == {"title": "X"}


def test_parse_missing_colon_is_ignored():
    src = "---\ntitle X\n---\nbody\n"
    fm, _ = parse(src)
    assert fm == {}


def test_parse_unknown_field_is_ignored():
    src = "---\ntitle: X\nunknownkey: value\n---\nbody\n"
    fm, _ = parse(src)
    assert "unknownkey" not in fm
    assert fm["title"] == "X"


def test_parse_expands_home_in_output_dir():
    src = "---\noutput-dir: ~/somewhere\n---\nbody\n"
    fm, _ = parse(src)
    assert fm["output-dir"].endswith("/somewhere")
    assert not fm["output-dir"].startswith("~")


# ---- validation ----------------------------------------------------------


@pytest.mark.parametrize("val", VALID_PAGE_NUMBERS)
def test_page_numbers_accepts_all_valid_values(val):
    fm, _ = parse(f"---\npage-numbers: {val}\n---\nbody\n")
    assert fm["page-numbers"] == val


def test_page_numbers_rejects_invalid_value():
    fm, _ = parse("---\npage-numbers: middle-of-nowhere\n---\nbody\n")
    assert "page-numbers" not in fm


@pytest.mark.parametrize("val", VALID_BLEND_STRATEGIES)
def test_blend_strategy_accepts_all_valid_values(val):
    fm, _ = parse(f"---\nblend-strategy: {val}\n---\nbody\n")
    assert fm["blend-strategy"] == val


def test_blend_strategy_rejects_invalid_value():
    fm, _ = parse("---\nblend-strategy: nope\n---\nbody\n")
    assert "blend-strategy" not in fm


def test_known_fields_matches_advertised_docstring():
    """The tuple advertised in the module docstring should match KNOWN_FIELDS."""
    assert KNOWN_FIELDS == {
        "title", "output-dir", "page-numbers", "blend-strategy",
        "style", "author", "subject",
    }


# ---- resolver precedence -------------------------------------------------


def test_resolve_explicit_wins_over_front_matter():
    fm = {"title": "From FM", "page-numbers": "bottom-right"}
    cfg = resolve(fm, explicit={"title": "From arg"})
    assert cfg.title == "From arg"
    assert cfg.sources["title"] == "explicit"
    # page-numbers had no explicit override → front-matter wins
    assert cfg.page_numbers == "bottom-right"
    assert cfg.sources["page-numbers"] == "front-matter"


def test_resolve_front_matter_fills_in_when_explicit_is_none():
    fm = {"title": "From FM"}
    cfg = resolve(fm, explicit={"title": None})
    assert cfg.title == "From FM"
    assert cfg.sources["title"] == "front-matter"


def test_resolve_empty_string_treated_as_absent():
    """An empty explicit value should NOT beat front matter."""
    fm = {"output-dir": "/tmp/via-fm"}
    cfg = resolve(fm, explicit={"output-dir": ""})
    assert cfg.output_dir == "/tmp/via-fm"


def test_resolve_no_front_matter_leaves_fields_none():
    cfg = resolve({}, explicit={})
    assert cfg.title is None
    assert cfg.page_numbers is None
    assert cfg.sources == {}


# ---- style + server-bound rule ------------------------------------------


def test_style_server_bound_wins_over_front_matter():
    fm = {"style": "personal"}
    cfg = resolve(fm, server_bound_style="easytocloud")
    assert cfg.style == "easytocloud"
    assert cfg.sources["style"] == "server-bound"


def test_style_server_bound_matches_front_matter_is_still_server_bound():
    fm = {"style": "easytocloud"}
    cfg = resolve(fm, server_bound_style="easytocloud")
    assert cfg.style == "easytocloud"
    assert cfg.sources["style"] == "server-bound"


def test_style_front_matter_used_when_no_server_binding():
    fm = {"style": "personal"}
    cfg = resolve(fm, server_bound_style=None)
    assert cfg.style == "personal"
    assert cfg.sources["style"] == "front-matter"


def test_style_explicit_wins_over_front_matter_on_generic_server():
    fm = {"style": "personal"}
    cfg = resolve(fm, explicit={"style": "corporate"}, server_bound_style=None)
    assert cfg.style == "corporate"
    assert cfg.sources["style"] == "explicit"


# ---- page-numbers CSS ---------------------------------------------------


def test_page_numbers_css_none_returns_empty():
    assert page_numbers_css(None) == ""


@pytest.mark.parametrize("pos", ["bottom-right", "bottom-center", "bottom-left"])
def test_page_numbers_css_simple_positions(pos):
    css = page_numbers_css(pos)
    assert f"@{pos}" in css
    assert "counter(page)" in css


def test_page_numbers_css_alternate_uses_left_right_pseudo_classes():
    css = page_numbers_css("alternate")
    assert "@page :first" in css      # title page — no number
    assert "@page :left" in css       # even pages
    assert "@page :right" in css      # odd pages
    assert "@bottom-left" in css      # left-page number position
    assert "@bottom-right" in css     # right-page number position
    assert "counter(page)" in css


def test_page_numbers_alternate_clears_all_bottom_boxes_on_first_page():
    """
    Regression: page 1 in `alternate` mode is a title page — no number in ANY
    bottom corner. WeasyPrint applies `:right` in addition to `:first` when
    page 1 is odd, so `:first` must clear *every* corner a matching `:left`
    or `:right` might have populated. Earlier version only cleared
    `bottom-center`, leaving `bottom-right` populated on page 1 (visible as
    a stray "1" in the corner).
    """
    css = page_numbers_css("alternate")
    # In the :first block, every bottom margin-box must be cleared.
    first_block_start = css.index("@page :first")
    first_block = css[first_block_start:]
    for box in ("@bottom-left", "@bottom-center", "@bottom-right"):
        assert box in first_block, f"{box} not cleared in :first block"
