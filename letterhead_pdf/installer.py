#!/usr/bin/env python3

import sys
import os
import logging
import shutil
import tempfile
from subprocess import run, PIPE
from typing import Optional

# Import logging configuration
from letterhead_pdf.log_config import LOG_DIR, LOG_FILE, configure_logging
from letterhead_pdf.exceptions import InstallerError

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
    
    # Remove existing app if it exists (to avoid signature issues on macOS)
    if os.path.exists(app_path):
        logging.info(f"Removing existing app: {app_path}")
        try:
            shutil.rmtree(app_path)
        except Exception as e:
            logging.warning(f"Could not remove existing app: {e} - trying to continue anyway")
    
    # Create temporary directory structure
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
            
            -- Check if it's a supported file type
            if this_path ends with ".pdf" or this_path ends with ".PDF" or this_path ends with ".md" or this_path ends with ".MD" then
                -- Get the POSIX path and determine file type
                set input_file to POSIX path of this_item
                
                -- Get the full application path
                set app_path to POSIX path of (path to me)
                
                -- We know exactly where the letterhead PDF is located
                do shell script "mkdir -p \\"$HOME/Library/Logs/Mac-letterhead\\""
                
                -- Get the app bundle path
                -- First get the directory of the executable (Contents/MacOS)
                set app_dir to do shell script "dirname " & quoted form of app_path
                
                -- Then go up to the .app bundle, containing the required components
                set app_bundle to do shell script "echo " & quoted form of app_path & " | sed -E 's:/Contents/.*$::'"
                
                -- The letterhead is always in the Resources folder (we put it there during creation)
                set letterhead_path to app_bundle & "/Contents/Resources/letterhead.pdf"
                set home_path to POSIX path of (path to home folder)
                
                -- Make sure the letterhead file exists
                if (do shell script "[ -f \\"" & letterhead_path & "\\" ] && echo \\"yes\\" || echo \\"no\\"") is "no" then
                    error "Letterhead template not found at " & letterhead_path & ". Please reinstall the letterhead applier."
                end if
                
                -- Get file extension and basename
                set file_ext to do shell script "echo " & quoted form of this_path & " | tr '[:upper:]' '[:lower:]' | grep -o '\\\\.[^.]*$'"
                set quoted_input_file to quoted form of input_file
                set file_basename to do shell script "basename " & quoted_input_file & " " & file_ext
                
                -- Get the directory of the source file for default save location
                set source_dir to do shell script "dirname " & quoted_input_file
                
                -- Get the application name for postfix
                set app_name to do shell script "basename " & quoted form of app_path & " | sed 's/\\\\.app$//'"
                
                -- Build the command
                set cmd to "export HOME=" & quoted form of home_path & " && cd " & quoted form of source_dir
                -- Get the version from the app bundle's Info.plist
                set version_cmd to "defaults read " & quoted form of app_bundle & "/Contents/Info CFBundleShortVersionString 2>/dev/null || echo \\"0.6.9\\""
                set version to do shell script version_cmd
                
                set cmd to cmd & " && /usr/bin/env PATH=$HOME/.local/bin:$HOME/Library/Python/*/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin uvx mac-letterhead@" & version & " "
                
                if file_ext is equal to ".md" then
                    -- For markdown files, use merge-md command
                    set cmd to cmd & "merge-md "
                else
                    -- For PDF files, use merge command
                    set cmd to cmd & "merge "
                end if
                
                set cmd to cmd & quoted form of letterhead_path & " \\"" & file_basename & "\\" " & quoted form of source_dir & " " & quoted_input_file & " --strategy darken --output-postfix \\"" & app_name & "\\""
                
                -- Execute the command with careful handling for immediate error feedback
                try
                    do shell script cmd
                on error execErr
                    display dialog "Error processing file: " & execErr buttons {"OK"} default button "OK" with icon stop
                    error execErr
                end try
            else
                -- Not a supported file type
                display dialog "Unsupported file type. Please use PDF (.pdf) or Markdown (.md) files." buttons {"OK"} default button "OK" with icon stop
            end if
        on error errMsg
            -- Error getting file info
            display dialog "Error processing file: " & errMsg buttons {"OK"} default button "OK" with icon stop
        end try
    end repeat
end open

on run
    display dialog "Letterhead Applier" & return & return & "To apply a letterhead to a document:" & return & "1. Drag and drop a PDF or Markdown (.md) file onto this application icon" & return & "2. The letterhead will be applied automatically" & return & "3. You'll be prompted to save the merged document" & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md) - will be converted to PDF with proper margins" buttons {"OK"} default button "OK"
end run'''
        
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
            raise InstallerError(error_msg)
        
        # Copy letterhead to the compiled app bundle's Resources folder
        app_resources_dir = os.path.join(app_path, "Contents", "Resources")
        os.makedirs(app_resources_dir, exist_ok=True)
        
        app_letterhead = os.path.join(app_resources_dir, "letterhead.pdf")
        shutil.copy2(abs_letterhead_path, app_letterhead)
        logging.info(f"Added letterhead to app bundle: {app_letterhead}")
        
        # Set the custom icon
        try:
            # Direct path to icon resources - we know exactly where they are
            custom_icon_path = os.path.join(os.path.dirname(__file__), "resources", "Mac-letterhead.icns")
            
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
                
                # Use the fileicon tool if available (simple method)
                try:
                    fileicon_result = run(["which", "fileicon"], capture_output=True, text=True, check=False)
                    if fileicon_result.returncode == 0 and fileicon_result.stdout.strip():
                        fileicon_path = fileicon_result.stdout.strip()
                        run([fileicon_path, "set", app_path, custom_icon_path], check=False)
                        logging.info("Set app icon using fileicon tool")
                except Exception as e:
                    logging.warning(f"Could not set icon with fileicon tool: {e}")
            else:
                logging.warning(f"Custom icon not found at {custom_icon_path}, using default AppleScript icon")
        except Exception as e:
            logging.warning(f"Could not set custom icon: {str(e)} - using default icon")
            
        print(f"Created Letterhead Applier app: {app_path}")
        print(f"You can now drag and drop PDF or Markdown (.md) files onto the app to apply the letterhead.")
        
        return app_path
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
