#!/usr/bin/env python3

class PDFMergeError(Exception):
    """Custom exception for PDF merge errors"""
    pass

class PDFCreationError(Exception):
    """Custom exception for PDF creation errors"""
    pass

class PDFMetadataError(Exception):
    """Custom exception for PDF metadata errors"""
    pass

class InstallerError(Exception):
    """Custom exception for installer errors"""
    pass
