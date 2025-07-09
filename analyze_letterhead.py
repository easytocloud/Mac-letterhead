#!/usr/bin/env python3

import sys
import os
import fitz  # PyMuPDF
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class LetterheadAnalyzer:
    """Analyzes letterhead PDFs to find optimal printable space"""
    
    def __init__(self):
        self.default_margin = 72  # 1 inch in points
        self.min_margin = 36      # 0.5 inch minimum
        self.safe_padding = 20    # Safe distance from letterhead content
    
    def analyze_letterhead(self, letterhead_path: str, output_path: str):
        """Analyze letterhead and create visualization of printable space"""
        logging.info(f"Analyzing letterhead: {letterhead_path}")
        
        # Open the letterhead PDF
        letterhead_doc = fitz.open(letterhead_path)
        
        # Create output document
        output_doc = fitz.open()
        
        try:
            # Analyze each page
            for page_num in range(letterhead_doc.page_count):
                logging.info(f"Analyzing page {page_num + 1}")
                letterhead_page = letterhead_doc[page_num]
                
                # Get page dimensions
                page_rect = letterhead_page.rect
                
                # Find all content regions
                content_regions = self._find_content_regions(letterhead_page)
                
                # Calculate optimal printable space
                printable_rect = self._calculate_printable_space(page_rect, content_regions)
                
                # Create visualization page
                output_page = output_doc.new_page(width=page_rect.width, height=page_rect.height)
                
                # Copy original letterhead content
                output_page.show_pdf_page(page_rect, letterhead_doc, page_num)
                
                # Draw printable space as light grey rectangle
                self._draw_printable_space(output_page, printable_rect, content_regions)
                
                # Add analysis info
                self._add_analysis_info(output_page, page_rect, printable_rect, content_regions)
            
            # Save the analysis
            output_doc.save(output_path)
            logging.info(f"Analysis saved to: {output_path}")
            
        finally:
            letterhead_doc.close()
            output_doc.close()
    
    def _find_content_regions(self, page) -> List[Tuple[str, fitz.Rect]]:
        """Find all content regions on the page"""
        content_regions = []
        page_rect = page.rect
        
        # Define page quarters for classification
        top_quarter = page_rect.height / 4
        bottom_quarter = page_rect.height * 3 / 4
        
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
        
        return content_regions
    
    def _calculate_printable_space(self, page_rect: fitz.Rect, content_regions: List[Tuple[str, fitz.Rect]]) -> fitz.Rect:
        """Calculate the largest printable rectangle that doesn't overlap letterhead content"""
        
        # Start with default margins
        initial_rect = fitz.Rect(
            self.default_margin,  # left
            self.default_margin,  # top
            page_rect.width - self.default_margin,   # right
            page_rect.height - self.default_margin   # bottom
        )
        
        logging.info(f"Initial printable area: {initial_rect}")
        
        # Adjust boundaries to avoid letterhead content
        adjusted_rect = initial_rect
        
        for region_type, content_rect in content_regions:
            # Check if content overlaps with current printable area
            if adjusted_rect.intersects(content_rect):
                logging.info(f"Content overlaps printable area: {region_type} at {content_rect}")
                
                # Determine how to adjust the printable area
                adjusted_rect = self._adjust_printable_area(adjusted_rect, content_rect, page_rect)
        
        # Ensure minimum printable area
        min_width = page_rect.width * 0.3  # At least 30% of page width
        min_height = page_rect.height * 0.3  # At least 30% of page height
        
        if adjusted_rect.width < min_width or adjusted_rect.height < min_height:
            logging.warning(f"Printable area too small: {adjusted_rect.width}x{adjusted_rect.height}")
            # Fall back to a centered rectangle with minimum size
            center_x = page_rect.width / 2
            center_y = page_rect.height / 2
            adjusted_rect = fitz.Rect(
                center_x - min_width/2,
                center_y - min_height/2,
                center_x + min_width/2,
                center_y + min_height/2
            )
        
        usable_percentage = (adjusted_rect.width * adjusted_rect.height) / (page_rect.width * page_rect.height) * 100
        logging.info(f"Final printable area: {adjusted_rect} ({usable_percentage:.1f}% of page)")
        
        return adjusted_rect
    
    def _adjust_printable_area(self, printable_rect: fitz.Rect, content_rect: fitz.Rect, page_rect: fitz.Rect) -> fitz.Rect:
        """Adjust printable area to avoid overlapping with content"""
        
        # Calculate possible adjustments
        adjustments = []
        
        # Option 1: Move left boundary right (avoid content on left)
        if content_rect.x1 + self.safe_padding < page_rect.width * 0.8:
            new_rect = fitz.Rect(
                max(printable_rect.x0, content_rect.x1 + self.safe_padding),
                printable_rect.y0,
                printable_rect.x1,
                printable_rect.y1
            )
            if new_rect.width > 0:
                adjustments.append(new_rect)
        
        # Option 2: Move right boundary left (avoid content on right)
        if content_rect.x0 - self.safe_padding > page_rect.width * 0.2:
            new_rect = fitz.Rect(
                printable_rect.x0,
                printable_rect.y0,
                min(printable_rect.x1, content_rect.x0 - self.safe_padding),
                printable_rect.y1
            )
            if new_rect.width > 0:
                adjustments.append(new_rect)
        
        # Option 3: Move top boundary down (avoid content above)
        if content_rect.y1 + self.safe_padding < page_rect.height * 0.8:
            new_rect = fitz.Rect(
                printable_rect.x0,
                max(printable_rect.y0, content_rect.y1 + self.safe_padding),
                printable_rect.x1,
                printable_rect.y1
            )
            if new_rect.height > 0:
                adjustments.append(new_rect)
        
        # Option 4: Move bottom boundary up (avoid content below)
        if content_rect.y0 - self.safe_padding > page_rect.height * 0.2:
            new_rect = fitz.Rect(
                printable_rect.x0,
                printable_rect.y0,
                printable_rect.x1,
                min(printable_rect.y1, content_rect.y0 - self.safe_padding)
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
    
    def _draw_printable_space(self, page, printable_rect: fitz.Rect, content_regions: List[Tuple[str, fitz.Rect]]):
        """Draw the printable space and content regions on the page"""
        
        # Draw printable space as light grey rectangle
        page.draw_rect(printable_rect, color=(0.8, 0.8, 0.8), fill=(0.9, 0.9, 0.9), width=1)
        
        # Draw content regions with different colors
        colors = {
            'header': (1, 0.8, 0.8),      # Light red
            'footer': (0.8, 0.8, 1),      # Light blue  
            'middle': (1, 1, 0.8)         # Light yellow
        }
        
        for region_type, content_rect in content_regions:
            color = colors.get(region_type, (0.8, 0.8, 0.8))
            page.draw_rect(content_rect, color=(0.5, 0.5, 0.5), fill=color, width=0.5)
    
    def _add_analysis_info(self, page, page_rect: fitz.Rect, printable_rect: fitz.Rect, content_regions: List[Tuple[str, fitz.Rect]]):
        """Add analysis information as text on the page"""
        
        # Calculate statistics
        total_area = page_rect.width * page_rect.height
        printable_area = printable_rect.width * printable_rect.height
        usable_percentage = (printable_area / total_area) * 100
        
        # Create info text
        info_lines = [
            f"Letterhead Analysis",
            f"Page: {page_rect.width:.0f}x{page_rect.height:.0f}pt",
            f"Printable: {printable_rect.width:.0f}x{printable_rect.height:.0f}pt",
            f"Usable: {usable_percentage:.1f}% of page",
            f"Content regions: {len(content_regions)}",
            "",
            "Legend:",
            "Grey = Printable space",
            "Red = Header content", 
            "Blue = Footer content",
            "Yellow = Middle content"
        ]
        
        # Add text in bottom right corner
        y_pos = page_rect.height - 20
        for line in info_lines:
            if line:  # Skip empty lines
                page.insert_text(
                    (page_rect.width - 200, y_pos),
                    line,
                    fontsize=8,
                    color=(0, 0, 0)
                )
            y_pos -= 12

def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze_letterhead.py <letterhead.pdf> <output.pdf>")
        print("Example: python analyze_letterhead.py easy.pdf easy_analysis.pdf")
        sys.exit(1)
    
    letterhead_path = sys.argv[1]
    output_path = sys.argv[2]
    
    if not os.path.exists(letterhead_path):
        print(f"Error: Letterhead file not found: {letterhead_path}")
        sys.exit(1)
    
    try:
        analyzer = LetterheadAnalyzer()
        analyzer.analyze_letterhead(letterhead_path, output_path)
        print(f"Analysis complete! Check: {output_path}")
        
    except Exception as e:
        print(f"Error analyzing letterhead: {e}")
        logging.exception("Full error details:")
        sys.exit(1)

if __name__ == "__main__":
    main()
