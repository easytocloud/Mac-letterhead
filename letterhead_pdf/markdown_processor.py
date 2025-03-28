#!/usr/bin/env python3

import os
import logging
import tempfile
from typing import Optional, Dict, Tuple
import markdown
import fitz  # PyMuPDF
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

class MarkdownProcessor:
    """Handles conversion of Markdown files to PDF with proper formatting"""
    
    def __init__(self):
        """Initialize the Markdown processor with default settings"""
        self.md = markdown.Markdown(extensions=['tables', 'fenced_code', 'footnotes'])
        self.font_config = FontConfiguration()
        
        # Default CSS for PDF generation
        self.default_css = CSS(string='''
            @page {
                margin: 0;  /* We'll set margins based on letterhead analysis */
                @top-left { content: ''; }
                @top-right { content: ''; }
                @bottom-left { content: ''; }
                @bottom-right { content: ''; }
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 9pt;
                line-height: 1.3;
                margin: 0;
                padding: 0;
            }
            h1 {
                font-size: 13pt;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }
            
            h2 {
                font-size: 11pt;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }
            
            h3, h4, h5, h6 {
                font-size: 10pt;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }
            p {
                margin: 0.5em 0;
            }
            pre {
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 4px;
                overflow-x: auto;
            }
            code {
                font-family: "SF Mono", Monaco, Consolas, monospace;
                font-size: 0.95em;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 0.5em;
                text-align: left;
            }
            th {
                background-color: #f5f5f5;
            }
        ''', font_config=self.font_config)

    def analyze_page_regions(self, page):
        """Analyze a page to detect header and footer regions and page size"""
        page_rect = page.rect
        
        # Determine page size
        # Standard sizes in points (1 point = 1/72 inch)
        # A4: 595 x 842 points
        # Letter: 612 x 792 points
        width = page_rect.width
        height = page_rect.height
        
        # Determine closest standard size
        if abs(width - 595) <= 1 and abs(height - 842) <= 1:
            page_size = "A4"
        elif abs(width - 612) <= 1 and abs(height - 792) <= 1:
            page_size = "letter"
        else:
            # Default to A4 for non-standard sizes
            page_size = "A4"
            logging.info(f"Non-standard page size detected ({width}x{height}), defaulting to A4")
        
        # Split page into quarters vertically
        top_quarter = page_rect.height / 4
        bottom_quarter = page_rect.height * 3 / 4
        
        # Initialize regions
        header_rect = None
        footer_rect = None
        middle_rect = None
        
        # First analyze text blocks
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])
            block_center = (block_rect.y0 + block_rect.y1) / 2
            
            # Categorize block based on its vertical position
            if block_center < top_quarter:
                # Block is in top third (header)
                if header_rect is None:
                    header_rect = block_rect
                else:
                    header_rect = header_rect.include_rect(block_rect)
            elif block_center > bottom_quarter:
                # Block is in bottom third (footer)
                if footer_rect is None:
                    footer_rect = block_rect
                else:
                    footer_rect = footer_rect.include_rect(block_rect)
            else:
                # Block is in middle third
                if middle_rect is None:
                    middle_rect = block_rect
                else:
                    middle_rect = middle_rect.include_rect(block_rect)
        
        # Then analyze drawings (logos, graphics, etc.)
        paths = page.get_drawings()
        for path in paths:
            # Each path contains drawing commands and a bounding box
            rect = fitz.Rect(path["rect"])
            center = (rect.y0 + rect.y1) / 2
            
            # Categorize content based on its vertical position
            if center < top_quarter:
                # Content is in top third (header)
                if header_rect is None:
                    header_rect = rect
                else:
                    header_rect = header_rect.include_rect(rect)
            elif center > bottom_quarter:
                # Content is in bottom third (footer)
                if footer_rect is None:
                    footer_rect = rect
                else:
                    footer_rect = footer_rect.include_rect(rect)
            else:
                # Content is in middle third
                if middle_rect is None:
                    middle_rect = rect
                else:
                    middle_rect = middle_rect.include_rect(rect)
        
        return {
            'header': header_rect,
            'footer': footer_rect,
            'middle': middle_rect,
            'page_rect': page_rect,
            'page_size': page_size,
            'width': width,
            'height': height
        }

    def analyze_letterhead(self, letterhead_path: str) -> Dict[str, Dict[str, float]]:
        """
        Analyze letterhead PDF to determine safe printable areas and detect header/footer regions
        
        Returns:
            Dict containing margin information for first and subsequent pages
        """
        logging.info(f"Analyzing letterhead margins: {letterhead_path}")
        
        try:
            doc = fitz.open(letterhead_path)
            margins = {
                'first_page': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
                'other_pages': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
            }
            
            # Analyze first page
            if doc.page_count > 0:
                regions = self.analyze_page_regions(doc[0])
                page_rect = regions['page_rect']
                
                # Calculate margins based on detected regions
                margins['first_page'] = {
                    'top': regions['header'].y1 if regions['header'] else 0,
                    'right': page_rect.width - (regions['middle'].x1 if regions['middle'] else page_rect.width),
                    'bottom': page_rect.height - (regions['footer'].y0 if regions['footer'] else page_rect.height),
                    'left': regions['middle'].x0 if regions['middle'] else 0
                }
                
                # If there's a second page, analyze it for other pages template
                if doc.page_count > 1:
                    regions = self.analyze_page_regions(doc[1])
                    margins['other_pages'] = {
                        'top': regions['header'].y1 if regions['header'] else 0,
                        'right': page_rect.width - (regions['middle'].x1 if regions['middle'] else page_rect.width),
                        'bottom': page_rect.height - (regions['footer'].y0 if regions['footer'] else page_rect.height),
                        'left': regions['middle'].x0 if regions['middle'] else 0
                    }
                else:
                    # If no second page, use first page margins
                    margins['other_pages'] = margins['first_page'].copy()
            
            # Add padding to ensure we don't overlap with letterhead
            # More padding for top/bottom where letterhead content is likely to be
            for page_type in margins:
                margins[page_type]['top'] += 40  # Extra padding for header
                margins[page_type]['bottom'] += 40  # Extra padding for footer
                margins[page_type]['left'] += 20  # Standard padding for sides
                margins[page_type]['right'] += 20
            
            # Log detected regions
            logging.info(f"Detected margins for first page: {margins['first_page']}")
            logging.info(f"Detected margins for other pages: {margins['other_pages']}")
            
            return margins
            
        except Exception as e:
            logging.error(f"Error analyzing letterhead margins: {str(e)}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()

    def md_to_pdf(self, md_path: str, output_path: str, letterhead_path: str) -> str:
        """
        Convert markdown file to PDF with proper margins based on letterhead
        
        Args:
            md_path: Path to markdown file
            output_path: Path to save the output PDF
            letterhead_path: Path to letterhead PDF for margin analysis
            
        Returns:
            Path to the generated PDF
        """
        logging.info(f"Converting markdown to PDF: {md_path} -> {output_path}")
        
        try:
            # Read markdown content
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert to HTML and wrap sections in divs
            html_content = self.md.convert(md_content)
            
            # Split content into sections at h1/h2 headers
            import re
            sections = re.split(r'(<h[12][^>]*>.*?</h[12]>)', html_content)
            wrapped_content = []
            for section in sections:
                if section.strip():
                    if section.startswith('<h'):
                        # Start new section with header
                        wrapped_content.append(f'<div class="content-section">{section}')
                    else:
                        # Either close previous section or wrap standalone content
                        if wrapped_content and wrapped_content[-1].startswith('<div'):
                            wrapped_content[-1] += f'{section}</div>'
                        else:
                            wrapped_content.append(f'<div class="content-section">{section}</div>')
            
            html_content = '\n'.join(wrapped_content)
            
            # Analyze letterhead for margins and page size
            doc = fitz.open(letterhead_path)
            try:
                first_page = doc[0]
                regions = self.analyze_page_regions(first_page)
                margins = self.analyze_letterhead(letterhead_path)
                
                # Get page size from letterhead analysis
                page_size = regions['page_size']
                page_width = regions['width']
                page_height = regions['height']
            finally:
                doc.close()
            
            logging.info(f"Using page size from letterhead: {page_size} ({page_width}x{page_height})")
            
            # Calculate content height (page height minus top and bottom margins)
            content_height = page_height - margins['first_page']['top'] - margins['first_page']['bottom']
            
            # Create CSS with margins and page-specific styles
            margin_css = CSS(string=f'''
                /* Define page layouts */
                @page {{
                    size: {page_width}pt {page_height}pt;
                    margin: {margins['other_pages']['top']}pt {margins['other_pages']['right']}pt {margins['other_pages']['bottom']}pt {margins['other_pages']['left']}pt;
                    @top-left {{ content: ''; }}
                    @top-right {{ content: ''; }}
                    @bottom-left {{ content: ''; }}
                    @bottom-right {{ content: ''; }}
                }}
                
                @page:first {{
                    margin: {margins['first_page']['top']}pt {margins['first_page']['right']}pt {margins['first_page']['bottom']}pt {margins['first_page']['left']}pt;
                }}
                
                /* Content styles */
                body {{
                    margin: 0;
                    padding: 0;
                    font-size: 9pt;  /* Slightly smaller base font */
                    line-height: 1.3;
                    max-width: 100%;
                    box-sizing: border-box;
                }}
                
                /* Content sections */
                .content-section {{
                    margin-bottom: 1em;
                    page-break-inside: avoid;
                }}
                
                /* Ensure proper spacing between sections */
                .content-section + .content-section {{
                    margin-top: 1em;
                }}
                
                /* Force page breaks before major sections */
                h1:not(:first-of-type) {{
                    page-break-before: always;
                }}
                
                /* Prevent orphaned headers */
                h1, h2, h3, h4, h5, h6 {{
                    page-break-after: avoid;
                    break-after: avoid;
                }}
                
                /* Keep lists together */
                li {{
                    page-break-inside: avoid;
                    break-inside: avoid;
                }}
                
                /* Table handling */
                table {{
                    width: 100%;
                    margin: 1em 0;
                    page-break-inside: avoid;  /* Keep tables together */
                }}
                
                tr {{
                    page-break-inside: avoid;
                }}
                
                /* Ensure proper spacing and page breaks */
                p, h1, h2, h3, h4, h5, h6, ul, ol, table {{
                    margin-top: 0;
                    margin-bottom: 1em;
                    break-inside: avoid;
                    page-break-inside: avoid;
                }}
                
                /* Prevent orphaned headers */
                h1, h2, h3, h4, h5, h6 {{
                    page-break-after: avoid;
                }}
                
                /* Keep lists together */
                li {{
                    page-break-inside: avoid;
                }}
                
                /* Table handling */
                table {{
                    page-break-inside: auto;
                }}
                
                tr {{
                    page-break-inside: avoid;
                    page-break-after: auto;
                }}
            ''', font_config=self.font_config)
            
            # Create complete HTML document
            html_doc = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>Converted Document</title>
                </head>
                <body>
                    <div class="content-wrapper">
                        {html_content}
                    </div>
                </body>
                </html>
            '''
            
            # Convert to PDF with WeasyPrint
            HTML(string=html_doc).write_pdf(
                output_path,
                stylesheets=[self.default_css, margin_css],
                font_config=self.font_config
            )
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error converting markdown to PDF: {str(e)}")
            raise
