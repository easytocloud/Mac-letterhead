#!/usr/bin/env python3
"""
Custom exceptions for Mac-letterhead application.

This module defines all custom exceptions used throughout the application
to provide clear error categorization and handling.
"""


class LetterheadError(Exception):
    """Base exception class for all Mac-letterhead related errors"""
    pass


class PDFMergeError(LetterheadError):
    """Exception raised when PDF merging operations fail"""
    pass


class PDFCreationError(LetterheadError):
    """Exception raised when PDF creation operations fail"""
    pass


class PDFMetadataError(LetterheadError):
    """Exception raised when PDF metadata operations fail"""
    pass


class InstallerError(LetterheadError):
    """Exception raised when droplet installation operations fail"""
    pass


class MarkdownProcessingError(LetterheadError):
    """Exception raised when Markdown processing operations fail"""
    pass
