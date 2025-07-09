#!/usr/bin/env python3

import sys
import os
import logging
import shutil
import tempfile
from subprocess import run, PIPE
from typing import Optional

# Import logging configuration and version
from letterhead_pdf.log_config import LOG_DIR, LOG_FILE, configure_logging
from letterhead_pdf.exceptions import InstallerError
from letterhead_pdf import __version__

def create_applescript_droplet(letterhead_path: str, app_name: str = "Letterhead Applier", output_dir: str = None) -> str:
    """Create an AppleScript droplet application for the given letterhead"""
    logging.info(f"Creating AppleScript droplet for: {letterhead_path}")
    logging.info(f"Using version from __init__.py: {__version__}")
    
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
    
    # Store version for use in AppleScript
    version = __version__
    logging.info(f"Using version for droplet: {version}")
    
    # Create temporary directory structure
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create the AppleScript with enhanced security and error handling
        applescript_content = f'''-- Letterhead Applier AppleScript Droplet
-- This script takes dropped PDF and Markdown files and applies a letterhead template
-- Enhanced for macOS Tahoe beta security requirements

on open these_items
    -- First, check if we have any items
    if (count of these_items) is 0 then
        display dialog "No files were dropped. Please drag PDF or Markdown files onto this application." buttons {{"OK"}} default button "OK" with icon note
        return
    end if
    
    -- Process each dropped file with enhanced error handling
    repeat with i from 1 to count of these_items
        set this_item to item i of these_items
        
        try
            -- Enhanced file validation for security
            tell application "System Events"
                set file_exists to exists file (this_item as string)
                if not file_exists then
                    display dialog "File no longer exists or cannot be accessed: " & (this_item as string) buttons {{"OK"}} default button "OK" with icon caution
                    return
                end if
                
                set file_info to info for this_item
                set file_name to name of file_info
                set file_extension to name extension of file_info
            end tell
            
            -- Check if it's a supported file type (case insensitive)
            set file_extension_lower to my toLower(file_extension)
            if file_extension_lower is not in {{"pdf", "md", "markdown"}} then
                display dialog "Unsupported file type: " & file_extension & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md, .markdown)" buttons {{"OK"}} default button "OK" with icon stop
                return
            end if
            
            -- Get the POSIX path safely
            set input_file to POSIX path of this_item
            
            -- Get paths and validate letterhead
            set app_path to POSIX path of (path to me)
            set app_bundle to my getAppBundle(app_path)
            set letterhead_path to app_bundle & "/Contents/Resources/letterhead.pdf"
            
            -- Validate letterhead exists
            tell application "System Events"
                if not (exists file letterhead_path) then
                    display dialog "Letterhead template not found. Please reinstall the letterhead applier." buttons {{"OK"}} default button "OK" with icon stop
                    return
                end if
            end tell
            
            -- Create log directory
            do shell script "mkdir -p \\"$HOME/Library/Logs/Mac-letterhead\\""
            
            -- Get file basename without extension
            set file_basename to my getBasename(file_name, file_extension)
            
            -- Get the directory of the source file for default save location
            set source_dir to do shell script "dirname " & quoted form of input_file
            set home_path to POSIX path of (path to home folder)
            
            -- Get the application name for postfix
            set app_name to do shell script "basename " & quoted form of app_path & " | sed 's/\\\\.app$//'"
            
            -- Build the command with proper quoting and error handling
            set cmd to "export HOME=" & quoted form of home_path & " && cd " & quoted form of source_dir
            set cmd to cmd & " && /usr/bin/env PATH=$HOME/.local/bin:$HOME/Library/Python/*/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin uvx --quiet mac-letterhead@{version} "
            
            -- Choose command based on file type
            if file_extension_lower is in {{"md", "markdown"}} then
                set cmd to cmd & "merge-md "
            else
                set cmd to cmd & "merge "
            end if
            
            set cmd to cmd & quoted form of letterhead_path & " \\"" & file_basename & "\\" " & quoted form of source_dir & " " & quoted form of input_file & " --strategy darken --output-postfix \\"" & app_name & "\\""
            
            -- Execute the command with enhanced error handling
            try
                -- Log the command for debugging
                do shell script "echo 'Processing: " & file_name & "' >> \\"$HOME/Library/Logs/Mac-letterhead/droplet.log\\""
                do shell script "echo 'Command: " & cmd & "' >> \\"$HOME/Library/Logs/Mac-letterhead/droplet.log\\""
                
                -- Execute the main command
                set result_output to do shell script cmd
                
                -- Log success
                do shell script "echo 'Success: " & file_name & "' >> \\"$HOME/Library/Logs/Mac-letterhead/droplet.log\\""
                
                -- Show success notification (brief)
                display notification "Successfully processed " & file_name with title "Letterhead Applied"
                
            on error execErr
                -- Enhanced error handling with user-friendly messages
                set error_msg to "Error processing " & file_name & ":" & return & return
                
                if execErr contains "Markdown module not available" then
                    set error_msg to error_msg & "Markdown processing is not available. This may be due to missing dependencies." & return & return & "Solutions:" & return & "1. Try processing a PDF file instead" & return & "2. Contact support for assistance with Markdown files"
                else if execErr contains "uvx" then
                    set error_msg to error_msg & "Could not run mac-letterhead. Please ensure it's properly installed." & return & return & "Try running this in Terminal:" & return & "uvx mac-letterhead@{version} --version"
                else
                    set error_msg to error_msg & execErr
                end if
                
                -- Log the error
                do shell script "echo 'Error: " & execErr & "' >> \\"$HOME/Library/Logs/Mac-letterhead/droplet.log\\""
                
                display dialog error_msg buttons {{"OK"}} default button "OK" with icon stop
            end try
            
        on error errMsg
            -- Top-level error handling
            do shell script "echo 'Top-level error: " & errMsg & "' >> \\"$HOME/Library/Logs/Mac-letterhead/droplet.log\\""
            display dialog "Error processing file: " & errMsg buttons {{"OK"}} default button "OK" with icon stop
        end try
    end repeat
end open

on run
    display dialog "Letterhead Applier v{version}" & return & return & "To apply a letterhead to a document:" & return & "1. Drag and drop a PDF or Markdown (.md) file onto this application icon" & return & "2. The letterhead will be applied automatically" & return & "3. You'll be prompted to save the merged document" & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md, .markdown) - converted to PDF with proper margins" & return & return & "Note: On macOS Tahoe beta, you may need to approve file access the first time." buttons {{"OK"}} default button "OK"
end run

-- Helper function to convert text to lowercase
on toLower(str)
    return do shell script "echo " & quoted form of str & " | tr '[:upper:]' '[:lower:]'"
end toLower

-- Helper function to get app bundle path
on getAppBundle(app_path)
    return do shell script "echo " & quoted form of app_path & " | sed -E 's:/Contents/.*$::'"
end getAppBundle

-- Helper function to get basename without extension
on getBasename(file_name, file_extension)
    if file_extension is "" then
        return file_name
    else
        set ext_length to (length of file_extension) + 1
        return text 1 thru -(ext_length) of file_name
    end if
end getBasename'''
        
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
