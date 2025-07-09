#!/usr/bin/env python3

import os
import logging
import tempfile
import urllib.request
import importlib.util
import sys
from typing import Optional, Dict, Tuple, List
import fitz  # PyMuPDF
import re

# Check if markdown is available
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError as e:
    MARKDOWN_AVAILABLE = False
    logging.warning(f"Markdown module not available: {e}. Install with: uvx mac-letterhead@0.8.2")

# Check if WeasyPrint is available and functional
WEASYPRINT_AVAILABLE = False
if importlib.util.find_spec("weasyprint") is not None:
    try:
        # Set library path for WeasyPrint before importing (needed for uvx isolation)
        dyld_fallback_path = os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', '')
        homebrew_lib = '/opt/homebrew/lib'
        if homebrew_lib not in dyld_fallback_path:
            if dyld_fallback_path:
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = f"{homebrew_lib}:{dyld_fallback_path}"
            else:
                os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = homebrew_lib
        
        # Try to import and test WeasyPrint functionality
        from weasyprint import HTML
        # Create a simple test to verify WeasyPrint can actually work
        test_html = HTML(string="<html><body>Test</body></html>")
        # If this doesn't raise an exception, WeasyPrint is functional
        WEASYPRINT_AVAILABLE = True
        logging.info("WeasyPrint is available and functional")
    except Exception as e:
        WEASYPRINT_AVAILABLE = False
        logging.warning(f"WeasyPrint installed but not functional: {e}. Using ReportLab fallback.")

# Check if Pygments is available for syntax highlighting
PYGMENTS_AVAILABLE = importlib.util.find_spec("pygments") is not None
if PYGMENTS_AVAILABLE:
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, guess_lexer
        from pygments.formatters import HtmlFormatter
        logging.info("Pygments available for syntax highlighting")
    except ImportError:
        PYGMENTS_AVAILABLE = False
        logging.warning("Pygments import failed. Code blocks will not have syntax highlighting.")

# Import ReportLab for fallback rendering
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, ListFlowable, ListItem, Preformatted
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# WeasyPrint will be imported later when needed to avoid import errors

# Define point unit (1/72 inch)
pt = 1

