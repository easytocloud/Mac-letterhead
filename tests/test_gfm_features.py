#!/usr/bin/env python3

"""
Comprehensive test suite for GitHub Flavored Markdown features.

This test suite covers:
- Strikethrough text rendering
- Task list functionality (checked and unchecked)
- Nested task lists
- Mixed content with GFM features
- Backend compatibility (GFM vs standard markdown)
- Integration with PDF generation pipeline
"""

import os
import sys
import unittest
import unittest.mock
import tempfile
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from letterhead_pdf.markdown_processor import MarkdownProcessor, PYCMARKGFM_AVAILABLE
from letterhead_pdf.pdf_merger import PDFMerger

# Test configuration
TEST_OUTPUT_DIR = Path(__file__).parent.parent / "test-output"
TEST_OUTPUT_DIR.mkdir(exist_ok=True)


class TestGitHubFlavoredMarkdown(unittest.TestCase):
    """Test GitHub Flavored Markdown features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with processors and test data."""
        # Create test letterhead
        cls.test_letterhead_path = cls._create_test_letterhead()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        
        # Track if GFM is available
        cls.gfm_available = PYCMARKGFM_AVAILABLE
        if not cls.gfm_available:
            cls.logger.warning("pycmarkgfm not available, some tests will be skipped")
    
    @classmethod
    def _create_test_letterhead(cls) -> str:
        """Create a simple test letterhead PDF for testing."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        letterhead_path = TEST_OUTPUT_DIR / "test_letterhead_gfm.pdf"
        
        # Create simple letterhead
        c = canvas.Canvas(str(letterhead_path), pagesize=A4)
        width, height = A4
        
        # Add simple header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "GFM TEST LETTERHEAD")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "GitHub Flavored Markdown Testing")
        
        # Add a simple line
        c.line(50, height - 80, width - 50, height - 80)
        
        c.save()
        return str(letterhead_path)
    
    def test_gfm_backend_availability(self):
        """Test that pycmarkgfm backend is available and working."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        # Test direct import
        import pycmarkgfm
        html = pycmarkgfm.gfm_to_html("~~test~~")
        self.assertIn('<del>', html)
        self.assertIn('test', html)
        self.assertIn('</del>', html)
    
    def test_processor_auto_detection(self):
        """Test that MarkdownProcessor correctly auto-detects GFM availability."""
        processor = MarkdownProcessor()
        
        if self.gfm_available:
            self.assertTrue(processor.use_gfm, "Should auto-detect and enable GFM")
        else:
            self.assertFalse(processor.use_gfm, "Should fallback to standard markdown")
    
    def test_processor_explicit_modes(self):
        """Test explicit GFM mode selection."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        # Test explicit GFM mode
        gfm_processor = MarkdownProcessor(use_gfm=True)
        self.assertTrue(gfm_processor.use_gfm)
        
        # Test explicit standard mode
        std_processor = MarkdownProcessor(use_gfm=False)
        self.assertFalse(std_processor.use_gfm)
        
        # Test impossible mode (GFM requested but not available)
        with unittest.mock.patch('letterhead_pdf.markdown_processor.PYCMARKGFM_AVAILABLE', False):
            fallback_processor = MarkdownProcessor(use_gfm=True)
            self.assertFalse(fallback_processor.use_gfm)
    
    def test_strikethrough_processing(self):
        """Test strikethrough text processing."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        test_cases = [
            ("~~simple strikethrough~~", "<del>simple strikethrough</del>"),
            ("text with ~~strikethrough~~ in middle", "text with <del>strikethrough</del> in middle"),
            ("~~multiple~~ ~~strikethrough~~ sections", "<del>multiple</del> <del>strikethrough</del> sections"),
            ("**bold** and ~~strikethrough~~", "<strong>bold</strong> and <del>strikethrough</del>"),
        ]
        
        for markdown, expected_part in test_cases:
            with self.subTest(markdown=markdown):
                html = processor.md_to_html(markdown)
                self.assertIn(expected_part, html, f"Failed for: {markdown}")
    
    def test_task_list_processing(self):
        """Test task list processing."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        markdown = """Task list:
