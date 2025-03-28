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
                font-size: 12pt;
                line-height: 1.5;
                margin: 0;
                padding: 0;
            }
            h1, h2, h3, h4, h5, h6 {
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
                font-size: 0.9em;
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

    def analyze_letterhead(self, letterhead_path: str) -> Dict[str, Dict[str, float]]:
        """
        Analyze letterhead PDF to determine safe printable areas
        
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
                page = doc[0]
                # Get text blocks to determine content areas
                blocks = page.get_text("dict")["blocks"]
                
                # Initialize with page dimensions
                page_rect = page.rect
                content_rect = None
                
                # Find content boundaries
                for block in blocks:
                    block_rect = fitz.Rect(block["bbox"])
                    if content_rect is None:
                        content_rect = block_rect
                    else:
                        content_rect = content_rect.include_rect(block_rect)
                
                if content_rect:
                    # Calculate margins based on content boundaries
                    margins['first_page'] = {
                        'top': content_rect.y0,
                        'right': page_rect.width - content_rect.x1,
                        'bottom': page_rect.height - content_rect.y1,
                        'left': content_rect.x0
                    }
                
                # If there's a second page, analyze it for other pages template
                if doc.page_count > 1:
                    page = doc[1]
                    blocks = page.get_text("dict")["blocks"]
                    content_rect = None
                    
                    for block in blocks:
                        block_rect = fitz.Rect(block["bbox"])
                        if content_rect is None:
                            content_rect = block_rect
                        else:
                            content_rect = content_rect.include_rect(block_rect)
                    
                    if content_rect:
                        margins['other_pages'] = {
                            'top': content_rect.y0,
                            'right': page_rect.width - content_rect.x1,
                            'bottom': page_rect.height - content_rect.y1,
                            'left': content_rect.x0
                        }
                else:
                    # If no second page, use first page margins
                    margins['other_pages'] = margins['first_page'].copy()
            
            # Add some padding to ensure we don't overlap with letterhead
            padding = 20  # 20 points padding
            for page_type in margins:
                for edge in margins[page_type]:
                    margins[page_type][edge] += padding
            
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
            
            # Convert to HTML
            html_content = self.md.convert(md_content)
            
            # Analyze letterhead for margins
            margins = self.analyze_letterhead(letterhead_path)
            
            # Create CSS with margins
            margin_css = CSS(string=f'''
                @page:first {{
                    margin-top: {margins['first_page']['top']}pt;
                    margin-right: {margins['first_page']['right']}pt;
                    margin-bottom: {margins['first_page']['bottom']}pt;
                    margin-left: {margins['first_page']['left']}pt;
                }}
                @page {{
                    margin-top: {margins['other_pages']['top']}pt;
                    margin-right: {margins['other_pages']['right']}pt;
                    margin-bottom: {margins['other_pages']['bottom']}pt;
                    margin-left: {margins['other_pages']['left']}pt;
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
                    {html_content}
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
