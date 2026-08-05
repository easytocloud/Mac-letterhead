"""
WeasyPrint PDF backend — high-quality rendering with full CSS support.
"""

import logging
import os
import re


def enhance_gfm_task_lists(html_content: str) -> str:
    """Replace raw checkbox inputs with Unicode symbols and add CSS classes."""

    def replace_checked(match):
        data_attr = match.group(1) or ''
        return f'<li class="task-item task-checked"{data_attr}>☑ {match.group(3)}</li>'

    def replace_unchecked(match):
        data_attr = match.group(1) or ''
        return f'<li class="task-item task-unchecked"{data_attr}>☐ {match.group(3)}</li>'

    checked_pat = re.compile(
        r'<li(\s+data-gfm-task="[^"]*")?>\s*(<input type="checkbox" checked[^>]*\s*/?\s*>)\s*(.*?)</li>',
        re.DOTALL)
    unchecked_pat = re.compile(
        r'<li(\s+data-gfm-task="[^"]*")?>\s*(<input type="checkbox"[^>]*\s*/?\s*>)\s*(.*?)</li>',
        re.DOTALL)

    html_content = checked_pat.sub(replace_checked, html_content)
    html_content = unchecked_pat.sub(replace_unchecked, html_content)
    html_content = re.sub(r'\[x\]', '<span class="task-checked">☑</span>', html_content)
    html_content = re.sub(r'\[\s\]', '<span class="task-unchecked task-unchecked-scaled">☐</span>', html_content)
    return html_content


def _strip_page_rules_with_margins(css: str) -> str:
    """
    Remove `@page { ... }` blocks that declare a `margin-*` property so the
    letterhead-derived margins (set later with `!important`) win. `@page`
    blocks whose body contains only margin-boxes like `@bottom-right { ... }`
    are preserved — that's how front-matter `page-numbers:` injects counters,
    and how users can customize headers/footers via their own CSS.

    Handles nested braces correctly (a naive `@page\\s*{[^}]*}` regex breaks
    on `@page { @bottom-right { ... } }` because `[^}]` stops at the first
    inner brace).
    """
    result = []
    i = 0
    n = len(css)
    while i < n:
        # Find next @page
        m = re.search(r'@page\b[^{]*', css[i:], flags=re.IGNORECASE)
        if not m:
            result.append(css[i:])
            break
        start_idx = i + m.start()
        result.append(css[i:start_idx])
        # Find the opening brace
        brace_start = css.find('{', start_idx)
        if brace_start == -1:
            result.append(css[start_idx:])
            break
        # Walk the block, respecting nested braces
        depth = 1
        j = brace_start + 1
        while j < n and depth > 0:
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        # j now points just past the closing brace of the outermost block
        block = css[start_idx:j]
        # Only drop the block if its top-level body has a margin-* declaration.
        # Inspect only the direct children — a margin-* inside an inner
        # margin-box shouldn't count (that's user-authored, and not conflicting).
        body = css[brace_start + 1:j - 1]
        top_level = _strip_nested_braces(body)
        if re.search(r'\bmargin(?:-top|-right|-bottom|-left)?\s*:', top_level, flags=re.IGNORECASE):
            # drop the block
            pass
        else:
            result.append(block)
        i = j
    return ''.join(result)


def _strip_nested_braces(s: str) -> str:
    """Return `s` with content inside nested {…} pairs removed, so a subsequent
    regex only sees top-level declarations."""
    out = []
    depth = 0
    for ch in s:
        if ch == '{':
            depth += 1
            continue
        if ch == '}':
            depth = max(0, depth - 1)
            continue
        if depth == 0:
            out.append(ch)
    return ''.join(out)