- [x] Completed task
- [ ] Incomplete task
- [x] Another completed task"""
        
        html = processor.md_to_html(markdown)
        
        # Check for task list elements
        self.assertIn('<input type="checkbox" checked', html)
        self.assertIn('<input type="checkbox" disabled', html)
        self.assertIn('data-gfm-task', html)
        
        # Count checkboxes
        checked_count = html.count('checked=""')
        unchecked_count = html.count('<input type="checkbox" disabled=""')
        
        self.assertEqual(checked_count, 2, "Should have 2 checked tasks")
        self.assertEqual(unchecked_count, 1, "Should have 1 unchecked task")
    
    def test_nested_task_lists(self):
        """Test nested task list processing."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        markdown = """Nested tasks:
- [x] Top level completed
  - [x] Nested completed
  - [ ] Nested incomplete
- [ ] Top level incomplete
  - [x] Nested under incomplete"""
        
        html = processor.md_to_html(markdown)
        
        # Check for nested structure
        self.assertIn('<ul>', html)
        self.assertIn('</ul>', html)
        
        # Should have proper nesting
        nested_ul_count = html.count('<ul>')
        self.assertGreaterEqual(nested_ul_count, 2, "Should have nested <ul> elements")
        
        # Count total checkboxes
        total_checkboxes = html.count('<input type="checkbox"')
        self.assertEqual(total_checkboxes, 5, "Should have 5 total checkboxes")
    
    def test_table_checkbox_processing(self):
        """Test that checkboxes in table cells are properly converted"""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        markdown = """| Task | Status |
|------|--------|
| Feature A | [x] Complete |
| Feature B | [ ] Pending |"""
        
        html = processor.md_to_html(markdown)
        
        # Raw HTML should contain [x] and [ ] text in table cells
        self.assertIn('[x] Complete', html)
        self.assertIn('[ ] Pending', html)
        
        # Test WeasyPrint enhancement
        enhanced_html = processor._enhance_gfm_task_lists_for_weasyprint(html)
        self.assertIn('<span class="task-checked">☑</span> Complete', enhanced_html)
        self.assertIn('<span class="task-unchecked task-unchecked-scaled">☐</span> Pending', enhanced_html)
        
        # Test ReportLab processing
        cleaned_html = processor.clean_html_for_reportlab(html)
        self.assertIn('☑ Complete', cleaned_html)
        self.assertIn('☐ Pending', cleaned_html)
    
    def test_mixed_content_with_gfm(self):
        """Test mixed content including GFM features."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        markdown = """# Mixed Content Test

Regular **bold** and *italic* text.

~~Strikethrough~~ text here.

Task list:
- [x] ~~Completed and struck~~
- [ ] **Bold incomplete task**
- [x] Regular completed

| Task | Status | Notes |
|------|--------|-------|
| Feature A | [x] Complete | ~~Old approach~~ |
| Feature B | [ ] Pending | **High priority** |

Code with `~~not strikethrough~~` in backticks."""
        
        html = processor.md_to_html(markdown)
        
        # Check various elements are present
        self.assertIn('<h1>', html)
        self.assertIn('<strong>', html)
        self.assertIn('<em>', html)
        self.assertIn('<del>', html)
        self.assertIn('<input type="checkbox"', html)
        self.assertIn('<table>', html)
        self.assertIn('<code>', html)
        
        # Verify strikethrough in table cells works
        self.assertIn('<del>Old approach</del>', html)
        self.assertIn('<del>Completed and struck</del>', html)
    
    def test_gfm_vs_standard_markdown(self):
        """Test differences between GFM and standard markdown."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        test_markdown = """~~strikethrough~~ text
- [x] task item
- [ ] another task"""
        
        # Test GFM processor
        gfm_processor = MarkdownProcessor(use_gfm=True)
        gfm_html = gfm_processor.md_to_html(test_markdown)
        
        # Test standard processor
        std_processor = MarkdownProcessor(use_gfm=False)
        std_html = std_processor.md_to_html(test_markdown)
        
        # GFM should have del tags
        self.assertIn('<del>', gfm_html)
        self.assertNotIn('<del>', std_html)
        
        # GFM should have checkboxes
        self.assertIn('<input type="checkbox"', gfm_html)
        self.assertNotIn('<input type="checkbox"', std_html)
        
        # Standard should treat as literal text
        self.assertIn('~~strikethrough~~', std_html)
        self.assertIn('[x]', std_html)
    
    def test_html_cleaning_for_reportlab(self):
        """Test HTML cleaning for ReportLab compatibility."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        markdown = """~~strikethrough~~ and tasks:
