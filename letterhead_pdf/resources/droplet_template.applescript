-- Letterhead Applier AppleScript Droplet
-- This script takes dropped PDF and Markdown files and applies a letterhead template
-- Enhanced for macOS Tahoe beta security requirements

on open these_items
    -- Create log directory first
    try
        do shell script "mkdir -p " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead")
    end try
    
    -- Debug: Log that we received items
    do shell script "echo " & quoted form of ("Droplet received " & (count of these_items) & " items") & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
    
    -- First, check if we have any items
    if (count of these_items) is 0 then
        display dialog "No files were dropped. Please drag PDF or Markdown files onto this application." buttons {"OK"} default button "OK" with icon note
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
                    display dialog "File no longer exists or cannot be accessed: " & (this_item as string) buttons {"OK"} default button "OK" with icon caution
                    return
                end if
                
                set file_info to info for this_item
                set file_name to name of file_info
                set file_extension to name extension of file_info
            end tell
            
            -- Check if it's a supported file type (case insensitive)
            set file_extension_lower to my toLower(file_extension)
            if file_extension_lower is not in {"pdf", "md", "markdown"} then
                display dialog "Unsupported file type: " & file_extension & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md, .markdown)" buttons {"OK"} default button "OK" with icon stop
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
                    display dialog "Letterhead template not found. Please reinstall the letterhead applier." buttons {"OK"} default button "OK" with icon stop
                    return
                end if
            end tell
            
            -- Get file basename without extension
            set file_basename to my getBasename(file_name, file_extension)
            
            -- Get the directory of the source file for default save location
            set source_dir to my getDirname(input_file)
            
            -- Debug: Log key variables
            do shell script "echo " & quoted form of ("File name: " & file_name) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            do shell script "echo " & quoted form of ("File basename: " & file_basename) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            do shell script "echo " & quoted form of ("Source dir: " & source_dir) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            do shell script "echo " & quoted form of ("Input file: " & input_file) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            
            -- Get the application name for postfix
            set app_name_full to my getBasenameFromPath(app_path)
            -- Remove .app extension using AppleScript
            if app_name_full ends with ".app" then
                set app_name to text 1 thru -5 of app_name_full
            else
                set app_name to app_name_full
            end if
            
            -- Build the command using the simplest possible approach
            if file_extension_lower is in {"md", "markdown"} then
                set full_cmd to "cd " & quoted form of source_dir & " && uvx mac-letterhead@{{VERSION}} merge-md " & quoted form of letterhead_path & " " & quoted form of file_basename & " " & quoted form of source_dir & " " & quoted form of input_file & " --strategy darken --output-postfix " & quoted form of app_name
            else
                set full_cmd to "cd " & quoted form of source_dir & " && uvx mac-letterhead@{{VERSION}} merge " & quoted form of letterhead_path & " " & quoted form of file_basename & " " & quoted form of source_dir & " " & quoted form of input_file & " --strategy darken --output-postfix " & quoted form of app_name
            end if
            
            -- Execute the command with enhanced error handling
            try
                -- Log the command for debugging
                do shell script "echo " & quoted form of ("Processing: " & file_name) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                do shell script "echo " & quoted form of ("Command: " & full_cmd) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                -- Execute the main command
                set result_output to do shell script full_cmd
                
                -- Log success
                do shell script "echo " & quoted form of ("Success: " & file_name) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                -- Show success notification (brief)
                display notification "Successfully processed " & file_name with title "Letterhead Applied"
                
            on error execErr
                -- Enhanced error handling with user-friendly messages
                set error_msg to "Error processing " & file_name & ":" & return & return
                
                if execErr contains "Markdown module not available" then
                    set error_msg to error_msg & "Markdown processing is not available. This may be due to missing dependencies." & return & return & "Solutions:" & return & "1. Try processing a PDF file instead" & return & "2. Contact support for assistance with Markdown files"
                else if execErr contains "uvx" then
                    set error_msg to error_msg & "Could not run mac-letterhead. Please ensure it's properly installed." & return & return & "Try running this in Terminal:" & return & "uvx mac-letterhead@{{VERSION}} --version"
                else
                    set error_msg to error_msg & execErr
                end if
                
                -- Log the error
                do shell script "echo " & quoted form of ("Error: " & execErr) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                display dialog error_msg buttons {"OK"} default button "OK" with icon stop
            end try
            
        on error errMsg
            -- Top-level error handling
            do shell script "echo " & quoted form of ("Top-level error: " & errMsg) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            display dialog "Error processing file: " & errMsg buttons {"OK"} default button "OK" with icon stop
        end try
    end repeat
end open

on run
    display dialog "Letterhead Applier v{{VERSION}}" & return & return & "To apply a letterhead to a document:" & return & "1. Drag and drop a PDF or Markdown (.md) file onto this application icon" & return & "2. The letterhead will be applied automatically" & return & "3. You'll be prompted to save the merged document" & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md, .markdown) - converted to PDF with proper margins" & return & return & "Note: On macOS Tahoe beta, you may need to approve file access the first time." buttons {"OK"} default button "OK"
end run

-- Helper function to convert text to lowercase (pure AppleScript)
on toLower(str)
    set lowerStr to ""
    repeat with i from 1 to length of str
        set char to character i of str
        if char is in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" then
            set pos to (ASCII number char) - (ASCII number "A") + (ASCII number "a")
            set lowerStr to lowerStr & (ASCII character pos)
        else
            set lowerStr to lowerStr & char
        end if
    end repeat
    return lowerStr
end toLower

-- Helper function to get app bundle path (pure AppleScript)
on getAppBundle(app_path)
    -- Find the position of "/Contents" and remove everything after it
    set contentsPos to 0
    set pathLength to length of app_path
    if pathLength > 8 then
        set i to 1
        repeat while i <= (pathLength - 8)
            if text i thru (i + 8) of app_path is "/Contents" then
                set contentsPos to i
                exit repeat
            end if
            set i to i + 1
        end repeat
    end if
    
    if contentsPos > 0 then
        return text 1 thru (contentsPos - 1) of app_path
    else
        return app_path
    end if
end getAppBundle

-- Helper function to get dirname (pure AppleScript)
on getDirname(file_path)
    -- Find the last slash and return everything before it
    set lastSlashPos to 0
    set i to length of file_path
    
    repeat while i > 0
        if character i of file_path is "/" then
            set lastSlashPos to i
            exit repeat
        end if
        set i to i - 1
    end repeat
    
    if lastSlashPos > 1 then
        return text 1 thru (lastSlashPos - 1) of file_path
    else
        return "/"
    end if
end getDirname

-- Helper function to get basename from path (pure AppleScript)
on getBasenameFromPath(file_path)
    -- Find the last slash and return everything after it
    set lastSlashPos to 0
    set i to length of file_path
    
    repeat while i > 0
        if character i of file_path is "/" then
            set lastSlashPos to i
            exit repeat
        end if
        set i to i - 1
    end repeat
    
    if lastSlashPos > 0 and lastSlashPos < length of file_path then
        return text (lastSlashPos + 1) thru -1 of file_path
    else
        return file_path
    end if
end getBasenameFromPath

-- Helper function to get basename without extension
on getBasename(file_name, file_extension)
    if file_extension is "" then
        return file_name
    else
        set ext_length to (length of file_extension) + 1
        set name_length to length of file_name
        if ext_length < name_length then
            return text 1 thru -(ext_length) of file_name
        else
            return file_name
        end if
    end if
end getBasename
