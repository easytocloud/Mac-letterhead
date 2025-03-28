#!/usr/bin/env python3

import os
import logging
from typing import Optional, Dict, Any, Tuple
from Quartz import CoreGraphics

from letterhead_pdf.pdf_utils import create_pdf_document, create_output_context, get_doc_info
from letterhead_pdf.exceptions import PDFMergeError, PDFCreationError, PDFMetadataError

class PDFMerger:
    """Handles merging of letterhead and content PDFs"""
    
    def __init__(self, letterhead_path: str):
        """
        Initialize PDFMerger with a letterhead PDF path
        
        Args:
            letterhead_path: Path to the letterhead PDF template
        """
        self.letterhead_path = os.path.expanduser(letterhead_path)
        logging.info(f"Initializing PDFMerger with template: {self.letterhead_path}")

    def merge(self, input_path: str, output_path: str, strategy: str = "darken") -> None:
        """
        Merge letterhead with input PDF using the specified strategy
        
        Args:
            input_path: Path to the content PDF
            output_path: Path to save the merged PDF
            strategy: Merging strategy to use (overlay, multiply, transparency, etc.)
        
        Raises:
            FileNotFoundError: If input files don't exist
            PermissionError: If there are permission issues
            PDFCreationError: If PDF creation fails
            PDFMetadataError: If metadata extraction fails
            PDFMergeError: For other merge operation failures
        """
        # Validate strategy
        valid_strategies = ["multiply", "transparency", "reverse", "overlay", "darken"]
        if strategy not in valid_strategies:
            error_msg = f"Invalid strategy: {strategy}. Must be one of: {', '.join(valid_strategies)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Expand paths
        input_path = os.path.expanduser(input_path)
        output_path = os.path.expanduser(output_path)
        
        # Validate input file
        if not os.path.isfile(input_path):
            error_msg = f"Input file not found: {input_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        # Validate letterhead
        if not os.path.isfile(self.letterhead_path):
            error_msg = f"Letterhead template not found: {self.letterhead_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            logging.info(f"Starting PDF merge with strategy '{strategy}': {input_path} -> {output_path}")
            logging.info(f"Using letterhead: {self.letterhead_path}")
            
            metadata = get_doc_info(input_path)
            write_context = create_output_context(output_path, metadata)
            read_pdf = create_pdf_document(input_path)
            letterhead_pdf = create_pdf_document(self.letterhead_path)

            if not all([write_context, read_pdf, letterhead_pdf]):
                error_msg = "Failed to create PDF context or load PDFs"
                logging.error(error_msg)
                raise PDFMergeError(error_msg)

            # Get page counts for both PDFs
            num_pages = CoreGraphics.CGPDFDocumentGetNumberOfPages(read_pdf)
            num_letterhead_pages = CoreGraphics.CGPDFDocumentGetNumberOfPages(letterhead_pdf)
            
            logging.info(f"Processing {num_pages} content pages with {num_letterhead_pages} letterhead pages")
            
            # Process each page of the content document
            for page_num in range(1, num_pages + 1):
                logging.info(f"Processing page {page_num}")
                page = CoreGraphics.CGPDFDocumentGetPage(read_pdf, page_num)
                
                # Select the appropriate letterhead page based on the number of letterhead pages
                # and the current page number
                if num_letterhead_pages == 1:
                    # Single page letterhead: Use on all pages
                    letterhead_page_num = 1
                elif num_letterhead_pages == 2:
                    # Two page letterhead: First page on first page, second page on all other pages
                    letterhead_page_num = 1 if page_num == 1 else 2
                elif num_letterhead_pages == 3:
                    # Three page letterhead: 
                    # - First page on first page
                    # - Second page on all even pages (except first if it's even)
                    # - Third page on all odd pages (except first if it's odd)
                    if page_num == 1:
                        letterhead_page_num = 1
                    elif page_num % 2 == 0:  # Even page
                        letterhead_page_num = 2
                    else:  # Odd page other than first
                        letterhead_page_num = 3
                else:
                    # For more than 3 pages or any other case, just use first page
                    letterhead_page_num = 1
                
                letterhead_page = CoreGraphics.CGPDFDocumentGetPage(letterhead_pdf, letterhead_page_num)
                
                if not page or not letterhead_page:
                    error_msg = f"Failed to get page {page_num} with letterhead page {letterhead_page_num}"
                    logging.error(error_msg)
                    raise PDFMergeError(error_msg)
                
                media_box = CoreGraphics.CGPDFPageGetBoxRect(page, CoreGraphics.kCGPDFMediaBox)
                if CoreGraphics.CGRectIsEmpty(media_box):
                    media_box = None
                
                CoreGraphics.CGContextBeginPage(write_context, media_box)
                
                # Apply the selected merge strategy
                if strategy == "multiply":
                    self._strategy_multiply(write_context, page, letterhead_page)
                elif strategy == "transparency":
                    self._strategy_transparency(write_context, page, letterhead_page)
                elif strategy == "reverse":
                    self._strategy_reverse(write_context, page, letterhead_page)
                elif strategy == "overlay":
                    self._strategy_overlay(write_context, page, letterhead_page)
                elif strategy == "darken":
                    self._strategy_darken(write_context, page, letterhead_page)
                else:
                    # Default strategy - darken blend mode
                    self._strategy_darken(write_context, page, letterhead_page)
                
                CoreGraphics.CGContextEndPage(write_context)
            
            CoreGraphics.CGPDFContextClose(write_context)
            logging.info("PDF merge completed successfully")

        except PDFCreationError as e:
            # Specific handling for PDF creation errors
            error_msg = f"Failed to create PDF components: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg) from e
        except (FileNotFoundError, PermissionError) as e:
            # Handle file access errors
            error_msg = f"File access error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg) from e
        except Exception as e:
            # Fallback for unexpected errors
            error_msg = f"Unexpected error merging PDFs: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg) from e

    def _strategy_multiply(self, context, content_page, letterhead_page):
        """
        Original strategy - draw letterhead first with multiply blend, then content
        
        This is similar to the original implementation but with more explicit control.
        """
        # Draw letterhead first with multiply blend mode
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeMultiply)
        CoreGraphics.CGContextDrawPDFPage(context, letterhead_page)
        CoreGraphics.CGContextRestoreGState(context)
        
        # Draw content on top with normal blend mode
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeNormal)
        CoreGraphics.CGContextDrawPDFPage(context, content_page)
        CoreGraphics.CGContextRestoreGState(context)

    def _strategy_reverse(self, context, content_page, letterhead_page):
        """
        Reverse strategy - draw content first, then letterhead on top with blend mode
        
        This reverses the drawing order which may help with visibility of the letterhead.
        """
        # Draw content first
        CoreGraphics.CGContextDrawPDFPage(context, content_page)
        
        # Draw letterhead on top with multiply blend mode and partial transparency
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeMultiply)
        CoreGraphics.CGContextSetAlpha(context, 0.8)  # 80% opacity
        CoreGraphics.CGContextDrawPDFPage(context, letterhead_page)
        CoreGraphics.CGContextRestoreGState(context)

    def _strategy_transparency(self, context, content_page, letterhead_page):
        """
        Transparency strategy - use transparency layer for better blending
        
        Creates a transparency group which may provide better results for complex blending.
        """
        # Begin transparency layer
        CoreGraphics.CGContextBeginTransparencyLayer(context, None)
        
        # Draw letterhead
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeNormal)
        CoreGraphics.CGContextDrawPDFPage(context, letterhead_page)
        CoreGraphics.CGContextRestoreGState(context)
        
        # Draw content with suitable blend mode
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeOverlay)
        CoreGraphics.CGContextDrawPDFPage(context, content_page)
        CoreGraphics.CGContextRestoreGState(context)
        
        # End transparency layer
        CoreGraphics.CGContextEndTransparencyLayer(context)

    def _strategy_overlay(self, context, content_page, letterhead_page):
        """
        Overlay strategy - uses overlay blend mode for better visibility
        
        The overlay blend mode often works well for watermarks and letterheads as it
        preserves contrast while allowing the letterhead to show through.
        """
        # Draw letterhead first
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetAlpha(context, 0.9)  # Slightly transparent
        CoreGraphics.CGContextDrawPDFPage(context, letterhead_page)
        CoreGraphics.CGContextRestoreGState(context)
        
        # Draw content with overlay blend mode
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeOverlay)
        CoreGraphics.CGContextDrawPDFPage(context, content_page)
        CoreGraphics.CGContextRestoreGState(context)

    def _strategy_darken(self, context, content_page, letterhead_page):
        """
        Darken strategy - modified to combine normal content with letterhead 
        that's set to a different blend mode
        
        This approach better preserves the content's readability while still showing
        the letterhead.
        """
        # First, draw the content page with normal blend mode
        CoreGraphics.CGContextSaveGState(context)
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeNormal)
        CoreGraphics.CGContextDrawPDFPage(context, content_page)
        CoreGraphics.CGContextRestoreGState(context)
        
        # Then draw the letterhead with lighter blend mode and some transparency
        CoreGraphics.CGContextSaveGState(context)
        # Try a more compatible blend mode than Darken
        CoreGraphics.CGContextSetBlendMode(context, CoreGraphics.kCGBlendModeMultiply)
        # Add some transparency to ensure content remains readable
        CoreGraphics.CGContextSetAlpha(context, 0.9)  # 90% opacity
        CoreGraphics.CGContextDrawPDFPage(context, letterhead_page)
        CoreGraphics.CGContextRestoreGState(context)