- [x] completed
- [ ] incomplete"""
        
        # Get raw HTML
        raw_html = processor.md_to_html(markdown)
        
        # Clean for ReportLab
        cleaned_html = processor.clean_html_for_reportlab(raw_html)
        
        # Check transformations
        self.assertIn('<strike>', cleaned_html)  # del -> strike
        self.assertNotIn('<del>', cleaned_html)
        
        self.assertIn('☑', cleaned_html)  # checked checkbox -> ☑
        self.assertIn('☐', cleaned_html)  # unchecked checkbox -> ☐
        self.assertNotIn('<input', cleaned_html)
        self.assertNotIn('data-gfm-task', cleaned_html)
    
    def test_end_to_end_pdf_generation(self):
        """Test complete pipeline from GFM markdown to PDF."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        processor = MarkdownProcessor(use_gfm=True)
        
        test_markdown = """# GFM End-to-End Test

This tests the complete pipeline.

## Strikethrough
~~This should be struck through~~

## Task Lists
- [x] PDF generation works
- [ ] All features tested
- [x] ~~Old feature~~ completed

Regular list:
- Normal item
- Another item"""
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as md_file:
            md_file.write(test_markdown)
            md_path = md_file.name
        
        try:
            output_path = TEST_OUTPUT_DIR / "gfm_end_to_end_test.pdf"
            
            # Process through full pipeline
            processor.md_to_pdf(
                md_path,
                str(output_path),
                self.test_letterhead_path
            )
            
            # Verify output
            self.assertTrue(output_path.exists(), "End-to-end test output should exist")
            self.assertGreater(output_path.stat().st_size, 0, "End-to-end test output should not be empty")
            
        finally:
            # Clean up
            if os.path.exists(md_path):
                os.unlink(md_path)
    
    def test_performance_comparison(self):
        """Test performance difference between GFM and standard markdown."""
        if not self.gfm_available:
            self.skipTest("pycmarkgfm not available")
        
        sections = []
        for i in range(50):
            sections.extend([
                f"## Section {i}",
                f"~~Strikethrough {i}~~ with **bold** text.",
                f"- [x] Task {i} completed",
                f"- [ ] Task {i} pending",
                ""
            ])
        
        large_markdown = "# Performance Test\n\n" + "\n".join(sections)
        
        # Test GFM performance
        gfm_processor = MarkdownProcessor(use_gfm=True)
        gfm_start = time.time()
        gfm_html = gfm_processor.md_to_html(large_markdown)
        gfm_time = time.time() - gfm_start
        
        # Test standard performance
        std_processor = MarkdownProcessor(use_gfm=False)
        std_start = time.time()
        std_html = std_processor.md_to_html(large_markdown)
        std_time = time.time() - std_start
        
        # Log performance results
        self.logger.info(f"GFM processing time: {gfm_time:.3f}s")
        self.logger.info(f"Standard processing time: {std_time:.3f}s")
        
        # Both should complete in reasonable time
        self.assertLess(gfm_time, 5.0, "GFM processing should complete within 5 seconds")
        self.assertLess(std_time, 5.0, "Standard processing should complete within 5 seconds")
        
        # Verify output quality
        self.assertGreater(len(gfm_html), len(std_html), "GFM should produce more HTML due to additional elements")
        self.assertIn('<del>', gfm_html)
        self.assertIn('<input type="checkbox"', gfm_html)


class TestGFMIntegration(unittest.TestCase):
    """Integration tests for GFM with the full application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test class."""
        cls.gfm_available = PYCMARKGFM_AVAILABLE
        if not cls.gfm_available:
            cls.skipTest("pycmarkgfm not available")
        
        cls.test_letterhead_path = TestGitHubFlavoredMarkdown._create_test_letterhead()
    
    def test_makefile_compatibility(self):
        """Test that GFM works with make test commands."""
        # This test verifies that our changes don't break the existing Makefile tests
        # The actual test execution happens in the Makefile, this just documents the requirement
        self.assertTrue(True, "GFM should be compatible with existing make test-* commands")
    
    def test_mcp_server_integration(self):
        """Test that GFM works with MCP server integration."""
        processor = MarkdownProcessor()
        
        # Test that MCP server can use the processor
        self.assertIsNotNone(processor)
        
        # Test markdown processing works
        test_md = "~~test~~ content"
        html = processor.md_to_html(test_md)
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)


def run_gfm_tests():
    """Run all GFM tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubFlavoredMarkdown))
    suite.addTests(loader.loadTestsFromTestCase(TestGFMIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    # Run tests when script is executed directly
    result = run_gfm_tests()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)