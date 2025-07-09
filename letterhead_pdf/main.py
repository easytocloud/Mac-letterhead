#!/usr/bin/env python3

import sys
import os
import argparse
import logging
import tempfile
from typing import Optional, Dict, Any
from Quartz import PDFKit, CoreGraphics, kCGPDFContextUserPassword
from Foundation import (NSURL, kCFAllocatorDefault, NSObject, NSApplication,
                      NSRunLoop, NSDate, NSDefaultRunLoopMode)
# Import markdown processor - simplified import logic
try:
    from letterhead_pdf.markdown_processor import MarkdownProcessor, MARKDOWN_AVAILABLE
except ImportError as e:
    print(f"Error importing markdown processor: {e}")
    MARKDOWN_AVAILABLE = False
    MarkdownProcessor = None
from AppKit import (NSSavePanel, NSApp, NSFloatingWindowLevel,
                   NSModalResponseOK, NSModalResponseCancel,
                   NSApplicationActivationPolicyRegular)

from letterhead_pdf import __version__
from letterhead_pdf.pdf_merger import PDFMerger
from letterhead_pdf.installation import DropletBuilder
from letterhead_pdf.exceptions import InstallerError, PDFMergeError, PDFCreationError, PDFMetadataError

# Import logging configuration
from letterhead_pdf.log_config import LOG_DIR, LOG_FILE, configure_logging

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

    # The PDF utility methods have been moved to pdf_utils.py

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

        except PDFMergeError as e:
            # Specific handling for PDF merge errors
            logging.error(f"PDF merge error: {str(e)}")
            raise
        except Exception as e:
            # General exception handling for other unexpected errors
            error_msg = f"Error merging PDFs: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise PDFMergeError(error_msg)