class MarkdownProcessor:
    """Handles conversion of Markdown files to PDF with proper formatting"""
    
    def __init__(self):
        """Initialize the Markdown processor with default settings"""
        # Check if markdown is available
        if not MARKDOWN_AVAILABLE:
            raise ImportError("Markdown module not available. Install with: uvx mac-letterhead[markdown]@0.8.0")
            
        # Initialize Markdown with extensions
        extensions = [
            'tables',
            'fenced_code',
            'footnotes',
            'attr_list',
            'def_list',
            'abbr'
        ]
        
        # Add codehilite extension if Pygments is available
        if PYGMENTS_AVAILABLE:
            extensions.append('codehilite')
            
        self.md = markdown.Markdown(extensions=extensions)
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        
        # Temp directory for downloaded images
        self.temp_dir = None
    
    def setup_styles(self):
        """Set up custom styles for PDF generation"""
        # Modify existing styles
        self.styles['Normal'].fontSize = 9
        self.styles['Normal'].leading = 11
        self.styles['Normal'].spaceBefore = 4
        self.styles['Normal'].spaceAfter = 4
        
        # Improve code style
        self.styles['Code'].fontName = 'Courier'
        self.styles['Code'].fontSize = 8
        self.styles['Code'].leading = 10
        self.styles['Code'].backColor = colors.lightgrey
        self.styles['Code'].borderWidth = 1
        self.styles['Code'].borderColor = colors.grey
        self.styles['Code'].borderPadding = 6
        self.styles['Code'].spaceBefore = 6
        self.styles['Code'].spaceAfter = 6
        
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            alignment=TA_LEFT,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        ))
        self.styles.add(ParagraphStyle(
            name='CustomHeading3',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        ))
        self.styles.add(ParagraphStyle(
            name='BulletItem',
            parent=self.styles['Normal'],
            leftIndent=20,
            firstLineIndent=0
        ))
        self.styles.add(ParagraphStyle(
            name='NumberItem',
            parent=self.styles['Normal'],
            leftIndent=20,
            firstLineIndent=0
        ))
        self.styles.add(ParagraphStyle(
            name='Blockquote',
            parent=self.styles['Normal'],
            leftIndent=30,
            rightIndent=30,
            spaceBefore=12,
            spaceAfter=12,
            fontStyle='italic'
        ))

    def analyze_page_regions(self, page):
        """Analyze a page to detect all content regions and page size"""
        page_rect = page.rect
        
        # Determine page size
        width = page_rect.width
        height = page_rect.height
        
        # Determine closest standard size
        if abs(width - 595) <= 1 and abs(height - 842) <= 1:
            page_size = A4
        elif abs(width - 612) <= 1 and abs(height - 792) <= 1:
            page_size = LETTER
        else:
            page_size = A4
            logging.info(f"Non-standard page size detected ({width}x{height}), defaulting to A4")
        
        # Split page into quarters vertically for classification
        top_quarter = page_rect.height / 4
        bottom_quarter = page_rect.height * 3 / 4
        
        # Track all content regions separately
        content_regions = []
        
        # Analyze text blocks
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:  # Text block
                block_rect = fitz.Rect(block["bbox"])
                block_center_y = (block_rect.y0 + block_rect.y1) / 2
                
                # Classify by vertical position
                if block_center_y < top_quarter:
                    region_type = "header"
                elif block_center_y > bottom_quarter:
                    region_type = "footer"
                else:
                    region_type = "middle"
                
                content_regions.append((region_type, block_rect))
                logging.info(f"Text {region_type}: {block_rect}")
        
        # Analyze drawings/graphics
        drawings = page.get_drawings()
        for drawing in drawings:
            drawing_rect = fitz.Rect(drawing["rect"])
            drawing_center_y = (drawing_rect.y0 + drawing_rect.y1) / 2
            
            # Skip very small drawings (likely artifacts)
            if drawing_rect.width < 5 or drawing_rect.height < 5:
                continue
            
            # Skip very large drawings that cover most of the page (likely backgrounds)
            page_area = page_rect.width * page_rect.height
            drawing_area = drawing_rect.width * drawing_rect.height
            area_percentage = (drawing_area / page_area) * 100
            
            if area_percentage > 80:  # Skip drawings covering more than 80% of page
                logging.info(f"Skipping large background drawing: {drawing_rect} ({area_percentage:.1f}% of page)")
                continue
            
            # Skip drawings that span nearly the full width or height (likely borders/backgrounds)
            width_percentage = (drawing_rect.width / page_rect.width) * 100
            height_percentage = (drawing_rect.height / page_rect.height) * 100
            
            if width_percentage > 90 and height_percentage > 90:
                logging.info(f"Skipping full-page drawing: {drawing_rect}")
                continue
            
            # Classify by vertical position
            if drawing_center_y < top_quarter:
                region_type = "header"
            elif drawing_center_y > bottom_quarter:
                region_type = "footer"
            else:
                region_type = "middle"
            
            content_regions.append((region_type, drawing_rect))
            logging.info(f"Drawing {region_type}: {drawing_rect}")
        
        # Analyze images
        images = page.get_images()
        for img_index, img in enumerate(images):
            # Get image placement info
            image_list = page.get_image_rects(img[0])
            for image_rect in image_list:
                image_center_y = (image_rect.y0 + image_rect.y1) / 2
                
                # Classify by vertical position
                if image_center_y < top_quarter:
                    region_type = "header"
                elif image_center_y > bottom_quarter:
                    region_type = "footer"
                else:
                    region_type = "middle"
                
                content_regions.append((region_type, image_rect))
                logging.info(f"Image {region_type}: {image_rect}")
        
        # For backward compatibility, also provide combined regions
        header_rect = None
        footer_rect = None
        middle_rect = None
        
        for region_type, rect in content_regions:
            if region_type == "header":
                header_rect = header_rect.include_rect(rect) if header_rect else rect
            elif region_type == "footer":
                footer_rect = footer_rect.include_rect(rect) if footer_rect else rect
            elif region_type == "middle":
                middle_rect = middle_rect.include_rect(rect) if middle_rect else rect
        
        return {
            'header': header_rect,
            'footer': footer_rect,
            'middle': middle_rect,
            'content_regions': content_regions,  # All individual content regions
            'page_rect': page_rect,
            'page_size': page_size,
            'width': width,
            'height': height
        }

    def analyze_letterhead(self, letterhead_path: str) -> Dict[str, Dict[str, float]]:
        """Analyze letterhead PDF to determine safe printable areas"""
        logging.info(f"Analyzing letterhead margins: {letterhead_path}")
        
        try:
            doc = fitz.open(letterhead_path)
            margins = {
                'first_page': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0},
                'other_pages': {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
            }
            
            if doc.page_count > 0:
                regions = self.analyze_page_regions(doc[0])
                page_rect = regions['page_rect']
                
                margins['first_page'] = self._calculate_smart_margins(regions, page_rect)
                
                if doc.page_count > 1:
                    regions = self.analyze_page_regions(doc[1])
                    margins['other_pages'] = self._calculate_smart_margins(regions, page_rect)
                else:
                    margins['other_pages'] = margins['first_page'].copy()
            
            # Add minimal padding for top and bottom
            for page_type in margins:
                margins[page_type]['top'] += 20
                margins[page_type]['bottom'] += 20
            
            logging.info(f"Detected margins for first page: {margins['first_page']}")
            logging.info(f"Detected margins for other pages: {margins['other_pages']}")
            
            return margins
            
        except Exception as e:
            logging.error(f"Error analyzing letterhead margins: {str(e)}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()

    def _calculate_smart_margins(self, regions: Dict, page_rect) -> Dict[str, float]:
        """Calculate margins using comprehensive content analysis including middle blocks"""
        content_regions = regions.get('content_regions', [])
        
        # Default margins (standard document margins)
        default_margin = 72  # 1 inch in points
        min_margin = 36      # 0.5 inch minimum
        safe_padding = 20    # Safe distance from letterhead content
        
        page_width = page_rect.width
        page_height = page_rect.height
        
        # Start with default printable area
        printable_rect = fitz.Rect(
            default_margin,  # left
            default_margin,  # top
            page_width - default_margin,   # right
            page_height - default_margin   # bottom
        )
        
        logging.info(f"Initial printable area: {printable_rect}")
        
        # Adjust for each content region
        for region_type, content_rect in content_regions:
            if printable_rect.intersects(content_rect):
                logging.info(f"Content overlaps printable area: {region_type} at {content_rect}")
                printable_rect = self._adjust_printable_area(printable_rect, content_rect, page_rect)
        
        # Ensure minimum printable area
        min_width = page_width * 0.3  # At least 30% of page width
        min_height = page_height * 0.3  # At least 30% of page height
        
        if printable_rect.width < min_width or printable_rect.height < min_height:
            logging.warning(f"Printable area too small: {printable_rect.width}x{printable_rect.height}")
            # Fall back to centered rectangle with minimum size
            center_x = page_width / 2
            center_y = page_height / 2
            printable_rect = fitz.Rect(
                center_x - min_width/2,
                center_y - min_height/2,
                center_x + min_width/2,
                center_y + min_height/2
            )
        
        # Convert printable rectangle to margins
        left_margin = max(min_margin, printable_rect.x0)
        top_margin = max(min_margin, printable_rect.y0)
        right_margin = max(min_margin, page_width - printable_rect.x1)
        bottom_margin = max(min_margin, page_height - printable_rect.y1)
        
        # Log the effective printable area
        final_printable_width = page_width - left_margin - right_margin
        final_printable_height = page_height - top_margin - bottom_margin
        usable_percentage = (final_printable_width * final_printable_height) / (page_width * page_height) * 100
        
        logging.info(f"Final printable area: {final_printable_width:.1f}x{final_printable_height:.1f}pt ({usable_percentage:.1f}% of page)")
        logging.info(f"Margins: top={top_margin:.1f}, right={right_margin:.1f}, bottom={bottom_margin:.1f}, left={left_margin:.1f}")
        
        return {
            'top': top_margin,
            'right': right_margin,
            'bottom': bottom_margin,
            'left': left_margin
        }
    
    def _adjust_printable_area(self, printable_rect: fitz.Rect, content_rect: fitz.Rect, page_rect: fitz.Rect) -> fitz.Rect:
        """Adjust printable area to avoid overlapping with content"""
        safe_padding = 20
        
        # Calculate possible adjustments
        adjustments = []
        
        # Option 1: Move left boundary right (avoid content on left)
        if content_rect.x1 + safe_padding < page_rect.width * 0.8:
            new_rect = fitz.Rect(
                max(printable_rect.x0, content_rect.x1 + safe_padding),
                printable_rect.y0,
                printable_rect.x1,
                printable_rect.y1
            )
            if new_rect.width > 0:
                adjustments.append(new_rect)
        
        # Option 2: Move right boundary left (avoid content on right)
        if content_rect.x0 - safe_padding > page_rect.width * 0.2:
            new_rect = fitz.Rect(
                printable_rect.x0,
                printable_rect.y0,
                min(printable_rect.x1, content_rect.x0 - safe_padding),
                printable_rect.y1
            )
            if new_rect.width > 0:
                adjustments.append(new_rect)
        
        # Option 3: Move top boundary down (avoid content above)
        if content_rect.y1 + safe_padding < page_rect.height * 0.8:
            new_rect = fitz.Rect(
                printable_rect.x0,
                max(printable_rect.y0, content_rect.y1 + safe_padding),
                printable_rect.x1,
                printable_rect.y1
            )
            if new_rect.height > 0:
                adjustments.append(new_rect)
        
        # Option 4: Move bottom boundary up (avoid content below)
        if content_rect.y0 - safe_padding > page_rect.height * 0.2:
            new_rect = fitz.Rect(
                printable_rect.x0,
                printable_rect.y0,
                printable_rect.x1,
                min(printable_rect.y1, content_rect.y0 - safe_padding)
            )
            if new_rect.height > 0:
                adjustments.append(new_rect)
        
        # Choose the adjustment that preserves the most area
        if adjustments:
            best_rect = max(adjustments, key=lambda r: r.width * r.height)
            logging.info(f"Adjusted printable area from {printable_rect} to {best_rect}")
            return best_rect
        
        # If no good adjustment found, return original
        return printable_rect

    def extract_images(self, html_content):
        """Extract images from HTML content and return cleaned content"""
        # Find all image tags
        img_pattern = re.compile(r'<img[^>]+>')
        img_tags = img_pattern.findall(html_content)
        
        # Extract image sources
        images = []
        for img_tag in img_tags:
            src_match = re.search(r'src="([^"]+)"', img_tag)
            if src_match:
                src = src_match.group(1)
                # Only include local images
                if not src.startswith(('http://', 'https://')):
                    images.append(src)
            
            # Remove the image tag from the content
            html_content = html_content.replace(img_tag, '')
        
        return html_content, images

    def clean_html_for_reportlab(self, html_content):
        """Clean HTML content to be compatible with ReportLab"""
        # Remove Pygments code highlighting divs and spans - they're not compatible with ReportLab
        # Replace codehilite divs with simple pre tags
        html_content = re.sub(r'<div class="codehilite"><pre><span></span>(.*?)</pre></div>', 
                             r'<pre>\1</pre>', html_content, flags=re.DOTALL)
        
        # Remove all span elements with class attributes (from Pygments)
        html_content = re.sub(r'<span[^>]*class="[^"]*"[^>]*>(.*?)</span>', r'\1', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', html_content, flags=re.DOTALL)
        
        # Remove any remaining div tags with classes
        html_content = re.sub(r'<div[^>]*class="[^"]*"[^>]*>(.*?)</div>', r'\1', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<div[^>]*>(.*?)</div>', r'\1', html_content, flags=re.DOTALL)
        
        # Clean links - remove title and other attributes
        link_pattern = re.compile(r'<a\s+([^>]+)>')
        
        def clean_link(match):
            attrs = match.group(1)
            # Keep only href attribute
            href_match = re.search(r'href="([^"]+)"', attrs)
            if href_match:
                href = href_match.group(1)
                return f'<a href="{href}">'
            return '<a>'
        
        html_content = link_pattern.sub(clean_link, html_content)
        
        # Convert HTML formatting to ReportLab formatting
        html_content = html_content.replace('<strong>', '<b>').replace('</strong>', '</b>')
        html_content = html_content.replace('<em>', '<i>').replace('</em>', '</i>')
        
        # Handle inline code tags more carefully
        html_content = re.sub(r'<code[^>]*>(.*?)</code>', r'<font face="Courier">\1</font>', html_content)
        
        # Remove any remaining class attributes from any tags
        html_content = re.sub(r'(\s+class="[^"]*")', '', html_content)
        
        return html_content

    def process_list_items(self, list_type, lines, start_index):
        """Process list items and return a list of items and the new index"""
        items = []
        i = start_index
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('<li>'):
                # Extract text from list item
                text = line.replace('<li>', '').replace('</li>', '')
                
                # Handle multi-line list items
                j = i + 1
                while j < len(lines) and not lines[j].strip().endswith('</li>') and not lines[j].strip() == '</ul>' and not lines[j].strip() == '</ol>':
                    text += ' ' + lines[j].strip()
                    j += 1
                
                if j < len(lines) and lines[j].strip().endswith('</li>'):
                    text += ' ' + lines[j].strip().replace('</li>', '')
                    i = j
                
                # Convert HTML formatting
                text = text.replace('<strong>', '<b>').replace('</strong>', '</b>')
                text = text.replace('<em>', '<i>').replace('</em>', '</i>')
                text = text.replace('<code>', '<font face="Courier">').replace('</code>', '</font>')
                
                # Check for nested lists
                if '<ul>' in text or '<ol>' in text:
                    # Handle nested lists later
                    pass
                
                items.append(text)
            
            elif line == '</ul>' or line == '</ol>':
                break
            
            i += 1
        
        return items, i

    def markdown_to_flowables(self, html_content: str) -> list:
        """Convert HTML content from markdown to reportlab flowables"""
        # Create list of flowables
        flowables = []
        
        # Extract images first to avoid parsing issues
        html_content, images = self.extract_images(html_content)
        
        # Clean HTML for ReportLab compatibility
        html_content = self.clean_html_for_reportlab(html_content)
        
        # Add local images as separate flowables if they exist
        for img_src in images:
            try:
                # Local image
                img_obj = Image(img_src)
                img_obj.drawHeight = 0.5 * inch  # Even smaller height
                img_obj.drawWidth = 0.5 * inch * (img_obj.imageWidth / img_obj.imageHeight)
                flowables.append(img_obj)
                flowables.append(Spacer(1, 6))  # Smaller spacer
            except Exception as e:
                logging.warning(f"Failed to load local image {img_src}: {e}")
        
        # Process HTML content line by line to identify elements
        lines = html_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Headers
            if line.startswith('<h1>'):
                text = line.replace('<h1>', '').replace('</h1>', '')
                flowables.append(Paragraph(text, self.styles['CustomHeading1']))
                flowables.append(Spacer(1, 6))
            
            elif line.startswith('<h2>'):
                text = line.replace('<h2>', '').replace('</h2>', '')
                flowables.append(Paragraph(text, self.styles['CustomHeading2']))
                flowables.append(Spacer(1, 4))
            
            elif line.startswith('<h3>'):
                text = line.replace('<h3>', '').replace('</h3>', '')
                flowables.append(Paragraph(text, self.styles['CustomHeading3']))
                flowables.append(Spacer(1, 4))
            
            # Paragraphs
            elif line.startswith('<p>'):
                text = line.replace('<p>', '').replace('</p>', '')
                # Handle multi-line paragraphs
                j = i + 1
                while j < len(lines) and not lines[j].strip().endswith('</p>'):
                    text += ' ' + lines[j].strip()
                    j += 1
                if j < len(lines) and lines[j].strip().endswith('</p>'):
                    text += ' ' + lines[j].strip().replace('</p>', '')
                    i = j
                
                # Add paragraph text
                if text.strip():
                    flowables.append(Paragraph(text, self.styles['Normal']))
                    flowables.append(Spacer(1, 6))
            
            # Lists - improved handling
            elif line.startswith('<ul>'):
                items, i = self.process_list_items('bullet', lines, i + 1)
                
                # Create bullet list
                bullet_list = []
                for item_text in items:
                    bullet_list.append(ListItem(Paragraph(item_text, self.styles['BulletItem']), leftIndent=20))
                
                flowables.append(ListFlowable(
                    bullet_list,
                    bulletType='bullet',
                    start=0,
                    bulletFontName='Helvetica',
                    bulletFontSize=10,
                    leftIndent=20,
                    spaceBefore=6,
                    spaceAfter=6
                ))
            
            elif line.startswith('<ol>'):
                items, i = self.process_list_items('number', lines, i + 1)
                
                # Create numbered list
                number_list = []
                for item_text in items:
                    number_list.append(ListItem(Paragraph(item_text, self.styles['NumberItem']), leftIndent=20))
                
                flowables.append(ListFlowable(
                    number_list,
                    bulletType='1',
                    start=1,
                    bulletFontName='Helvetica',
                    bulletFontSize=10,
                    leftIndent=20,
                    spaceBefore=6,
                    spaceAfter=6
                ))
            
            # Code blocks - improved styling
            elif line.startswith('<pre>'):
                code = []
                j = i
                while j < len(lines) and not lines[j].strip().endswith('</pre>'):
                    if j > i:  # Skip the opening <pre> tag
                        code.append(lines[j])
                    j += 1
                if j < len(lines) and lines[j].strip().endswith('</pre>'):
                    code.append(lines[j].replace('</pre>', ''))
                    i = j
                
                code_text = '\n'.join(code).replace('<code>', '').replace('</code>', '')
                # Use Preformatted for better code block rendering
                flowables.append(Preformatted(code_text, self.styles['Code']))
                flowables.append(Spacer(1, 8))
            
            # Tables
            elif line.startswith('<table>'):
                data = []
                j = i + 1
                while j < len(lines) and not lines[j].strip() == '</table>':
                    if lines[j].strip().startswith('<tr>'):
                        row = []
                        k = j + 1
                        while k < len(lines) and not lines[k].strip() == '</tr>':
                            if lines[k].strip().startswith('<td>') or lines[k].strip().startswith('<th>'):
                                cell_text = lines[k].strip()
                                cell_text = cell_text.replace('<td>', '').replace('</td>', '')
                                cell_text = cell_text.replace('<th>', '').replace('</th>', '')
                                row.append(cell_text)
                            k += 1
                        j = k
                        if row:
                            data.append(row)
                    j += 1
                i = j
                
                if data:
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6)
                    ]))
                    flowables.append(table)
                    flowables.append(Spacer(1, 12))
            
            # Blockquotes
            elif line.startswith('<blockquote>'):
                text = []
                j = i + 1
                while j < len(lines) and not lines[j].strip() == '</blockquote>':
                    if lines[j].strip().startswith('<p>'):
                        p_text = lines[j].strip().replace('<p>', '').replace('</p>', '')
                        text.append(p_text)
                    j += 1
                i = j
                
                if text:
                    quote_text = ' '.join(text)
                    flowables.append(Paragraph(quote_text, self.styles['Blockquote']))
                    flowables.append(Spacer(1, 6))
            
            i += 1
        
        # If no content was added, add a blank paragraph
        if not flowables:
            flowables.append(Paragraph("", self.styles['Normal']))
        
        logging.info(f"Generated {len(flowables)} flowables")
        return flowables

    def md_to_pdf(self, md_path: str, output_path: str, letterhead_path: str) -> str:
        """Convert markdown file to PDF with proper margins based on letterhead"""
        logging.info(f"Converting markdown to PDF: {md_path} -> {output_path}")
        
        try:
            # Read markdown content
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convert to HTML
            html_content = self.md.convert(md_content)
            logging.info("Generated HTML content")
            
            # Analyze letterhead for margins and page size
            doc = fitz.open(letterhead_path)
            try:
                first_page = doc[0]
                regions = self.analyze_page_regions(first_page)
                margins = self.analyze_letterhead(letterhead_path)
                page_size = regions['page_size']
            finally:
                doc.close()
            
            # Create temporary file for initial PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                if WEASYPRINT_AVAILABLE:
                    # Use WeasyPrint for high-quality PDF generation
                    self._md_to_pdf_weasyprint(html_content, temp_pdf.name, margins, page_size)
                else:
                    # Fallback to ReportLab
                    self._md_to_pdf_reportlab(html_content, temp_pdf.name, margins, page_size)
                
                # Create final PDF with metadata
                pdf = fitz.open(temp_pdf.name)
                try:
                    pdf.set_metadata({
                        'title': os.path.basename(md_path),
                        'author': 'Mac-letterhead',
                        'creator': 'Mac-letterhead',
                        'producer': 'Mac-letterhead'
                    })
                    pdf.save(output_path)
                finally:
                    pdf.close()
            
            # Clean up temporary files
            os.unlink(temp_pdf.name)
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error converting markdown to PDF: {str(e)}")
            raise
    
    def _md_to_pdf_weasyprint(self, html_content, output_path, margins, page_size):
        """Convert HTML to PDF using WeasyPrint"""
        logging.info("Using WeasyPrint for PDF generation")
        
        # Import WeasyPrint components when needed
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Generate Pygments CSS for syntax highlighting if available
        pygments_css = ""
        if PYGMENTS_AVAILABLE:
            pygments_css = HtmlFormatter().get_style_defs('.codehilite')
            logging.info("Added Pygments CSS for syntax highlighting")
        
        # Create a basic HTML document with the content
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Markdown Document</title>
            <style>
                @page {{
                    margin-top: {margins['first_page']['top']}pt;
                    margin-right: {margins['first_page']['right']}pt;
                    margin-bottom: {margins['first_page']['bottom']}pt;
                    margin-left: {margins['first_page']['left']}pt;
                    @bottom-center {{
                        content: counter(page);
                    }}
                }}
                
                /* Basic styling */
                body {{
                    font-family: Helvetica, Arial, sans-serif;
                    font-size: 9pt;  /* Smaller base font size */
                    line-height: 1.3;
                    max-width: 100%;
                    margin: 0;
                    padding: 0;
                }}
                
                /* Headings */
                h1 {{ font-size: 14pt; margin-top: 12pt; margin-bottom: 6pt; }}
                h2 {{ font-size: 12pt; margin-top: 10pt; margin-bottom: 4pt; }}
                h3 {{ font-size: 10pt; margin-top: 8pt; margin-bottom: 4pt; }}
                
                /* Paragraphs */
                p {{ margin-top: 4pt; margin-bottom: 4pt; }}
                
                /* Code blocks with wrapping */
                pre {{ 
                    background-color: #f5f5f5; 
                    border: 1px solid #ccc; 
                    padding: 8pt; 
                    font-family: Courier, monospace;
                    font-size: 9pt;
                    white-space: pre-wrap;       /* CSS3 */
                    word-wrap: break-word;       /* IE */
                    overflow-wrap: break-word;
                    margin: 8pt 0;
                }}
                
                /* Inline code */
                code {{ 
                    font-family: Courier, monospace;
                    background-color: #f5f5f5;
                    padding: 1pt 3pt;
                    border-radius: 3pt;
                }}
                
                /* Blockquotes */
                blockquote {{
                    margin-left: 30pt;
                    margin-right: 30pt;
                    font-style: italic;
                    border-left: 3pt solid #ccc;
                    padding-left: 10pt;
                }}
                
                /* Tables */
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 12pt;
                    margin-bottom: 12pt;
                }}
                th, td {{
                    border: 0.25pt solid black;
                    padding: 6pt;
                }}
                th {{ background-color: #f0f0f0; }}
                
                /* Lists */
                ul, ol {{
                    margin-top: 6pt;
                    margin-bottom: 6pt;
                }}
                li {{
                    margin-bottom: 3pt;
                }}
                
                /* Syntax highlighting from Pygments */
                {pygments_css}
                
                /* Fix for code blocks to prevent double borders and extra spacing */
                .codehilite {{
                    background-color: transparent;
                    border: none;
                    padding: 0;
                    margin: 0;
                    overflow-x: auto;
                }}
                
                .codehilite pre {{
                    margin: 0;
                    padding: 8pt;
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }}
                
                /* Fix for command line code blocks */
                .codehilite .gp {{ /* Prompt */
                    padding-right: 4pt;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Convert HTML to PDF
        html = HTML(string=html_template)
        html.write_pdf(output_path, font_config=font_config)
    
    def _md_to_pdf_reportlab(self, html_content, output_path, margins, page_size):
        """Convert HTML to PDF using ReportLab (fallback method)"""
        logging.info("Using ReportLab for PDF generation")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            leftMargin=margins['first_page']['left'],
            rightMargin=margins['first_page']['right'],
            topMargin=margins['first_page']['top'],
            bottomMargin=margins['first_page']['bottom'],
            allowSplitting=True,
            displayDocTitle=True,
            pageCompression=0
        )
        
        # Convert HTML to reportlab flowables
        flowables = self.markdown_to_flowables(html_content)
        
        # Build PDF
        doc.build(flowables)
