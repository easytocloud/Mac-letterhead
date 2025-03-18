#!/usr/bin/env python3

import sys
import os
import argparse
import logging
from typing import Optional, Dict, Any
from Quartz import PDFKit, CoreGraphics, kCGPDFContextUserPassword
from Foundation import NSURL, kCFAllocatorDefault, NSObject, NSApplication
from AppKit import NSSavePanel, NSApp, NSFloatingWindowLevel

from letterhead_pdf import __version__

# Set up logging
LOG_DIR = os.path.expanduser("~/Library/Logs/Mac-letterhead")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "letterhead.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class PDFMergeError(Exception):
    """Custom exception for PDF merge errors"""
    pass

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        pass

class LetterheadPDF:
    def __init__(self, letterhead_path: str, destination: str = "~/Desktop", suffix: str = " wm.pdf"):
        self.letterhead_path = os.path.expanduser(letterhead_path)
        self.destination = os.path.expanduser(destination)
        self.suffix = suffix
        logging.info(f"Initializing LetterheadPDF with template: {self.letterhead_path}")

    def save_dialog(self, directory: str, filename: str) -> str:
        """Show save dialog and return selected path"""
        logging.info(f"Opening save dialog with initial directory: {directory}")
        
        # Initialize application if needed
        if NSApp() is None:
            app = NSApplication.sharedApplication()
            delegate = AppDelegate.alloc().init()
            app.setDelegate_(delegate)
            app.finishLaunching()
        
        panel = NSSavePanel.savePanel()
        panel.setTitle_("Save PDF with Letterhead")
        panel.setLevel_(NSFloatingWindowLevel)  # Make dialog float above other windows
        my_url = NSURL.fileURLWithPath_isDirectory_(directory, True)
        panel.setDirectoryURL_(my_url)
        panel.setNameFieldStringValue_(filename)
        NSApp.activateIgnoringOtherApps_(True)
        
        ret_value = panel.runModal()
        logging.info(f"Save dialog return value: {ret_value}")
        
        if ret_value:
            selected_path = panel.filename()
            if not selected_path:
                # If no path but OK was clicked, use default location
                selected_path = os.path.join(directory, filename)
            logging.info(f"Save dialog result: {selected_path}")
            return selected_path
        else:
            logging.info("Save dialog cancelled")
            return ''

    def create_pdf_document(self, path: str) -> Optional[CoreGraphics.CGPDFDocumentRef]:
        """Create PDF document from path"""
        logging.info(f"Creating PDF document from: {path}")
        path_bytes = path.encode('utf-8')
        url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
            kCFAllocatorDefault,
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

    def create_output_context(self, path: str, metadata: Dict[str, Any]) -> Optional[CoreGraphics.CGContextRef]:
        """Create PDF context for output"""
        logging.info(f"Creating output context for: {path}")
        path_bytes = path.encode('utf-8')
        url = CoreGraphics.CFURLCreateFromFileSystemRepresentation(
            kCFAllocatorDefault,
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

    def get_doc_info(self, file_path: str) -> Dict[str, Any]:
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

    def merge_pdfs(self, input_path: str, output_path: str) -> None:
        """Merge letterhead with input PDF"""
        try:
            logging.info(f"Starting PDF merge: {input_path} -> {output_path}")
            logging.info(f"Using letterhead: {self.letterhead_path}")
            
            metadata = self.get_doc_info(input_path)
            write_context = self.create_output_context(output_path, metadata)
            read_pdf = self.create_pdf_document(input_path)
            letterhead_pdf = self.create_pdf_document(self.letterhead_path)

            if not all([write_context, read_pdf, letterhead_pdf]):
                error_msg = "Failed to create PDF context or load PDFs"
                logging.error(error_msg)
                raise PDFMergeError(error_msg)

            num_pages = CoreGraphics.CGPDFDocumentGetNumberOfPages(read_pdf)
            logging.info(f"Processing {num_pages} pages")
            
            for page_num in range(1, num_pages + 1):
                logging.info(f"Processing page {page_num}")
                page = CoreGraphics.CGPDFDocumentGetPage(read_pdf, page_num)
                letterhead_page = CoreGraphics.CGPDFDocumentGetPage(letterhead_pdf, 1)
                
                if not page or not letterhead_page:
                    error_msg = f"Failed to get page {page_num}"
                    logging.error(error_msg)
                    raise PDFMergeError(error_msg)
                
                media_box = CoreGraphics.CGPDFPageGetBoxRect(page, CoreGraphics.kCGPDFMediaBox)
                if CoreGraphics.CGRectIsEmpty(media_box):
                    media_box = None
                
                CoreGraphics.CGContextBeginPage(write_context, media_box)
                CoreGraphics.CGContextDrawPDFPage(write_context, page)
                CoreGraphics.CGContextSetBlendMode(write_context, CoreGraphics.kCGBlendModeNormal)
                CoreGraphics.CGContextDrawPDFPage(write_context, letterhead_page)
                CoreGraphics.CGContextEndPage(write_context)
            
            CoreGraphics.CGPDFContextClose(write_context)
            logging.info("PDF merge completed successfully")

        except Exception as e:
            error_msg = f"Error merging PDFs: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg)

def create_service_script(letterhead_path: str) -> None:
    """Create a PDF Service script for the given letterhead"""
    logging.info(f"Creating PDF Service script for: {letterhead_path}")
    pdf_services_dir = os.path.expanduser("~/Library/PDF Services")
    os.makedirs(pdf_services_dir, exist_ok=True)
    
    letterhead_name = os.path.splitext(os.path.basename(letterhead_path))[0]
    script_name = f"Letterhead {letterhead_name}"
    script_path = os.path.join(pdf_services_dir, script_name)
    
    script_content = f'''#!/bin/bash
# Letterhead PDF Service for {letterhead_name}
uvx mac-letterhead print "{os.path.abspath(letterhead_path)}" "$1" "$2" "$3"
'''
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    logging.info(f"Created PDF Service: {script_path}")

def print_command(args: argparse.Namespace) -> int:
    """Handle the print command"""
    try:
        logging.info(f"Starting print command with args: {args}")
        letterhead = LetterheadPDF(letterhead_path=args.letterhead_path)
        
        # Use save dialog to get output location
        short_name = os.path.splitext(args.title)[0]
        output_path = letterhead.save_dialog(letterhead.destination, short_name + letterhead.suffix)
        
        if not output_path:
            logging.warning("Save dialog cancelled")
            print("Save dialog cancelled.")
            return 1
            
        if not os.path.exists(args.input_path):
            error_msg = f"Input file not found: {args.input_path}"
            logging.error(error_msg)
            print(error_msg)
            return 1
            
        letterhead.merge_pdfs(args.input_path, output_path)
        logging.info("Print command completed successfully")
        return 0
        
    except PDFMergeError as e:
        logging.error(str(e))
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"Unexpected error: {str(e)}")
        return 1

def install_command(args: argparse.Namespace) -> int:
    """Handle the install command"""
    try:
        logging.info(f"Starting install command with args: {args}")
        if not os.path.exists(args.letterhead_path):
            error_msg = f"Letterhead PDF not found: {args.letterhead_path}"
            logging.error(error_msg)
            print(error_msg)
            return 1
            
        create_service_script(args.letterhead_path)
        logging.info("Install command completed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"Error installing service: {str(e)}", exc_info=True)
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
    
    logging.info(f"Starting Mac-letterhead v{__version__}")
    
    if args.command == 'install':
        return install_command(args)
    elif args.command == 'print':
        return print_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error("Fatal error", exc_info=True)
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
