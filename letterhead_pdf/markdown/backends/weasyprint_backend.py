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

    # Load and validate custom CSS
    custom_css = ""
    if css_path:
        css_abs = os.path.realpath(os.path.expanduser(css_path))
        home = os.path.realpath(os.path.expanduser("~"))
        if not css_abs.startswith(home + os.sep) and css_abs != home:
            raise ValueError(
                f"CSS path must be within the home directory: {css_path!r} resolves to {css_abs!r}"
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

    # Strip any @page rules from custom CSS — our margin block takes precedence
    if custom_css:
        stripped = re.sub(r'@page\s*{[^}]*}', '', custom_css, flags=re.DOTALL | re.IGNORECASE)
        if stripped != custom_css:
            logging.info("Removed @page rules from custom CSS to preserve letterhead margins")
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

    @bottom-center {{
        content: counter(page);
        font-family: Helvetica, Arial, sans-serif;
        font-size: 9pt;
        color: #666666;
    }}
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
