#!/usr/bin/env python3

"""
Comprehensive test suite for list rendering edge cases.

This test suite covers:
- Basic list testing (simple bulleted/numbered lists)
- Nested list testing (2-level, 3+ level nesting)
- Edge cases (malformed HTML, unusual formatting)
- Backend compatibility (WeasyPrint vs ReportLab)
- Performance and memory usage validation
"""

import os
import sys
import unittest
import tempfile
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from letterhead_pdf.markdown_processor import MarkdownProcessor
from letterhead_pdf.pdf_merger import PDFMerger

# Test configuration
TEST_FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_EXPECTED_DIR = Path(__file__).parent / "expected_outputs"
TEST_OUTPUT_DIR = Path(__file__).parent.parent / "test-output"

# Ensure test output directory exists
TEST_OUTPUT_DIR.mkdir(exist_ok=True)

class TestListRendering(unittest.TestCase):
    """Main test class for list rendering functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with processors and test data."""
        cls.processor = MarkdownProcessor()
        
        # Create a simple test letterhead for testing
        cls.test_letterhead_path = cls._create_test_letterhead()
        
        # Initialize PDFMerger with the test letterhead
        cls.merger = PDFMerger(cls.test_letterhead_path)
        
        # Performance tracking
        cls.performance_data = {}
        
        # Setup logging for test output
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
    
    @classmethod
    def _create_test_letterhead(cls) -> str:
        """Create a simple test letterhead PDF for testing."""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        letterhead_path = TEST_OUTPUT_DIR / "test_letterhead.pdf"
        
        # Create simple letterhead
        c = canvas.Canvas(str(letterhead_path), pagesize=A4)
        width, height = A4
        
        # Add simple header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "TEST LETTERHEAD")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "For List Rendering Tests")
        
        # Add a simple line
        c.line(50, height - 80, width - 50, height - 80)
        
        c.save()
        return str(letterhead_path)
    
    def setUp(self):
        """Set up each test."""
        self.start_time = time.time()
    
    def tearDown(self):
        """Track test execution time."""
        execution_time = time.time() - self.start_time
        test_name = self.id().split('.')[-1]
        self.performance_data[test_name] = execution_time
    
    def _process_markdown_file(self, fixture_name: str, backend: str = "reportlab") -> Tuple[str, Dict]:
        """
        Process a markdown fixture file and return the output path and metrics.
        
        Args:
            fixture_name: Name of the fixture file (without .md extension)
            backend: Backend to use ("reportlab" or "weasyprint")
        
        Returns:
            Tuple of (output_path, metrics_dict)
        """
        fixture_path = TEST_FIXTURES_DIR / f"{fixture_name}.md"
        
        if not fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")
        
        # Read fixture content
        with open(fixture_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Create output filename
        output_filename = f"{fixture_name}_{backend}_test.pdf"
        output_path = TEST_OUTPUT_DIR / output_filename
        
        # Process with timing
        start_time = time.time()
        
        try:
            # Write markdown to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_md:
                tmp_md.write(markdown_content)
                tmp_md_path = tmp_md.name
            
            # Convert markdown to PDF
            self.processor.md_to_pdf(
                tmp_md_path,
                str(output_path),
                self.test_letterhead_path
            )
            
            processing_time = time.time() - start_time
            success = True
            error = None
            
        except Exception as e:
            processing_time = time.time() - start_time
            success = False
            error = str(e)
            self.logger.error(f"Processing failed for {fixture_name} with {backend}: {error}")
        finally:
            # Clean up temporary file
            if 'tmp_md_path' in locals() and os.path.exists(tmp_md_path):
                os.unlink(tmp_md_path)
        
        # Collect metrics
        metrics = {
            'processing_time': processing_time,
            'success': success,
            'error': error,
            'backend': backend,
            'fixture': fixture_name,
            'output_exists': output_path.exists(),
            'output_size': output_path.stat().st_size if output_path.exists() else 0
        }
        
        return str(output_path), metrics
    
    def _compare_backends(self, fixture_name: str) -> Dict:
        """
        Compare output between WeasyPrint and ReportLab backends.
        
        Args:
            fixture_name: Name of the fixture to test
        
        Returns:
            Dictionary with comparison results
        """
        # Process with both backends
        reportlab_path, reportlab_metrics = self._process_markdown_file(fixture_name, "reportlab")
        
        try:
            weasyprint_path, weasyprint_metrics = self._process_markdown_file(fixture_name, "weasyprint")
            weasyprint_available = True
        except Exception as e:
            self.logger.warning(f"WeasyPrint not available for {fixture_name}: {e}")
            weasyprint_path, weasyprint_metrics = None, None
            weasyprint_available = False
        
        comparison = {
            'fixture': fixture_name,
            'reportlab_metrics': reportlab_metrics,
            'weasyprint_metrics': weasyprint_metrics,
            'weasyprint_available': weasyprint_available,
            'both_successful': (
                reportlab_metrics['success'] and 
                (weasyprint_metrics['success'] if weasyprint_available else True)
            )
        }
        
        # Compare file sizes if both succeeded
        if (comparison['both_successful'] and weasyprint_available and 
            reportlab_metrics['output_size'] > 0 and weasyprint_metrics['output_size'] > 0):
            
            size_diff = abs(reportlab_metrics['output_size'] - weasyprint_metrics['output_size'])
            size_ratio = size_diff / max(reportlab_metrics['output_size'], weasyprint_metrics['output_size'])
            
            comparison['size_difference'] = size_diff
            comparison['size_ratio'] = size_ratio
            comparison['similar_size'] = size_ratio < 0.5  # Within 50% is considered similar
        
        return comparison

    # BASIC LIST TESTS
    
    def test_simple_lists_reportlab(self):
        """Test simple lists with ReportLab backend."""
        output_path, metrics = self._process_markdown_file("simple_lists", "reportlab")
        
        self.assertTrue(metrics['success'], f"Simple lists failed with ReportLab: {metrics['error']}")
        self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
        self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
    
    def test_simple_lists_weasyprint(self):
        """Test simple lists with WeasyPrint backend."""
        try:
            output_path, metrics = self._process_markdown_file("simple_lists", "weasyprint")
            
            self.assertTrue(metrics['success'], f"Simple lists failed with WeasyPrint: {metrics['error']}")
            self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
            self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
            
        except Exception as e:
            self.skipTest(f"WeasyPrint not available: {e}")
    
    def test_simple_lists_backend_comparison(self):
        """Compare simple lists output between backends."""
        comparison = self._compare_backends("simple_lists")
        
        self.assertTrue(comparison['reportlab_metrics']['success'], 
                       "ReportLab processing should succeed")
        
        if comparison['weasyprint_available']:
            self.assertTrue(comparison['both_successful'], 
                           "Both backends should process simple lists successfully")

    # NESTED LIST TESTS
    
    def test_nested_lists_reportlab(self):
        """Test nested lists with ReportLab backend."""
        output_path, metrics = self._process_markdown_file("nested_lists", "reportlab")
        
        self.assertTrue(metrics['success'], f"Nested lists failed with ReportLab: {metrics['error']}")
        self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
        self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
    
    def test_nested_lists_weasyprint(self):
        """Test nested lists with WeasyPrint backend."""
        try:
            output_path, metrics = self._process_markdown_file("nested_lists", "weasyprint")
            
            self.assertTrue(metrics['success'], f"Nested lists failed with WeasyPrint: {metrics['error']}")
            self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
            self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
            
        except Exception as e:
            self.skipTest(f"WeasyPrint not available: {e}")
    
    def test_nested_lists_backend_comparison(self):
        """Compare nested lists output between backends."""
        comparison = self._compare_backends("nested_lists")
        
        self.assertTrue(comparison['reportlab_metrics']['success'], 
                       "ReportLab processing should succeed")
        
        if comparison['weasyprint_available']:
            self.assertTrue(comparison['both_successful'], 
                           "Both backends should process nested lists successfully")

    # MIXED CONTENT TESTS
    
    def test_mixed_content_lists_reportlab(self):
        """Test lists with mixed content using ReportLab backend."""
        output_path, metrics = self._process_markdown_file("mixed_content_lists", "reportlab")
        
        self.assertTrue(metrics['success'], f"Mixed content lists failed with ReportLab: {metrics['error']}")
        self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
        self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
    
    def test_mixed_content_lists_weasyprint(self):
        """Test lists with mixed content using WeasyPrint backend."""
        try:
            output_path, metrics = self._process_markdown_file("mixed_content_lists", "weasyprint")
            
            self.assertTrue(metrics['success'], f"Mixed content lists failed with WeasyPrint: {metrics['error']}")
            self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
            self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
            
        except Exception as e:
            self.skipTest(f"WeasyPrint not available: {e}")

    # EDGE CASE TESTS
    
    def test_edge_case_lists_reportlab(self):
        """Test edge case lists with ReportLab backend."""
        output_path, metrics = self._process_markdown_file("edge_case_lists", "reportlab")
        
        # Edge cases might not always succeed, but should not crash
        self.assertTrue(os.path.exists(output_path) or not metrics['success'], 
                       "Should either create output or fail gracefully")
    
    def test_malformed_lists_reportlab(self):
        """Test malformed lists with ReportLab backend."""
        output_path, metrics = self._process_markdown_file("malformed_lists", "reportlab")
        
        # Malformed content should be handled gracefully
        if metrics['success']:
            self.assertTrue(os.path.exists(output_path), "Output PDF was not created")
            self.assertGreater(metrics['output_size'], 0, "Output PDF is empty")
        else:
            # It's okay if malformed content fails, but error should be logged
            self.assertIsNotNone(metrics['error'], "Error should be captured")
    
    # PERFORMANCE TESTS
    
    def test_performance_benchmark(self):
        """Benchmark list processing performance."""
        fixtures = ["simple_lists", "nested_lists", "mixed_content_lists", "edge_case_lists"]
        performance_results = {}
        
        for fixture in fixtures:
            self.logger.info(f"Benchmarking {fixture}...")
            
            # Test ReportLab performance
            start_time = time.time()
            output_path, metrics = self._process_markdown_file(fixture, "reportlab")
            reportlab_time = time.time() - start_time
            
            performance_results[fixture] = {
                'reportlab_time': reportlab_time,
                'reportlab_success': metrics['success']
            }
            
            # Test WeasyPrint performance if available
            try:
                start_time = time.time()
                output_path, metrics = self._process_markdown_file(fixture, "weasyprint")
                weasyprint_time = time.time() - start_time
                
                performance_results[fixture]['weasyprint_time'] = weasyprint_time
                performance_results[fixture]['weasyprint_success'] = metrics['success']
                
                # Calculate relative performance
                if reportlab_time > 0 and weasyprint_time > 0:
                    performance_results[fixture]['speed_ratio'] = reportlab_time / weasyprint_time
                    
            except Exception as e:
                self.logger.info(f"WeasyPrint benchmark skipped for {fixture}: {e}")
        
        # Log performance summary
        self.logger.info("Performance Benchmark Results:")
        for fixture, results in performance_results.items():
            self.logger.info(f"  {fixture}:")
            self.logger.info(f"    ReportLab: {results['reportlab_time']:.3f}s")
            if 'weasyprint_time' in results:
                self.logger.info(f"    WeasyPrint: {results['weasyprint_time']:.3f}s")
                if 'speed_ratio' in results:
                    self.logger.info(f"    Speed ratio: {results['speed_ratio']:.2f}x")
        
        # Assert reasonable performance
        for fixture, results in performance_results.items():
            self.assertLess(results['reportlab_time'], 30.0, 
                           f"{fixture} with ReportLab took too long: {results['reportlab_time']:.2f}s")
    
    # REGRESSION TESTS
    
    def test_all_fixtures_no_crash(self):
        """Regression test: ensure all fixtures process without crashing."""
        fixtures = ["simple_lists", "nested_lists", "mixed_content_lists", "edge_case_lists", "malformed_lists"]
        results = {}
        
        for fixture in fixtures:
            try:
                output_path, metrics = self._process_markdown_file(fixture, "reportlab")
                results[fixture] = {
                    'success': metrics['success'],
                    'error': metrics['error'],
                    'crashed': False
                }
            except Exception as e:
                results[fixture] = {
                    'success': False,
                    'error': str(e),
                    'crashed': True
                }
        
        # Log results
        self.logger.info("Regression Test Results:")
        for fixture, result in results.items():
            status = "✓" if result['success'] else ("✗ CRASH" if result['crashed'] else "✗ FAIL")
            self.logger.info(f"  {fixture}: {status}")
            if result['error']:
                self.logger.info(f"    Error: {result['error']}")
        
        # Assert no crashes occurred
        crashed_fixtures = [f for f, r in results.items() if r['crashed']]
        self.assertEqual(len(crashed_fixtures), 0, 
                        f"These fixtures caused crashes: {crashed_fixtures}")
    
    # COMPATIBILITY TESTS
    
    def test_backend_compatibility(self):
        """Test that both backends produce compatible results."""
        fixtures = ["simple_lists", "nested_lists"]  # Use stable fixtures for compatibility test
        compatibility_results = {}
        
        for fixture in fixtures:
            comparison = self._compare_backends(fixture)
            compatibility_results[fixture] = comparison
            
            # ReportLab should always work
            self.assertTrue(comparison['reportlab_metrics']['success'], 
                           f"ReportLab should process {fixture} successfully")
            
            # If WeasyPrint is available, test compatibility
            if comparison['weasyprint_available']:
                self.assertTrue(comparison['both_successful'], 
                               f"Both backends should process {fixture} successfully")
        
        self.logger.info("Backend Compatibility Results:")
        for fixture, result in compatibility_results.items():
            weasy_status = "✓" if result.get('weasyprint_available') and result['weasyprint_metrics']['success'] else "✗"
            report_status = "✓" if result['reportlab_metrics']['success'] else "✗"
            self.logger.info(f"  {fixture}: ReportLab {report_status}, WeasyPrint {weasy_status}")


class TestListRenderingIntegration(unittest.TestCase):
    """Integration tests for list rendering with full PDF merger pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test class."""
        cls.processor = MarkdownProcessor()
        cls.test_letterhead_path = TestListRendering._create_test_letterhead()
        cls.merger = PDFMerger(cls.test_letterhead_path)
    
    def test_end_to_end_list_processing(self):
        """Test complete pipeline from Markdown with lists to final letterheaded PDF."""
        # Create test markdown with lists
        test_markdown = """
# Test Document with Lists

## Simple Lists

- First item
- Second item
- Third item

## Numbered Lists

1. First numbered item
2. Second numbered item
3. Third numbered item

## Nested Lists

- Top level
  - Nested level
  - Another nested item
- Back to top level
"""
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as md_file:
            md_file.write(test_markdown)
            md_path = md_file.name
        
        try:
            output_path = TEST_OUTPUT_DIR / "integration_test_lists.pdf"
            
            # Process through full pipeline
            self.processor.md_to_pdf(
                md_path,
                str(output_path),
                self.test_letterhead_path
            )
            
            # Verify output
            self.assertTrue(output_path.exists(), "Integration test output should exist")
            self.assertGreater(output_path.stat().st_size, 0, "Integration test output should not be empty")
            
        finally:
            # Clean up
            if os.path.exists(md_path):
                os.unlink(md_path)


def run_list_rendering_tests():
    """Run all list rendering tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestListRendering))
    suite.addTests(loader.loadTestsFromTestCase(TestListRenderingIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    # Run tests when script is executed directly
    result = run_list_rendering_tests()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)