def _load_default_css() -> str:
    """Load defaults.css from the package resources, with multiple fallbacks."""
    try:
        try:
            from importlib import resources
            with resources.open_text('letterhead_pdf.resources', 'defaults.css') as f:
                css = f.read()
            logging.info("Loaded default CSS via importlib.resources")
            return css
        except (ImportError, AttributeError):
            pass

        try:
            import importlib_resources
            with importlib_resources.open_text('letterhead_pdf.resources', 'defaults.css') as f:
                css = f.read()
            logging.info("Loaded default CSS via importlib_resources")
            return css
        except ImportError:
            pass

        # Final fallback: file path relative to this file's package root
        pkg_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(pkg_root, 'resources', 'defaults.css')
        with open(path, 'r', encoding='utf-8') as f:
            css = f.read()
        logging.info("Loaded default CSS via file path")
        return css

    except Exception as e:
        logging.warning(f"Could not load default CSS: {e}")
        return ""


def render(html_content: str, output_path: str, margins: dict, page_size, css_path: str = None) -> None:
    """Render html_content to output_path as PDF using WeasyPrint."""
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    html_content = enhance_gfm_task_lists(html_content)

    defaults_css = _load_default_css()

    # Load and validate custom CSS. Allow $HOME and the per-user temp directory; see
    # processor.py for the rationale (droplets stage their bundled CSS into mktemp).
    custom_css = ""
    if css_path:
        import tempfile as _tempfile
        css_abs = os.path.realpath(os.path.expanduser(css_path))
        allowed_roots = [
            os.path.realpath(os.path.expanduser("~")),
            os.path.realpath(_tempfile.gettempdir()),
        ]
        if not any(
            css_abs == root or css_abs.startswith(root + os.sep)
            for root in allowed_roots
        ):
            raise ValueError(
                f"CSS path must be within the home directory or system temp dir: "
                f"{css_path!r} resolves to {css_abs!r}"
            )
        if os.path.exists(css_abs):
            try:
                with open(css_abs, 'r', encoding='utf-8') as f:
                    custom_css = f.read()
                logging.info(f"CSS loaded: {css_abs} ({len(custom_css)} chars)")
            except Exception as e:
                logging.warning(f"CSS load failed for {css_abs!r}: {e}")
        else:
            logging.warning(f"CSS file not found: {css_abs}")

    # Strip @page rules from custom CSS *only if* they contain margin declarations
    # (margin-top/right/bottom/left) — those would conflict with the letterhead-
    # derived margins we set later with `!important`. Leave @page rules that only
    # contain margin-box boxes (@bottom-right, @top-left, etc.) intact — those
    # are how front-matter `page-numbers:` injects its counter, and how users
    # can customize headers/footers via their own CSS. Also handle nested braces
    # correctly by matching a balanced block via a small state machine, since the
    # naive `[^}]*` regex breaks on `@page { @bottom-right { ... } }`.
    if custom_css:
        stripped = _strip_page_rules_with_margins(custom_css)
        if stripped != custom_css:
            logging.info("Removed @page margin declarations from custom CSS to preserve letterhead margins")
        custom_css = stripped

    pygments_css = ""
    try:
        import importlib.util
        if importlib.util.find_spec("pygments") is not None:
            from pygments.formatters import HtmlFormatter
            pygments_css = HtmlFormatter().get_style_defs('.codehilite')
    except Exception:
        pass

    fp = margins['first_page']
    combined_css = f"""
{defaults_css}

{custom_css}

{pygments_css}

@page {{
    margin-top: {fp['top']}pt !important;
    margin-right: {fp['right']}pt !important;
    margin-bottom: {fp['bottom']}pt !important;
    margin-left: {fp['left']}pt !important;
    /* Page numbers deliberately OFF here — opt in via front-matter
     * `page-numbers:` (see letterhead_pdf.markdown.front_matter). */
}}
"""

    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Markdown Document</title>
    <style>{combined_css}</style>
</head>
<body>
{html_content}
</body>
</html>"""

    font_config = FontConfiguration()
    HTML(string=html_template).write_pdf(output_path, font_config=font_config)
    logging.info(f"WeasyPrint wrote PDF: {output_path}")
