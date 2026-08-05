"""
YAML-style front matter for Mac-letterhead Markdown documents.

Front matter is a small metadata block at the top of a Markdown file, delimited
by `---` on its own line to open and again to close. It lets users (and LLMs
calling the MCP server) declare per-document overrides without needing extra
CLI flags or tool parameters. Example:

    ---
    title: Q3 Investor Update
    output-dir: ~/Documents/Company/investor
    page-numbers: bottom-right
    ---

    # Q3 Investor Update

    Executive summary…

## Supported fields

All optional. Unknown fields are logged and ignored (forward-compatible).

    title             string   PDF title metadata + auto-generated filename
    output-dir        path     where to write the resulting PDF (supports ~)
    page-numbers      enum     bottom-right | bottom-center | bottom-left | alternate
                               (no default — omit to disable page numbers entirely)
    blend-strategy    enum     darken | multiply | overlay | transparency | reverse
    style             string   letterhead style name (ignored on dedicated MCP servers)
    author            string   PDF author metadata
    subject           string   PDF subject metadata

## Precedence (most-specific wins)

    explicit CLI/MCP arg   >   front matter   >   server/droplet defaults   >   hard-coded

Special case: on a dedicated MCP server (started with `--style <name>`), the
server's bound style always wins. Front-matter `style:` is ignored and a
warning is logged. Rationale: dedicated servers exist so the *user's phrasing*
picks the style, not the document contents.

## Why a hand-rolled parser (no PyYAML)

Front matter here is deliberately simple: scalars only, no lists, no nested
objects, no multi-line strings. A ~40-line parser handles it and avoids
pulling PyYAML into the base install. If we ever need richer YAML we can
swap this out.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# --- validation -----------------------------------------------------------

VALID_PAGE_NUMBERS = ("bottom-right", "bottom-center", "bottom-left", "alternate")
VALID_BLEND_STRATEGIES = ("darken", "multiply", "overlay", "transparency", "reverse")

# All fields we recognize. Anything else in front matter is warn + ignore.
KNOWN_FIELDS = frozenset({
    "title", "output-dir", "page-numbers", "blend-strategy",
    "style", "author", "subject",
})


# --- parsing --------------------------------------------------------------


def _coerce_bool(raw: str) -> Optional[bool]:
    v = raw.strip().lower()
    if v in ("true", "yes", "on"):
        return True
    if v in ("false", "no", "off"):
        return False
    return None


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    return s


def parse(markdown_content: str) -> Tuple[Dict[str, Any], str]:
    """
    Split a Markdown document into (front_matter_dict, body).

    If the document doesn't start with a `---` marker, returns ({}, original).
    If front matter is present but malformed (missing close, bad YAML, etc.),
    logs a warning and returns ({}, original) — the document still renders,
    just without metadata overrides.
    """
    if not markdown_content.startswith("---"):
        return {}, markdown_content

    lines = markdown_content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, markdown_content

    # Find the closing --- marker
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close_idx = i
            break

    if close_idx is None:
        logger.warning("Front matter opened with '---' but no closing '---' found; ignoring")
        return {}, markdown_content

    fm_lines = lines[1:close_idx]
    body = "".join(lines[close_idx + 1:])

    metadata: Dict[str, Any] = {}
    for raw_line in fm_lines:
        line = raw_line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue  # blank or comment
        if ":" not in line:
            logger.warning(f"Front matter line missing ':' separator, ignored: {line!r}")
            continue

        key, _, value = line.partition(":")
        key = key.strip().lower()
        value_raw = value.strip()

        if key not in KNOWN_FIELDS:
            logger.warning(f"Unknown front matter field {key!r} — ignored (known: {sorted(KNOWN_FIELDS)})")
            continue

        # Field-specific coercion + validation
        parsed = _coerce_value(key, value_raw)
        if parsed is not None:
            metadata[key] = parsed

    return metadata, body


def _coerce_value(key: str, raw: str) -> Any:
    """Type-check and validate a single front-matter value. Returns None to skip."""
    if raw == "" or raw.lower() == "null" or raw.lower() == "none":
        return None

    unquoted = _strip_quotes(raw)

    if key == "page-numbers":
        v = unquoted.lower()
        if v in VALID_PAGE_NUMBERS:
            return v
        logger.warning(f"page-numbers: invalid value {raw!r} (allowed: {VALID_PAGE_NUMBERS}) — ignored")
        return None

    if key == "blend-strategy":
        v = unquoted.lower()
        if v in VALID_BLEND_STRATEGIES:
            return v
        logger.warning(f"blend-strategy: invalid value {raw!r} (allowed: {VALID_BLEND_STRATEGIES}) — ignored")
        return None

    if key == "output-dir":
        # Expand ~ but don't validate existence; caller may create the directory.
        return str(Path(unquoted).expanduser())

    # title, style, author, subject — plain string
    return unquoted


# --- config resolution ---------------------------------------------------


@dataclass
class ResolvedConfig:
    """
    Effective per-document configuration after applying precedence rules.

    Every field is Optional — None means "no explicit value at this layer;
    downstream should use its own default". The rendering pipeline consults
    each in turn and applies the ones that are set.
    """
    title: Optional[str] = None
    output_dir: Optional[str] = None
    page_numbers: Optional[str] = None      # one of VALID_PAGE_NUMBERS or None
    blend_strategy: Optional[str] = None    # one of VALID_BLEND_STRATEGIES or None
    style: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None

    # Diagnostic: which layer supplied each value. Useful for `tail -f` debugging.
    sources: Dict[str, str] = field(default_factory=dict)


def resolve(
    front_matter: Dict[str, Any],
    *,
    explicit: Optional[Dict[str, Any]] = None,
    server_bound_style: Optional[str] = None,
) -> ResolvedConfig:
    """
    Apply the precedence rule to produce a single effective config.

        explicit CLI/MCP arg > front matter > (nothing from this layer)

    `explicit` — kwargs the CLI or MCP tool passed in; None values are treated
    as absent. Field names use the same kebab convention as front matter for
    consistency (e.g. `output-dir`, not `output_dir`).

    `server_bound_style` — when set, indicates the MCP server was started with
    `--style <name>`. In that case front-matter `style:` is ignored (with a
    warning) — the server binding wins per project rule.
    """
    explicit = explicit or {}
    cfg = ResolvedConfig()

    # Helper: pick the highest-precedence non-None value for a field.
    def pick(field_name: str) -> Tuple[Optional[Any], Optional[str]]:
        if explicit.get(field_name) not in (None, ""):
            return explicit[field_name], "explicit"
        if front_matter.get(field_name) not in (None, ""):
            return front_matter[field_name], "front-matter"
        return None, None

    for py_attr, fm_key in [
        ("title",         "title"),
        ("output_dir",    "output-dir"),
        ("page_numbers",  "page-numbers"),
        ("blend_strategy","blend-strategy"),
        ("author",        "author"),
        ("subject",       "subject"),
    ]:
        value, source = pick(fm_key)
        if value is not None:
            setattr(cfg, py_attr, value)
            cfg.sources[fm_key] = source

    # style has its own precedence — server binding overrides everything else.
    if server_bound_style:
        if front_matter.get("style") and front_matter["style"] != server_bound_style:
            logger.warning(
                f"Front matter requested style={front_matter['style']!r} but this "
                f"MCP server is bound to style={server_bound_style!r}; "
                f"honouring server binding. Use a generic (unbound) MCP server "
                f"if you want per-document style selection."
            )
        cfg.style = server_bound_style
        cfg.sources["style"] = "server-bound"
    else:
        value, source = pick("style")
        if value is not None:
            cfg.style = value
            cfg.sources["style"] = source

    if cfg.sources:
        logger.info(f"Front matter resolved: {dict(cfg.sources)}")
    return cfg


# --- page-numbers CSS ---------------------------------------------------


def page_numbers_css(position: Optional[str]) -> str:
    """
    Return the CSS `@page` rules that place a page number at `position`.

    `position` is one of VALID_PAGE_NUMBERS or None. None → empty string
    (page numbers disabled — the default).

    `alternate` is designed for multi-page letterheads (title + left-hand +
    right-hand). It suppresses the number on the first page (title), then
    alternates position on subsequent left/right pages.

    This CSS is understood by WeasyPrint. The ReportLab fallback does not
    honour @page rules — a warning is logged elsewhere in that case.
    """
    if not position:
        return ""

    if position == "alternate":
        # Book-style layout: title page (page 1) has no number; subsequent
        # left/right pages carry the number on the outer edge. Note that WeasyPrint
        # applies `:first` in addition to `:left`/`:right` when page 1 is odd —
        # so the `:first` rule must explicitly clear every corner that a matching
        # `:left` or `:right` rule might have set (`content: ""` on all three
        # bottom margin-boxes). Clearing only `bottom-center` leaves the `:right`
        # rule's bottom-right in place, and page 1 would still show "1".
        return (
            "@page :left  { @bottom-left  { content: counter(page); font-size: 9pt; color: #666; } }\n"
            "@page :right { @bottom-right { content: counter(page); font-size: 9pt; color: #666; } }\n"
            "@page :first {\n"
            "  @bottom-left   { content: \"\"; }\n"
            "  @bottom-center { content: \"\"; }\n"
            "  @bottom-right  { content: \"\"; }\n"
            "}\n"
        )

    # bottom-right | bottom-center | bottom-left
    slot = position  # matches the CSS margin-box name directly (bottom-right, etc.)
    return (
        f"@page {{ @{slot} {{ content: counter(page); font-size: 9pt; color: #666; }} }}\n"
    )
