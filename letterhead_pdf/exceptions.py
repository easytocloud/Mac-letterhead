#!/usr/bin/env python3

"""
Custom exceptions for the letterhead_pdf package
"""

class LetterheadError(Exception):
    """Base exception for all letterhead-related errors"""
    pass


class PDFMergeError(LetterheadError):
    """Exception raised for errors during PDF merging"""
    pass


class PDFCreationError(LetterheadError):
    """Exception raised for errors during PDF document creation"""
    pass


class PDFMetadataError(LetterheadError):
    """Exception raised for errors during PDF metadata access"""
    pass


class UIError(LetterheadError):
    """Exception raised for errors in the user interface"""
    pass


class FilePathError(LetterheadError):
    """Exception raised for errors with file paths"""
    pass


class InstallerError(LetterheadError):
    """Exception raised for errors during app installation"""
    pass