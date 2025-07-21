#!/usr/bin/env python3

"""
Optimized HTML parsing implementation for MarkdownProcessor.

This module contains the optimized HTML parsing methods that replace the manual 
line-by-line parsing with DOM-based parsing using html5lib.
"""

def add_optimized_methods_to_markdown_processor(processor_class):
    """Add optimized HTML parsing methods to MarkdownProcessor class"""
    
    def markdown_to_flowables(self, html_content: str) -> list:
        """Convert HTML content from markdown to reportlab flowables"""
        start_time = time.time()
        
        try:
            # Try optimized DOM-based parsing first
            if HTML5LIB_AVAILABLE:
                flowables = self._markdown_to_flowables_optimized(html_content)
                parse_time = time.time() - start_time
                logging.info(f"HTML parsed using optimized DOM parser in {parse_time:.3f}s")
                return flowables
            else:
                # Fall back to manual parsing
                logging.info("Using manual HTML parsing (html5lib not available)")
                flowables = self._markdown_to_flowables_manual(html_content)
                parse_time = time.time() - start_time
                logging.info(f"HTML parsed using manual parser in {parse_time:.3f}s")
                return flowables
                
        except Exception as e:
            # If optimized parsing fails, fall back to manual parsing
            logging.warning(f"Optimized HTML parsing failed ({e}), falling back to manual parsing")
            try:
                flowables = self._markdown_to_flowables_manual(html_content)
                parse_time = time.time() - start_time
                logging.info(f"HTML parsed using fallback manual parser in {parse_time:.3f}s")
                return flowables
            except Exception as fallback_error:
                logging.error(f"Both HTML parsing methods failed: {fallback_error}")
                # Return a basic paragraph with error message
                return [Paragraph("Error processing markdown content", self.styles['Normal'])]
    
    def _markdown_to_flowables_optimized(self, html_content: str) -> list:
        """Convert HTML content to flowables using DOM-based parsing (optimized)"""
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
        
        # Parse HTML into DOM tree
        try:
            # Wrap content in proper HTML structure for parsing
            full_html = f"<html><body>{html_content}</body></html>"
            doc = html5lib.parse(full_html, treebuilder="etree")
            
            # Find body element or use root if no body
            body = doc.find('.//{http://www.w3.org/1999/xhtml}body')
            if body is None:
                body = doc
                
            # Process elements in order
            for element in body:
                flowable_list = self._process_element_optimized(element)
                flowables.extend(flowable_list)
                
        except Exception as e:
            logging.error(f"DOM parsing failed: {e}")
            raise
        
        # If no content was added, add a blank paragraph
        if not flowables:
            flowables.append(Paragraph("", self.styles['Normal']))
        
        logging.info(f"Generated {len(flowables)} flowables using optimized parser")
        return flowables
    
    # Bind methods to the class
    processor_class.markdown_to_flowables = markdown_to_flowables
    processor_class._markdown_to_flowables_optimized = _markdown_to_flowables_optimized
    # Add other helper methods...
    
    return processor_class

# The actual optimized implementation will be injected at runtime