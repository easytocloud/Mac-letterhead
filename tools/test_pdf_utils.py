#!/usr/bin/env python3

"""
Simple test module to verify the pdf_utils functionality
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from letterhead_pdf.pdf_utils import PDFMergeError

class TestPDFUtils(unittest.TestCase):
    """Test cases for pdf_utils module"""
    
    def test_pdf_merge_error(self):
        """Test PDFMergeError can be raised and caught"""
        with self.assertRaises(PDFMergeError):
            raise PDFMergeError("Test error")
    
    @patch('letterhead_pdf.pdf_utils.CoreGraphics')
    @patch('letterhead_pdf.pdf_utils.logging')
    def test_create_pdf_document(self, mock_logging, mock_cg):
        """Test create_pdf_document function with mocks"""
        # Need to import inside test to allow patching
        from letterhead_pdf.pdf_utils import create_pdf_document
        
        # Set up mocks
        mock_doc = MagicMock()
        mock_cg.CFURLCreateFromFileSystemRepresentation.return_value = "mock_url"
        mock_cg.CGPDFDocumentCreateWithURL.return_value = mock_doc
        
        # Call function
        result = create_pdf_document("/test/path.pdf")
        
        # Verify
        self.assertEqual(result, mock_doc)
        mock_logging.info.assert_called_once()
        mock_cg.CFURLCreateFromFileSystemRepresentation.assert_called_once()
        mock_cg.CGPDFDocumentCreateWithURL.assert_called_once()

if __name__ == "__main__":
    unittest.main()