"""
HTML cleaning and Markdown indentation preprocessing for ReportLab compatibility.
"""

import logging
import re


def clean_html_for_reportlab(html_content: str) -> str:
    """Strip WeasyPrint/Pygments markup and translate tags to ReportLab equivalents."""
    html_content = re.sub(
        r'<div class="codehilite"><pre><span></span>(.*?)</pre></div>',
        r'<pre>\1</pre>', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<span[^>]*class="[^"]*"[^>]*>(.*?)</span>', r'\1', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<div[^>]*class="[^"]*"[^>]*>(.*?)</div>', r'\1', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1', html_content, flags=re.DOTALL)

    def clean_link(match):
        href = re.search(r'href="([^"]+)"', match.group(1))
        return f'<a href="{href.group(1)}">' if href else '<a>'

    html_content = re.compile(r'<a\s+([^>]+)>').sub(clean_link, html_content)

    html_content = html_content.replace('<strong>', '<b>').replace('</strong>', '</b>')
    html_content = html_content.replace('<em>', '<i>').replace('</em>', '</i>')
    html_content = html_content.replace('<del>', '<strike>').replace('</del>', '</strike>')
    html_content = re.sub(r'<code[^>]*>(.*?)</code>', r'<font face="Courier">\1</font>', html_content)

    html_content = re.sub(r'<input type="checkbox" checked[^>]*\s*/?\s*>\s*', '☑ ', html_content)
    html_content = re.sub(r'<input type="checkbox"[^>]*\s*/?\s*>\s*', '☐ ', html_content)
    html_content = re.sub(r'\[x\]', '☑', html_content)
    html_content = re.sub(r'\[\s\]', '☐', html_content)

    html_content = re.sub(r'\s+data-gfm-task="[^"]*"', '', html_content)
    html_content = re.sub(r'\s+disabled=""', '', html_content)
    html_content = re.sub(r'(\s+class="[^"]*")', '', html_content)

    return html_content


def process_list_items(list_type: str, lines: list, start_index: int, nesting_level: int = 0):
    """Walk HTML lines starting at start_index, collecting <li> items until </ul> or </ol>.

    Returns (items, new_index) where items is a list of dicts with keys
    'text', 'nesting_level', 'has_nested'.
    """
    items = []
    i = start_index

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('<li>'):
            text = line.replace('<li>', '').replace('</li>', '')
            j = i + 1
            while (j < len(lines)
                   and not lines[j].strip().endswith('</li>')
                   and lines[j].strip() not in ('</ul>', '</ol>')):
                text += ' ' + lines[j].strip()
                j += 1
            if j < len(lines) and lines[j].strip().endswith('</li>'):
                text += ' ' + lines[j].strip().replace('</li>', '')
                i = j

            text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
            text = text.replace('<em>', '<i>').replace('</em>', '</i>')
            text = text.replace('<code>', '<font face="Courier">').replace('</code>', '</font>')

            items.append({
                'text': text,
                'nesting_level': nesting_level,
                'has_nested': '<ul>' in text or '<ol>' in text,
            })

        elif line in ('</ul>', '</ol>'):
            break

        i += 1

    return items, i


def _calculate_normalized_indent(current_indent: int, indent_stack: list) -> int:
    """Return the 4-space-normalised indent for current_indent given the running stack."""
    if current_indent == 0:
        indent_stack.clear()
        return 0

    while indent_stack and indent_stack[-1][0] >= current_indent:
        indent_stack.pop()

    for original, normalized in indent_stack:
        if original == current_indent:
            return normalized

    normalized = 4 if not indent_stack else indent_stack[-1][1] + 4
    indent_stack.append((current_indent, normalized))
    return normalized


def preprocess_markdown_indentation(md_content: str) -> str:
    """Normalise list indentation to 4-space and insert blank lines after colons.

    This ensures the Python markdown library correctly recognises nested lists
    regardless of whether the source used 2-space or 4-space indentation.
    """
    lines = md_content.split('\n')
    processed = []
    list_item_pattern = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.*)$')
    colon_line_pattern = re.compile(r'^.*:\s*$')
    indent_stack: list = []

    for line in lines:
        match = list_item_pattern.match(line)
        if match:
            indent_str, marker, content = match.groups()
            current_indent = len(indent_str)

            if (processed and colon_line_pattern.match(processed[-1]) and current_indent == 0):
                processed.append('')
                logging.debug(f"Inserted blank line before top-level list: {line.strip()}")

            normalized = _calculate_normalized_indent(current_indent, indent_stack)
            processed_line = f"{' ' * normalized}{marker} {content}"
            processed.append(processed_line)

            if current_indent != normalized:
                logging.debug(f"Indent normalised {current_indent}->{normalized}: {line.strip()}")
        else:
            if line.strip() == '':
                pass
            elif not line.startswith(' '):
                indent_stack = []
            processed.append(line)

    return '\n'.join(processed)
