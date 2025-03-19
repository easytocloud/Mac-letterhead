#!/usr/bin/env python3

import sys
import os
import argparse
import logging
from typing import Optional, Dict, Any
from Quartz import PDFKit, CoreGraphics, kCGPDFContextUserPassword
from Foundation import (NSURL, kCFAllocatorDefault, NSObject, NSApplication,
                      NSRunLoop, NSDate, NSDefaultRunLoopMode)
from AppKit import (NSSavePanel, NSApp, NSFloatingWindowLevel,
                   NSModalResponseOK, NSModalResponseCancel,
                   NSApplicationActivationPolicyRegular)

from letterhead_pdf import __version__
from letterhead_pdf.pdf_merger import PDFMerger, PDFMergeError
from letterhead_pdf.installer import create_applescript_droplet

# Set up logging
LOG_DIR = os.path.expanduser("~/Library/Logs/Mac-letterhead")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "letterhead.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)  # Log to stderr for PDF Service context
    ]
)

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        logging.info("Application finished launching")

    def applicationWillTerminate_(self, notification):
        logging.info("Application will terminate")

class LetterheadPDF:
    def __init__(self, letterhead_path: str, destination: str = "~/Desktop", suffix: str = " wm.pdf"):
        self.letterhead_path = os.path.expanduser(letterhead_path)
        self.destination = os.path.expanduser(destination)
        self.suffix = suffix
        logging.info(f"Initializing LetterheadPDF with template: {self.letterhead_path}")

    def save_dialog(self, directory: str, filename: str) -> str:
        """Show save dialog and return selected path"""
        logging.info(f"Opening save dialog with initial directory: {directory}")
        
        try:
            # Initialize application if needed
            app = NSApplication.sharedApplication()
            if not app.delegate():
                delegate = AppDelegate.alloc().init()
                app.setDelegate_(delegate)
            
            # Set activation policy to regular to show UI properly
            app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
            
            if not app.isRunning():
                app.finishLaunching()
                logging.info("Application initialized")
            
            # Process events to ensure UI is ready
            run_loop = NSRunLoop.currentRunLoop()
            run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
            
            panel = NSSavePanel.savePanel()
            panel.setTitle_("Save PDF with Letterhead")
            panel.setLevel_(NSFloatingWindowLevel)  # Make dialog float above other windows
            my_url = NSURL.fileURLWithPath_isDirectory_(directory, True)
            panel.setDirectoryURL_(my_url)
            panel.setNameFieldStringValue_(filename)
            
            # Ensure app is active
            app.activateIgnoringOtherApps_(True)
            
            # Process events again
            run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
            
            logging.info("Running save dialog")
            ret_value = panel.runModal()
            logging.info(f"Save dialog return value: {ret_value}")
            
            if ret_value == NSModalResponseOK:
                selected_path = panel.filename()
                if not selected_path:
                    # If no path but OK was clicked, use default location
                    selected_path = os.path.join(directory, filename)
                logging.info(f"Save dialog result: {selected_path}")
                return selected_path
            else:
                logging.info("Save dialog cancelled")
                return ''
                
        except Exception as e:
            logging.error(f"Error in save dialog: {str(e)}", exc_info=True)
            raise PDFMergeError(f"Save dialog error: {str(e)}")

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

    def merge_pdfs(self, input_path: str, output_path: str, strategy: str = "all") -> None:
        """
        Merge letterhead with input PDF
        
        Args:
            input_path: Path to the content PDF
            output_path: Path to save the merged PDF
            strategy: Merging strategy to use. If "all", attempts multiple strategies
                     in separate files to compare results.
        """
        try:
            logging.info(f"Starting PDF merge with strategy '{strategy}': {input_path} -> {output_path}")
            
            # Create the PDF merger with our letterhead
            merger = PDFMerger(self.letterhead_path)
            
            if strategy == "all":
                # Try multiple strategies and save as separate files for comparison
                strategies = ["multiply", "reverse", "overlay", "transparency", "darken"]
                base_name, ext = os.path.splitext(output_path)
                
                for s in strategies:
                    strategy_path = f"{base_name}_{s}{ext}"
                    logging.info(f"Trying strategy '{s}': {strategy_path}")
                    merger.merge(input_path, strategy_path, strategy=s)
                    print(f"Created merged PDF with '{s}' strategy: {strategy_path}")
                
                # Also create the requested output with the default strategy
                merger.merge(input_path, output_path, strategy="darken")
                print(f"Created merged PDF with default 'darken' strategy: {output_path}")
                print(f"Generated {len(strategies) + 1} files with different merging strategies for comparison")
            else:
                # Use the specified strategy
                merger.merge(input_path, output_path, strategy=strategy)
            
            logging.info("PDF merge completed successfully")

        except Exception as e:
            error_msg = f"Error merging PDFs: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg)
def print_command(args: argparse.Namespace) -> int:
    """Handle the print command"""
    try:
        logging.info(f"Starting print command with args: {args}")
        
        # Initialize with custom suffix if provided
        suffix = f" {args.output_postfix}.pdf" if hasattr(args, 'output_postfix') and args.output_postfix else " wm.pdf"
        
        # Create LetterheadPDF instance with custom suffix and destination
        destination = args.save_dir if hasattr(args, 'save_dir') and args.save_dir else "~/Desktop"
        letterhead = LetterheadPDF(letterhead_path=args.letterhead_path, destination=destination, suffix=suffix)
        
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
            
        letterhead.merge_pdfs(args.input_path, output_path, strategy=args.strategy)
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
        
        # Get the letterhead filename without extension for app name
        letterhead_name = os.path.splitext(os.path.basename(args.letterhead_path))[0]
        app_name = f"Letterhead {letterhead_name}"
        
        # Create the AppleScript droplet
        app_path = create_applescript_droplet(
            letterhead_path=args.letterhead_path,
            app_name=app_name if hasattr(args, 'name') and args.name else app_name,
            output_dir=args.output_dir if hasattr(args, 'output_dir') else None
        )
        
        logging.info(f"Install command completed successfully: {app_path}")
        return 0
        
    except Exception as e:
        logging.error(f"Error creating letterhead app: {str(e)}", exc_info=True)
        print(f"Error creating letterhead app: {str(e)}")
        return 1

def main(args: Optional[list] = None) -> int:
    """Main entry point"""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Letterhead PDF Utility")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Create a letterhead droplet application')
    install_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    install_parser.add_argument('--name', help='Custom name for the applier app (default: "Letterhead <filename>")')
    install_parser.add_argument('--output-dir', help='Directory to save the app (default: Desktop)')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge letterhead with document')
    merge_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    merge_parser.add_argument('title', help='Output file title')
    merge_parser.add_argument('save_dir', help='Directory to save the output file')
    merge_parser.add_argument('input_path', help='Input PDF file path')
    merge_parser.add_argument('--strategy', choices=['multiply', 'reverse', 'overlay', 'transparency', 'darken', 'all'],
                            default='darken', help='Merging strategy to use (default: darken)')
    merge_parser.add_argument('--output-postfix', help='Postfix to add to output filename instead of "wm"')
    
    args = parser.parse_args(args)
    
    logging.info(f"Starting Mac-letterhead v{__version__}")
    
    if args.command == 'install':
        return install_command(args)
    elif args.command == 'merge':
        return print_command(args)
    elif args.command == 'print':  # Keep support for old print command for backward compatibility
        return print_command(args)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error("Fatal error", exc_info=True)
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)
