#!/usr/bin/env python3

import os
import logging
from typing import Optional, Dict, Any
from Quartz import PDFKit, CoreGraphics, kCGPDFContextUserPassword
from Foundation import NSURL

# Define PDFMergeError here to avoid circular imports
class PDFMergeError(Exception):
    """Custom exception for PDF merge errors"""
    pass

def create_pdf_document(path: str) -> Optional[CoreGraphics.CGPDFDocumentRef]:
    """Create PDF document from path"""
    logging.info(f"Creating PDF document from: {path}")
    path_bytes = path.encode('utf-8')
    url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
        CoreGraphics.kCFAllocatorDefault,
        path_bytes,
        len(path_bytes),
        False
    )
    if not url:
        error_msg = f"Failed to create URL for path: {path}"
        logging.error(error_msg)
        raise PDFMergeError(error_msg)
    doc = CoreGraphics.CGPDFDocumentCreateWithURL(url)
    if not doc:
        error_msg = f"Failed to create PDF document from: {path}"
        logging.error(error_msg)
        raise PDFMergeError(error_msg)
    return doc

def create_output_context(path: str, metadata: Dict[str, Any]) -> Optional[CoreGraphics.CGContextRef]:
    """Create PDF context for output"""
    logging.info(f"Creating output context for: {path}")
    path_bytes = path.encode('utf-8')
    url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
        CoreGraphics.kCFAllocatorDefault,
        path_bytes,
        len(path_bytes),
        False
    )
    if not url:
        error_msg = f"Failed to create output URL for path: {path}"
        logging.error(error_msg)
        raise PDFMergeError(error_msg)
    context = CoreGraphics.CGPDFContextCreateWithURL(url, None, metadata)
    if not context:
        error_msg = f"Failed to create PDF context for: {path}"
        logging.error(error_msg)
        raise PDFMergeError(error_msg)
    return context

def get_doc_info(file_path: str) -> Dict[str, Any]:
    """Get PDF metadata"""
    logging.info(f"Getting document info from: {file_path}")
    pdf_url = NSURL.fileURLWithPath_(file_path)
    pdf_doc = PDFKit.PDFDocument.alloc().initWithURL_(pdf_url)
    if not pdf_doc:
        error_msg = f"Failed to read PDF metadata from: {file_path}"
        logging.error(error_msg)
        raise PDFMergeError(error_msg)
    
    metadata = pdf_doc.documentAttributes()
    if "Keywords" in metadata:
        keys = metadata["Keywords"]
        mutable_metadata = metadata.mutableCopy()
        mutable_metadata["Keywords"] = tuple(keys)
        return mutable_metadata
    return metadata