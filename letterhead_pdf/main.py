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

def create_applescript_droplet(letterhead_path: str, app_name: str = "Letterhead Applier", output_dir: str = None) -> str:
    """Create an AppleScript droplet application for the given letterhead"""
    logging.info(f"Creating AppleScript droplet for: {letterhead_path}")
    
    # Ensure absolute path for letterhead
    abs_letterhead_path = os.path.abspath(letterhead_path)
    
    # Determine output directory (Desktop by default)
    if output_dir is None:
        output_dir = os.path.expanduser("~/Desktop")
    else:
        output_dir = os.path.expanduser(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # App path with extension
    app_path = os.path.join(output_dir, f"{app_name}.app")
    
    # Create temporary directory structure
    import tempfile
    import shutil
    from subprocess import run, PIPE
    
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create the AppleScript
        applescript_content = '''-- Letterhead Applier AppleScript Droplet
-- This script takes dropped PDF files and applies a letterhead template

on open these_items
    -- Process each dropped file
    repeat with i from 1 to count of these_items
        set this_item to item i of these_items
        
        try
            -- Get the file path as string directly from the dropped item
            set this_path to this_item as string
            
            -- Check if it's a PDF file by extension
            if this_path ends with ".pdf" or this_path ends with ".PDF" then
                -- Get the POSIX path directly
                set input_pdf to POSIX path of this_item
                
                -- Get the full application path
                set app_path to POSIX path of (path to me)
                
                -- Find the letterhead PDF by looking in several places
                -- 1. Try to locate it in the app bundle (multiple possible locations)
                -- 2. If not found, fall back to creating a temporary copy on the Desktop
                set test_path_1 to do shell script "dirname \\"" & app_path & "\\" | sed 's|/Scripts$||'"
                set test_path_1 to test_path_1 & "/letterhead.pdf"
                
                set test_path_2 to do shell script "dirname \\"" & app_path & "\\""
                set test_path_2 to test_path_2 & "/letterhead.pdf"
                
                set test_path_3 to do shell script "dirname \\"" & app_path & "\\" | sed 's|/Contents/Resources/Scripts$|/Contents/Resources|'"
                set test_path_3 to test_path_3 & "/letterhead.pdf"
                
                -- Create a temporary directory for storing diagnostic info
                do shell script "mkdir -p \\"$HOME/Library/Logs/Mac-letterhead\\""
                do shell script "echo 'Testing path 1: " & test_path_1 & "' > \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                do shell script "ls -la \\"" & test_path_1 & "\\" >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\" 2>&1 || echo 'Not found' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                
                do shell script "echo 'Testing path 2: " & test_path_2 & "' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                do shell script "ls -la \\"" & test_path_2 & "\\" >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\" 2>&1 || echo 'Not found' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                
                do shell script "echo 'Testing path 3: " & test_path_3 & "' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                do shell script "ls -la \\"" & test_path_3 & "\\" >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\" 2>&1 || echo 'Not found' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                
                -- Check each path and use the first one that exists
                set home_path to POSIX path of (path to home folder)
                set letterhead_path to home_path & "/Desktop/letterhead.pdf"
                
                if (do shell script "[ -f \\"" & test_path_1 & "\\" ] && echo \\"yes\\" || echo \\"no\\"") is "yes" then
                    set letterhead_path to test_path_1
                else if (do shell script "[ -f \\"" & test_path_2 & "\\" ] && echo \\"yes\\" || echo \\"no\\"") is "yes" then
                    set letterhead_path to test_path_2
                else if (do shell script "[ -f \\"" & test_path_3 & "\\" ] && echo \\"yes\\" || echo \\"no\\"") is "yes" then
                    set letterhead_path to test_path_3
                else
                    -- If we can't find the letterhead, extract it from the app
                    set app_dir to do shell script "dirname " & quoted form of app_path
                    do shell script "find " & quoted form of app_dir & " -name 'letterhead.pdf' > \\"$HOME/Library/Logs/Mac-letterhead/find_letterhead.log\\" 2>&1"
                    
                    -- As a last resort, make a copy in the Desktop folder
                    display dialog "Extracting letterhead template to Desktop..." buttons {} giving up after 1
                    do shell script "find " & quoted form of app_dir & " -name 'letterhead.pdf' -print | head -n 1 | xargs -I {} cp -f {} \\"" & home_path & "/Desktop/letterhead.pdf\\" || echo \\"Extraction failed\\" > \\"$HOME/Library/Logs/Mac-letterhead/extract.log\\" 2>&1"
                end if
                
                -- For better UX, use the source directory for output and application name for postfix
                set quoted_input_pdf to quoted form of input_pdf
                set file_basename to do shell script "basename " & quoted_input_pdf & " .pdf"
                
                -- Get the directory of the source PDF for default save location
                set source_dir to do shell script "dirname " & quoted_input_pdf
                
                -- Get the application name for postfix
                set app_name to do shell script "basename " & quoted form of app_path & " | sed 's/\\\\.app$//'"
                
                -- Display progress dialog
                display dialog "Applying letterhead to " & file_basename & ".pdf..." buttons {} giving up after 1
                
                -- Run the command with error handling
                try
                    -- Pass explicit HOME to ensure environment is correct
                    set home_path to POSIX path of (path to home folder)
                    
                    -- Create logs directory
                    do shell script "mkdir -p " & quoted form of home_path & "/Library/Logs/Mac-letterhead"
                    
                    -- Build the command 
                    -- We change the current directory to the source PDF's directory and set the output filename to use app name
                    set cmd to "export HOME=" & quoted form of home_path & " && cd " & quoted form of source_dir
                    set cmd to cmd & " && /usr/bin/env PATH=$HOME/.local/bin:$HOME/Library/Python/*/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin uvx mac-letterhead merge "
                    set cmd to cmd & quoted form of letterhead_path & " \\"" & file_basename & "\\" " & quoted form of source_dir & " " & quoted_input_pdf & " --strategy darken --output-postfix \\"" & app_name & "\\""
                    
                    -- Log the full command and paths for diagnostics
                    do shell script "echo 'Letterhead path: " & letterhead_path & "' > " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'App path: " & app_path & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'App name: " & app_name & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Source directory: " & source_dir & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Test paths:' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo '  Path 1: " & test_path_1 & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo '  Path 2: " & test_path_2 & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo '  Path 3: " & test_path_3 & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Input PDF: " & input_pdf & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Command: " & cmd & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Checking letterhead exists: ' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "ls -la " & quoted form of letterhead_path & " >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log 2>&1 || echo 'FILE NOT FOUND' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    
                    -- Execute the command with careful handling for immediate error feedback
                    try
                        do shell script cmd
                        -- Log success but don't show a dialog
                        do shell script "echo 'Success: Letterhead applied to " & file_basename & ".pdf' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    on error execErr
                        -- If the command fails, show dialog immediately
                        do shell script "echo 'EXEC ERROR: " & execErr & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                        display dialog "Error processing file: " & execErr buttons {"OK"} default button "OK" with icon stop
                        error execErr -- Re-throw the error to be caught by outer handler
                    end try
                on error errMsg
                    -- Log the error
                    do shell script "echo 'ERROR: " & errMsg & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    
                    -- Error message with details
                    display dialog "Error applying letterhead: " & errMsg buttons {"OK"} default button "OK" with icon stop
                end try
            else
                -- Not a PDF file
                display dialog "File " & this_path & " is not a PDF file." buttons {"OK"} default button "OK" with icon stop
            end if
        on error errMsg
            -- Error getting file info
            display dialog "Error processing file: " & errMsg buttons {"OK"} default button "OK" with icon stop
        end try
    end repeat
end open

on run
    display dialog "Letterhead Applier" & return & return & "To apply a letterhead to a PDF document:" & return & "1. Drag and drop a PDF file onto this application icon" & return & "2. The letterhead will be applied automatically" & return & "3. You'll be prompted to save the merged document" buttons {"OK"} default button "OK"
end run
'''
        
        applescript_path = os.path.join(tmp_dir, "letterhead_droplet.applescript")
        with open(applescript_path, 'w') as f:
            f.write(applescript_content)
        
        # Create Resources directory
        resources_dir = os.path.join(tmp_dir, "Resources")
        os.makedirs(resources_dir, exist_ok=True)
        
        # Copy letterhead to resources
        dest_letterhead = os.path.join(resources_dir, "letterhead.pdf")
        shutil.copy2(abs_letterhead_path, dest_letterhead)
        logging.info(f"Copied letterhead to: {dest_letterhead}")
        
        # Compile AppleScript into application
        logging.info(f"Compiling AppleScript to: {app_path}")
        
        # Use macOS osacompile to create the app
        result = run(["osacompile", "-o", app_path, applescript_path], 
                     capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Failed to compile AppleScript: {result.stderr}"
            logging.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Copy letterhead to the compiled app bundle's Resources folder
        app_resources_dir = os.path.join(app_path, "Contents", "Resources")
        os.makedirs(app_resources_dir, exist_ok=True)
        
        app_letterhead = os.path.join(app_resources_dir, "letterhead.pdf")
        shutil.copy2(abs_letterhead_path, app_letterhead)
        logging.info(f"Added letterhead to app bundle: {app_letterhead}")
        
        # Try to set a custom icon, but continue if we can't due to permissions
        try:
            # Use custom icon from resources directory if available (.icns format is correct for macOS)
            # Use importlib.resources to access package resources (works with installed packages)
            import importlib.resources as pkg_resources
            from importlib.abc import Traversable
            import tempfile
            
            # First check if we can find the resource in the package
            try:
                # Try with importlib.resources API
                with pkg_resources.path('letterhead_pdf', 'resources') as resources_path:
                    custom_icon_path = os.path.join(resources_path, "Mac-letterhead.icns")
                    if not os.path.exists(custom_icon_path):
                        # Try directly within the package directory
                        custom_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "Mac-letterhead.icns")
                    
                    if os.path.exists(custom_icon_path):
                        # Copy icon to app resources
                        app_icon = os.path.join(app_resources_dir, "applet.icns")
                        shutil.copy2(custom_icon_path, app_icon)
                        logging.info(f"Set custom icon: {app_icon}")
                        
                        # Also set document icon if it exists
                        document_icon = os.path.join(app_resources_dir, "droplet.icns")
                        if os.path.exists(document_icon):
                            shutil.copy2(custom_icon_path, document_icon)
                            logging.info(f"Set document icon: {document_icon}")
                    else:
                        logging.info(f"Custom icon not found at {custom_icon_path}, using default AppleScript icon")
                        
            except (ImportError, FileNotFoundError, NotADirectoryError):
                # Fallback to traditional path
                custom_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "Mac-letterhead.icns")
                if os.path.exists(custom_icon_path):
                    app_icon = os.path.join(app_resources_dir, "applet.icns")
                    shutil.copy2(custom_icon_path, app_icon)
                    logging.info(f"Set custom icon (fallback): {app_icon}")
                else:
                    logging.info("Custom icon not found on fallback path, using default AppleScript icon")
        except PermissionError:
            logging.warning("Cannot set icon due to permission restrictions - the app will use the default icon")
        except Exception as e:
            logging.warning(f"Cannot set icon: {str(e)} - continuing with default icon")
            
        print(f"Created Letterhead Applier app: {app_path}")
        print(f"You can now drag and drop PDF files onto the app to apply the letterhead.")
        
        return app_path
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

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
