#!/usr/bin/env python3

import sys
import os
import argparse
from typing import Optional, Dict, Any
from Quartz import PDFKit, CoreGraphics, kCGPDFContextUserPassword
from Foundation import NSURL, kCFAllocatorDefault
from AppKit import NSSavePanel, NSApp

__version__ = "0.1.0"

class PDFMergeError(Exception):
    """Custom exception for PDF merge errors"""
    pass

class LetterheadPDF:
    def __init__(self, letterhead_path: str, destination: str = "~/Desktop", suffix: str = " wm.pdf"):
        self.letterhead_path = os.path.expanduser(letterhead_path)
        self.destination = os.path.expanduser(destination)
        self.suffix = suffix

    def save_dialog(self, directory: str, filename: str) -> str:
        """Show save dialog and return selected path"""
        panel = NSSavePanel.savePanel()
        panel.setTitle_("Save PDF with Letterhead")
        my_url = NSURL.fileURLWithPath_isDirectory_(directory, True)
        panel.setDirectoryURL_(my_url)
        panel.setNameFieldStringValue_(filename)
        NSApp.activateIgnoringOtherApps_(True)
        ret_value = panel.runModal()
        return panel.filename() if ret_value else ''

    def create_pdf_document(self, path: str) -> Optional[CoreGraphics.CGPDFDocumentRef]:
        """Create PDF document from path"""
        path_bytes = path.encode('utf-8')
        url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
            kCFAllocatorDefault,
            path_bytes,
            len(path_bytes),
            False
        )
        if not url:
            raise PDFMergeError(f"Failed to create URL for path: {path}")
        return CoreGraphics.CGPDFDocumentCreateWithURL(url)

    def create_output_context(self, path: str, metadata: Dict[str, Any]) -> Optional[CoreGraphics.CGContextRef]:
        """Create PDF context for output"""
        path_bytes = path.encode('utf-8')
        url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
            kCFAllocatorDefault,
            path_bytes,
            len(path_bytes),
            False
        )
        if not url:
            raise PDFMergeError(f"Failed to create output URL for path: {path}")
        return CoreGraphics.CGPDFContextCreateWithURL(url, None, metadata)

    def get_doc_info(self, file_path: str) -> Dict[str, Any]:
        """Get PDF metadata"""
        pdf_url = NSURL.fileURLWithPath_(file_path)
        pdf_doc = PDFKit.PDFDocument.alloc().initWithURL_(pdf_url)
        if not pdf_doc:
            raise PDFMergeError(f"Failed to read PDF metadata from: {file_path}")
        
        metadata = pdf_doc.documentAttributes()
        if "Keywords" in metadata:
            keys = metadata["Keywords"]
            mutable_metadata = metadata.mutableCopy()
            mutable_metadata["Keywords"] = tuple(keys)
            return mutable_metadata
        return metadata

    def merge_pdfs(self, input_path: str, output_path: str) -> None:
        """Merge letterhead with input PDF"""
        try:
            metadata = self.get_doc_info(input_path)
            write_context = self.create_output_context(output_path, metadata)
            read_pdf = self.create_pdf_document(input_path)
            letterhead_pdf = self.create_pdf_document(self.letterhead_path)

            if not all([write_context, read_pdf, letterhead_pdf]):
                raise PDFMergeError("Failed to create PDF context or load PDFs")

            num_pages = CoreGraphics.CGPDFDocumentGetNumberOfPages(read_pdf)
            
            for page_num in range(1, num_pages + 1):
                page = CoreGraphics.CGPDFDocumentGetPage(read_pdf, page_num)
                letterhead_page = CoreGraphics.CGPDFDocumentGetPage(letterhead_pdf, 1)
                
                if not page or not letterhead_page:
                    raise PDFMergeError(f"Failed to get page {page_num}")
                
                media_box = CoreGraphics.CGPDFPageGetBoxRect(page, CoreGraphics.kCGPDFMediaBox)
                if CoreGraphics.CGRectIsEmpty(media_box):
                    media_box = None
                
                CoreGraphics.CGContextBeginPage(write_context, media_box)
                CoreGraphics.CGContextDrawPDFPage(write_context, page)
                CoreGraphics.CGContextSetBlendMode(write_context, CoreGraphics.kCGBlendModeNormal)
                CoreGraphics.CGContextDrawPDFPage(write_context, letterhead_page)
                CoreGraphics.CGContextEndPage(write_context)
            
            CoreGraphics.CGPDFContextClose(write_context)

        except Exception as e:
            raise PDFMergeError(f"Error merging PDFs: {str(e)}")

def create_service_script(letterhead_path: str) -> None:
    """Create a PDF Service script for the given letterhead"""
    pdf_services_dir = os.path.expanduser("~/Library/PDF Services")
    os.makedirs(pdf_services_dir, exist_ok=True)
    
    letterhead_name = os.path.splitext(os.path.basename(letterhead_path))[0]
    script_name = f"Letterhead {letterhead_name}"
    script_path = os.path.join(pdf_services_dir, script_name)
    
    script_content = f'''#!/bin/bash
# Letterhead PDF Service for {letterhead_name}
uv run mac-letterhead print "{os.path.abspath(letterhead_path)}" "$1" "$2" "$3"
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    print(f"Created PDF Service: {script_path}")

def print_command(args: argparse.Namespace) -> int:
    """Handle the print command"""
    try:
        letterhead = LetterheadPDF(letterhead_path=args.letterhead_path)
        
        # Use save dialog to get output location
        short_name = os.path.splitext(args.title)[0]
        output_path = letterhead.save_dialog(letterhead.destination, short_name + letterhead.suffix)
        
        if not output_path:
            print("No output location selected.")
            return 1
            
        if not os.path.exists(args.input_path):
            print(f"Input file not found: {args.input_path}")
            return 1
            
        letterhead.merge_pdfs(args.input_path, output_path)
        return 0
        
    except PDFMergeError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1

def install_command(args: argparse.Namespace) -> int:
    """Handle the install command"""
    try:
        if not os.path.exists(args.letterhead_path):
            print(f"Letterhead PDF not found: {args.letterhead_path}")
            return 1
            
        create_service_script(args.letterhead_path)
        return 0
        
    except Exception as e:
        print(f"Error installing service: {str(e)}")
        return 1

def main(args: Optional[list] = None) -> int:
    """Main entry point"""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Letterhead PDF Service Manager")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install a new letterhead service')
    install_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    
    # Print command
    print_parser = subparsers.add_parser('print', help='Merge letterhead with document')
    print_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    print_parser.add_argument('title', help='Output file title')
    print_parser.add_argument('options', help='Print options')
    print_parser.add_argument('input_path', help='Input PDF file path')
    
    args = parser.parse_args(args)
    
    if args.command == 'install':
        return install_command(args)
    elif args.command == 'print':
        return print_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
