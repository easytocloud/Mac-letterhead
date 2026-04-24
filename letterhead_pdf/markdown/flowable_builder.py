"""
Convert parsed HTML to ReportLab flowables.
"""

import logging
import re
from typing import List

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image, KeepTogether, ListFlowable, ListItem,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)

from letterhead_pdf.markdown.html_cleaner import clean_html_for_reportlab, process_list_items


def build_styles():
    """Return a StyleSheet with the custom styles used for letterhead documents."""
    styles = getSampleStyleSheet()

    styles['Normal'].fontSize = 9
    styles['Normal'].leading = 11
    styles['Normal'].spaceBefore = 4
    styles['Normal'].spaceAfter = 4

    styles['Code'].fontName = 'Courier'
    styles['Code'].fontSize = 8
    styles['Code'].leading = 10
    styles['Code'].backColor = colors.lightgrey
    styles['Code'].borderWidth = 1
    styles['Code'].borderColor = colors.grey
    styles['Code'].borderPadding = 6
    styles['Code'].spaceBefore = 6
    styles['Code'].spaceAfter = 6

    styles.add(ParagraphStyle('CustomHeading1', fontName='Helvetica-Bold', fontSize=14,
                               leading=18, alignment=TA_LEFT, spaceBefore=10, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle('CustomHeading2', fontName='Helvetica-Bold', fontSize=12,
                               leading=16, alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle('CustomHeading3', fontName='Helvetica-Bold', fontSize=10,
                               leading=14, alignment=TA_LEFT, spaceBefore=6, spaceAfter=3, keepWithNext=True))
    styles.add(ParagraphStyle('BulletItem', parent=styles['Normal'], leftIndent=20, firstLineIndent=0))
    styles.add(ParagraphStyle('NumberItem', parent=styles['Normal'], leftIndent=20, firstLineIndent=0))
    styles.add(ParagraphStyle('Blockquote', parent=styles['Normal'],
                               leftIndent=30, rightIndent=30, spaceBefore=12, spaceAfter=12, fontStyle='italic'))
    return styles


def detect_list_nesting_structure(html_content: str) -> dict:
    """Return nesting metadata (max_depth, base_indent, indent_per_level) for html_content."""
    depth = max_depth = 0
    for match in re.finditer(r'<(?:ul|ol)[^>]*>|</(?:ul|ol)>', html_content):
        if match.group(0).startswith('</'):
            depth -= 1
        else:
            depth += 1
            max_depth = max(max_depth, depth)
    return {'max_depth': max_depth, 'base_indent': 18, 'indent_per_level': 18}


def calculate_list_indentation(nesting_level: int, indent_info: dict) -> int:
    """Points of left-indent for the given nesting depth."""
    return max(indent_info['base_indent'] + nesting_level * indent_info['indent_per_level'], 12)


def safe_list_item_value(item_type: str, proposed_value=None):
    """Return a value that won't crash ReportLab's ListItem implementation."""
    if item_type == 'bullet':
        if proposed_value is None:
            return '•'
        return 0 if proposed_value == 0 else str(proposed_value)
    else:
        if proposed_value is None:
            return 0
        return str(proposed_value) if isinstance(proposed_value, int) and proposed_value != 0 else proposed_value


def parse_nested_lists(text: str) -> str:
    """Flatten one level of nested <ul>/<ol> to indented plain text for ReportLab."""
    def replace(match):
        list_type = match.group(1)
        items = re.findall(r'<li>(.*?)</li>', match.group(2), re.DOTALL)
        result = ""
        for i, item in enumerate(items, 1):
            result += ("\n    • " if list_type == 'ul' else f"\n    {i}. ") + item.strip()
        return result

    return re.sub(r'<(ul|ol)>(.*?)</\1>', replace, text, flags=re.DOTALL)


def extract_images(html_content: str):
    """Remove <img> tags from HTML and return (cleaned_html, [src, ...])."""
    images = []
    for img_tag in re.compile(r'<img[^>]+>').findall(html_content):
        m = re.search(r'src="([^"]+)"', img_tag)
        if m:
            src = m.group(1)
            if not src.startswith(('http://', 'https://')):
                images.append(src)
        html_content = html_content.replace(img_tag, '')
    return html_content, images


def markdown_to_flowables(html_content: str, styles) -> List:
    """Convert HTML (from a Markdown conversion) to a list of ReportLab flowables."""
    flowables = []

    html_content, images = extract_images(html_content)
    html_content = clean_html_for_reportlab(html_content)

    for src in images:
        try:
            img = Image(src)
            img.drawHeight = 0.5 * inch
            img.drawWidth = 0.5 * inch * (img.imageWidth / img.imageHeight)
            flowables.append(img)
            flowables.append(Spacer(1, 6))
        except Exception as e:
            logging.warning(f"Failed to load image {src}: {e}")

    lines = html_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('<h1>'):
            flowables.append(Paragraph(line.replace('<h1>', '').replace('</h1>', ''), styles['CustomHeading1']))
            flowables.append(Spacer(1, 6))

        elif line.startswith('<h2>'):
            flowables.append(Paragraph(line.replace('<h2>', '').replace('</h2>', ''), styles['CustomHeading2']))
            flowables.append(Spacer(1, 4))

        elif line.startswith('<h3>'):
            flowables.append(Paragraph(line.replace('<h3>', '').replace('</h3>', ''), styles['CustomHeading3']))
            flowables.append(Spacer(1, 4))

        elif line.startswith('<p>'):
            text = line.replace('<p>', '').replace('</p>', '')
            j = i + 1
            while j < len(lines) and not lines[j].strip().endswith('</p>'):
                text += ' ' + lines[j].strip()
                j += 1
            if j < len(lines) and lines[j].strip().endswith('</p>'):
                text += ' ' + lines[j].strip().replace('</p>', '')
                i = j
            if text.strip():
                flowables.append(Paragraph(text, styles['Normal']))
                flowables.append(Spacer(1, 6))

        elif line.startswith('<ul>'):
            indent_info = detect_list_nesting_structure(html_content)
            items, i = process_list_items('bullet', lines, i + 1)
            bullet_list = []
            for item_data in items:
                text = item_data['text'] if isinstance(item_data, dict) else item_data
                level = item_data['nesting_level'] if isinstance(item_data, dict) else 0
                indent = calculate_list_indentation(level, indent_info)
                item_style = ParagraphStyle(f'BulletItem_L{level}', parent=styles['Normal'],
                                            leftIndent=indent, firstLineIndent=0)
                bullet_list.append(ListItem(Paragraph(text, item_style),
                                            leftIndent=indent, value=safe_list_item_value('bullet')))
            flowables.append(ListFlowable(bullet_list, bulletType='bullet', start=0,
                                          bulletFontName='Helvetica', bulletFontSize=10,
                                          leftIndent=indent_info['base_indent'],
                                          spaceBefore=6, spaceAfter=6))

        elif line.startswith('<ol>'):
            indent_info = detect_list_nesting_structure(html_content)
            items, i = process_list_items('number', lines, i + 1)
            number_list = []
            for item_data in items:
                text = item_data['text'] if isinstance(item_data, dict) else item_data
                level = item_data['nesting_level'] if isinstance(item_data, dict) else 0
                indent = calculate_list_indentation(level, indent_info)
                item_style = ParagraphStyle(f'NumberItem_L{level}', parent=styles['Normal'],
                                            leftIndent=indent, firstLineIndent=0)
                number_list.append(ListItem(Paragraph(text, item_style),
                                            leftIndent=indent, value=safe_list_item_value('number')))
            flowables.append(ListFlowable(number_list, bulletType='1', start=1,
                                          bulletFontName='Helvetica', bulletFontSize=10,
                                          leftIndent=indent_info['base_indent'],
                                          spaceBefore=6, spaceAfter=6))

        elif line.startswith('<pre>'):
            code = []
            j = i
            while j < len(lines) and not lines[j].strip().endswith('</pre>'):
                if j > i:
                    code.append(lines[j])
                j += 1
            if j < len(lines) and lines[j].strip().endswith('</pre>'):
                code.append(lines[j].replace('</pre>', ''))
                i = j
            code_text = '\n'.join(code).replace('<code>', '').replace('</code>', '')
            flowables.append(Preformatted(code_text, styles['Code']))
            flowables.append(Spacer(1, 8))

        elif line.startswith('<table>'):
            data = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != '</table>':
                if lines[j].strip().startswith('<tr>'):
                    row = []
                    k = j + 1
                    while k < len(lines) and lines[k].strip() != '</tr>':
                        cell = lines[k].strip()
                        if cell.startswith('<td>') or cell.startswith('<th>'):
                            cell = cell.replace('<td>', '').replace('</td>', '')
                            cell = cell.replace('<th>', '').replace('</th>', '')
                            row.append(cell)
                        k += 1
                    j = k
                    if row:
                        data.append(row)
                j += 1
            i = j
            if data:
                t = Table(data)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                flowables.append(t)
                flowables.append(Spacer(1, 12))

        elif line.startswith('<blockquote>'):
            text = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != '</blockquote>':
                p = lines[j].strip()
                if p.startswith('<p>'):
                    text.append(p.replace('<p>', '').replace('</p>', ''))
                j += 1
            i = j
            if text:
                flowables.append(Paragraph(' '.join(text), styles['Blockquote']))
                flowables.append(Spacer(1, 6))

        i += 1

    if not flowables:
        flowables.append(Paragraph("", styles['Normal']))

    logging.info(f"Generated {len(flowables)} flowables")
    return flowables