def merge_md_command(args: argparse.Namespace) -> int:
    """Handle the merge-md command for Markdown files"""
    try:
        logging.info(f"Starting merge-md command with args: {args}")
        
        # Check if Markdown is available
        if not MARKDOWN_AVAILABLE:
            error_msg = (
                "Markdown module not available. For Markdown processing, please install the required dependencies:\n"
                "Install Mac-letterhead with Markdown support: uvx mac-letterhead[markdown]@0.8.0\n\n"
                "For more information, see the installation instructions in the README."
            )
            logging.error("Markdown module not available for Markdown processing")
            print(error_msg)
            return 1
        
        # Check if WeasyPrint is available
        import importlib.util
        weasyprint_available = importlib.util.find_spec("weasyprint") is not None
        
        if not weasyprint_available:
            logging.warning("WeasyPrint not available, falling back to ReportLab for Markdown processing")
            print("Note: WeasyPrint is not installed. Using ReportLab for Markdown processing (limited formatting).")
            print("For high-quality Markdown processing, please install the required dependencies:")
            print("1. Install system dependencies: brew install pango cairo fontconfig freetype harfbuzz")
            print("2. Install Mac-letterhead with Markdown support: uvx mac-letterhead[markdown]@0.8.0")
        
        # Initialize with custom suffix if provided
        suffix = f" {args.output_postfix}.pdf" if hasattr(args, 'output_postfix') and args.output_postfix else " wm.pdf"
        
        # Create LetterheadPDF instance with custom suffix and destination
        destination = args.save_dir if hasattr(args, 'save_dir') and args.save_dir else "~/Desktop"
        letterhead = LetterheadPDF(letterhead_path=args.letterhead_path, destination=destination, suffix=suffix)
        
        # Determine output path
        if hasattr(args, 'output') and args.output:
            # Use specified output path directly
            output_path = os.path.expanduser(args.output)
            logging.info(f"Using specified output path: {output_path}")
        else:
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
        
        # Create a temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert markdown to PDF
            md_processor = MarkdownProcessor()
            temp_pdf = os.path.join(temp_dir, "converted.pdf")
            
            try:
                # Convert markdown to PDF with proper margins
                md_processor.md_to_pdf(args.input_path, temp_pdf, args.letterhead_path)
                
                # Merge the converted PDF with letterhead
                letterhead.merge_pdfs(temp_pdf, output_path, strategy=args.strategy)
                
                logging.info("Merge-md command completed successfully")
                print(f"Successfully created PDF with letterhead: {output_path}")
                return 0
                
            except Exception as e:
                error_msg = f"Error processing markdown: {str(e)}"
                logging.error(error_msg)
                print(error_msg)
                return 1
                
    except Exception as e:
        logging.error(f"Error in merge-md command: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1

def print_command(args: argparse.Namespace) -> int:
    """Handle the print command"""
    try:
        logging.info(f"Starting print command with args: {args}")
        
        # Initialize with custom suffix if provided
        suffix = f" {args.output_postfix}.pdf" if hasattr(args, 'output_postfix') and args.output_postfix else " wm.pdf"
        
        # Create LetterheadPDF instance with custom suffix and destination
        destination = args.save_dir if hasattr(args, 'save_dir') and args.save_dir else "~/Desktop"
        letterhead = LetterheadPDF(letterhead_path=args.letterhead_path, destination=destination, suffix=suffix)
        
        # Determine output path
        if hasattr(args, 'output') and args.output:
            # Use specified output path directly
            output_path = os.path.expanduser(args.output)
            logging.info(f"Using specified output path: {output_path}")
        else:
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
        logging.error(f"PDF merge error: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    except PDFCreationError as e:
        logging.error(f"PDF creation error: {str(e)}")
        print(f"Error creating PDF: {str(e)}")
        return 1
    except PDFMetadataError as e:
        logging.error(f"PDF metadata error: {str(e)}")
        print(f"Error reading PDF metadata: {str(e)}")
        return 1
    except UIError as e:
        logging.error(f"UI error: {str(e)}")
        print(f"User interface error: {str(e)}")
        return 1
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    except PermissionError as e:
        logging.error(f"Permission error: {str(e)}")
        print(f"Error: Insufficient permissions: {str(e)}")
        return 1
    except ValueError as e:
        logging.error(f"Invalid value: {str(e)}")
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
        
        # Check for development mode
        is_dev = hasattr(args, 'dev') and args.dev
        python_path = getattr(args, 'python_path', None) if is_dev else None
        
        if is_dev:
            app_name += " (Dev)"
            logging.info("Creating development droplet")
        
        # Create the droplet builder and build the droplet
        builder = DropletBuilder(
            development_mode=is_dev,
            python_path=python_path
        )
        
        app_path = builder.create_droplet(
            letterhead_path=args.letterhead_path,
            app_name=args.name if hasattr(args, 'name') and args.name else app_name,
            output_dir=args.output_dir if hasattr(args, 'output_dir') else None
        )
        
        logging.info(f"Install command completed successfully: {app_path}")
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    except PermissionError as e:
        logging.error(f"Permission error: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    except InstallerError as e:
        logging.error(f"Installation error: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        logging.error(f"Error creating letterhead app: {str(e)}", exc_info=True)
        print(f"Unexpected error: {str(e)}")
        return 1

def main(args: Optional[list] = None) -> int:
    """Main entry point"""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Letterhead PDF Utility")
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        help='Set logging level (default depends on command)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Create a letterhead droplet application')
    install_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    install_parser.add_argument('--name', help='Custom name for the applier app (default: "Letterhead <filename>")')
    install_parser.add_argument('--output-dir', help='Directory to save the app (default: Desktop)')
    install_parser.add_argument('--dev', action='store_true', help='Create a development droplet using local code')
    install_parser.add_argument('--python-path', help='Path to Python interpreter for development mode (default: current interpreter)')
    
    # Merge commands
    merge_parser = subparsers.add_parser('merge', help='Merge letterhead with PDF document')
    merge_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    merge_parser.add_argument('title', help='Output file title')
    merge_parser.add_argument('save_dir', help='Directory to save the output file')
    merge_parser.add_argument('input_path', help='Input PDF file path')
    merge_parser.add_argument('--strategy', choices=['multiply', 'reverse', 'overlay', 'transparency', 'darken', 'all'],
                            default='darken', help='Merging strategy to use (default: darken)')
    merge_parser.add_argument('--output-postfix', help='Postfix to add to output filename instead of "wm"')
    merge_parser.add_argument('--output', help='Specify output file path directly (bypasses save dialog)')
    
    # Add merge-md command
    merge_md_parser = subparsers.add_parser('merge-md', help='Convert Markdown to PDF and merge with letterhead')
    merge_md_parser.add_argument('letterhead_path', help='Path to letterhead PDF template')
    merge_md_parser.add_argument('title', help='Output file title')
    merge_md_parser.add_argument('save_dir', help='Directory to save the output file')
    merge_md_parser.add_argument('input_path', help='Input Markdown file path')
    merge_md_parser.add_argument('--strategy', choices=['multiply', 'reverse', 'overlay', 'transparency', 'darken', 'all'],
                              default='darken', help='Merging strategy to use (default: darken)')
    merge_md_parser.add_argument('--output-postfix', help='Postfix to add to output filename instead of "wm"')
    merge_md_parser.add_argument('--output', help='Specify output file path directly (bypasses save dialog)')
    
    args = parser.parse_args(args)
    
    # Set log level based on command and command-line arguments
    if args.log_level:
        # Use user-provided log level if specified
        log_level = getattr(logging, args.log_level)
    else:
        # Default log levels per command
        if args.command == 'install':
            log_level = logging.WARNING  # Less verbose for install command
        else:
            log_level = logging.INFO  # More verbose for other commands
    
    # Configure logging with the appropriate level
    configure_logging(level=log_level)
    
    # Now that logging is configured with the appropriate level
    if log_level <= logging.INFO:
        logging.info(f"Starting Mac-letterhead v{__version__}")
    
    if args.command == 'install':
        return install_command(args)
    elif args.command == 'merge':
        return print_command(args)
    elif args.command == 'merge-md':
        return merge_md_command(args)
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
