
#!/usr/bin/env python3

import sys
import os
import logging
import shutil
import tempfile
from subprocess import run, PIPE
from typing import Optional

# Set up logging (use the same constants from main)
LOG_DIR = os.path.expanduser("~/Library/Logs/Mac-letterhead")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "letterhead.log")

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
        import shutil
        try:
            shutil.rmtree(app_path)
        except Exception as e:
            logging.warning(f"Could not remove existing app: {e} - trying to continue anyway")
    
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
                
                -- We know exactly where the letterhead PDF is located
                do shell script "mkdir -p \\"$HOME/Library/Logs/Mac-letterhead\\""
                
                -- Get the app bundle path
                -- First get the directory of the executable (Contents/MacOS)
                set app_dir to do shell script "dirname " & quoted form of app_path
                
                -- Then go up to the .app bundle, containing the required components
                -- We need to extract just the .app bundle path without removing it
                set app_bundle to do shell script "echo " & quoted form of app_path & " | sed -E 's:/Contents/.*$::'"
                
                -- For diagnostics and verification
                do shell script "echo 'Full app path: " & app_path & "' > \\"$HOME/Library/Logs/Mac-letterhead/bundle.log\\""
                do shell script "echo 'Derived bundle: " & app_bundle & "' >> \\"$HOME/Library/Logs/Mac-letterhead/bundle.log\\""
                
                -- The letterhead is always in the Resources folder (we put it there during creation)
                set letterhead_path to app_bundle & "/Contents/Resources/letterhead.pdf"
                set home_path to POSIX path of (path to home folder)
                
                -- Log the paths for diagnostics
                do shell script "echo 'App path: " & app_path & "' > \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                do shell script "echo 'App bundle: " & app_bundle & "' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                do shell script "echo 'Letterhead path: " & letterhead_path & "' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                
                -- Make sure the letterhead file exists
                if (do shell script "[ -f \\"" & letterhead_path & "\\" ] && echo \\"yes\\" || echo \\"no\\"") is "no" then
                    -- Log the error without showing dialog yet (we'll handle it in the outer error catch)
                    do shell script "echo 'ERROR: Letterhead.pdf not found at expected location' >> \\"$HOME/Library/Logs/Mac-letterhead/path_tests.log\\""
                    -- Just throw the error to be caught by outer handler
                    error "Letterhead template not found at " & letterhead_path & ". Please reinstall the letterhead applier."
                end if
                
                -- For better UX, use the source directory for output and application name for postfix
                set quoted_input_pdf to quoted form of input_pdf
                set file_basename to do shell script "basename " & quoted_input_pdf & " .pdf"
                
                -- Get the directory of the source PDF for default save location
                set source_dir to do shell script "dirname " & quoted_input_pdf
                
                -- Get the application name for postfix
                set app_name to do shell script "basename " & quoted form of app_path & " | sed 's/\\\\.app$//'"
                
                -- No progress dialog to avoid confusing users with small files
                -- We'll only show feedback if there's an error
                
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
                    do shell script "echo 'App bundle: " & app_bundle & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
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
            # Standardized approach: Use only letterhead_pdf/resources for icon
            # This is the proper way to access package resources that works for installed packages
            import importlib.resources as pkg_resources
            import tempfile
            
            # Use Python's importlib.resources to locate the icon
            try:
                logging.info("Locating icon using package resources...")
                
                # Try to get the icon path, with fallbacks for different Python versions
                try:
                    # Modern approach (Python 3.9+)
                    if hasattr(pkg_resources, 'files'):
                        resources = pkg_resources.files('letterhead_pdf.resources')
                        icns_file = resources.joinpath('Mac-letterhead.icns')
                        custom_icon_path = str(icns_file)
                        logging.info(f"Found icon using modern importlib.resources: {custom_icon_path}")
                    else:
                        # Legacy approach (Python 3.7-3.8)
                        with pkg_resources.path('letterhead_pdf.resources', 'Mac-letterhead.icns') as p:
                            custom_icon_path = str(p)
                            logging.info(f"Found icon using legacy importlib.resources: {custom_icon_path}")
                except (ImportError, ModuleNotFoundError, FileNotFoundError) as e:
                    logging.warning(f"Could not find icon using importlib.resources: {str(e)}")
                    
                    # Direct path fallback - last resort for development environments
                    custom_icon_path = os.path.join(os.path.dirname(__file__), "resources", "Mac-letterhead.icns")
                    logging.info(f"Falling back to direct path: {custom_icon_path}")
                    
                if custom_icon_path and os.path.exists(custom_icon_path):
                    # Copy icon to app resources
                    app_icon = os.path.join(app_resources_dir, "applet.icns")
                    shutil.copy2(custom_icon_path, app_icon)
                    logging.info(f"Set custom icon: {app_icon}")
                    
                    # Also set document icon if it exists
                    document_icon = os.path.join(app_resources_dir, "droplet.icns")
                    if os.path.exists(document_icon):
                        shutil.copy2(custom_icon_path, document_icon)
                        logging.info(f"Set document icon: {document_icon}")
                    
                    # Use more direct macOS-specific approaches to set the icon
                    try:
                        from subprocess import run, PIPE
                        import tempfile
                        
                        logging.info(f"Setting custom icon using macOS specific methods")
                        
                        # Create a temporary AppleScript to set the icon
                        icon_script = f'''
                        tell application "Finder"
                            set file_path to POSIX file "{app_path}" as alias
                            set icon_path to POSIX file "{custom_icon_path}" as alias
                            set icon of file_path to icon of icon_path
                        end tell
                        '''
                        
                        # Write the script to a temporary file
                        fd, script_path = tempfile.mkstemp(suffix='.scpt')
                        try:
                            with os.fdopen(fd, 'w') as f:
                                f.write(icon_script)
                            
                            # Execute the AppleScript
                            run(["osascript", script_path], check=False)
                            logging.info("Set icon using AppleScript")
                        finally:
                            # Clean up the temporary file
                            os.unlink(script_path)
                        
                        # Also try the fileicon tool if available
                        fileicon_result = run(["which", "fileicon"], capture_output=True, text=True, check=False)
                        if fileicon_result.returncode == 0 and fileicon_result.stdout.strip():
                            fileicon_path = fileicon_result.stdout.strip()
                            run([fileicon_path, "set", app_path, custom_icon_path], check=False)
                            logging.info("Set icon using fileicon tool")
                        
                        # Alternative direct method for macOS
                        try:
                            import Cocoa
                            workspace = Cocoa.NSWorkspace.sharedWorkspace()
                            workspace.setIcon_forFile_options_(
                                Cocoa.NSImage.alloc().initWithContentsOfFile_(custom_icon_path),
                                app_path, 
                                0
                            )
                            logging.info("Set icon using NSWorkspace")
                        except Exception as cocoa_err:
                            logging.warning(f"Could not set icon using NSWorkspace: {cocoa_err}")
                        
                        logging.info("Tried multiple methods to set the icon")
                    except Exception as e:
                        logging.warning(f"Could not set icon: {e}")
                else:
                    logging.info(f"Custom icon not found after all attempts, using default AppleScript icon")
                        
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
