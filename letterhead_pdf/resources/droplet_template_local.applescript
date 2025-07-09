-- Local Development Letterhead Applier Droplet
-- Enhanced to handle both PDF and Markdown files

on open these_items
    -- Create log directory first
    try
        do shell script "mkdir -p " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead")
    end try
    
    -- Debug: Log that we received items
    do shell script "echo " & quoted form of ("Dev droplet received " & (count of these_items) & " items") & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
    
    -- First, check if we have any items
    if (count of these_items) is 0 then
        display dialog "No files were dropped. Please drag PDF or Markdown files onto this application." buttons {"OK"} default button "OK" with icon note
        return
    end if
    
    -- Process each dropped file
    repeat with i from 1 to count of these_items
        set this_item to item i of these_items
        
        try
            -- Get file info
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
            
            -- Get paths
            set input_file to POSIX path of this_item
            set letterhead_path to "{{LETTERHEAD_PATH}}"
            set python_path to "{{PYTHON}}"
            
            -- Get file basename without extension
            set file_basename to my getBasename(file_name, file_extension)
            
            -- Get the directory of the source file for default save location
            set source_dir to my getDirname(input_file)
            
            -- Debug: Log key variables
            do shell script "echo " & quoted form of ("Dev processing: " & file_name) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            do shell script "echo " & quoted form of ("File extension: " & file_extension_lower) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            
            -- Build the command based on file type
            if file_extension_lower is in {"md", "markdown"} then
                set cmd to "cd " & quoted form of source_dir & " && " & quoted form of python_path & " -m letterhead_pdf.main merge-md " & quoted form of letterhead_path & " " & quoted form of file_basename & " " & quoted form of source_dir & " " & quoted form of input_file & " --strategy darken --output-postfix " & quoted form of "dev"
            else
                set cmd to "cd " & quoted form of source_dir & " && " & quoted form of python_path & " -m letterhead_pdf.main merge " & quoted form of letterhead_path & " " & quoted form of file_basename & " " & quoted form of source_dir & " " & quoted form of input_file & " --strategy darken --output-postfix " & quoted form of "dev"
            end if
            
            -- Execute the command
            try
                -- Log the command for debugging
                do shell script "echo " & quoted form of ("Dev command: " & cmd) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                -- Execute the main command
                set result_output to do shell script cmd
                
                -- Log success
                do shell script "echo " & quoted form of ("Dev success: " & file_name) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                -- Show success notification
                display notification "Successfully processed " & file_name & " (dev mode)" with title "Letterhead Applied"
                
            on error execErr
                -- Enhanced error handling with user-friendly messages
                set error_msg to "Error processing " & file_name & " (dev mode):" & return & return
                
                if execErr contains "Markdown module not available" then
                    set error_msg to error_msg & "Markdown processing is not available. This may be due to missing dependencies." & return & return & "Solutions:" & return & "1. Try processing a PDF file instead" & return & "2. Install markdown dependencies: uv pip install markdown"
                else if execErr contains "Failed to read PDF metadata" then
                    set error_msg to error_msg & "The file appears to be corrupted or not a valid " & file_extension & " file."
                else
                    set error_msg to error_msg & execErr
                end if
                
                -- Log the error
                do shell script "echo " & quoted form of ("Dev error: " & execErr) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
                
                display dialog error_msg buttons {"OK"} default button "OK" with icon stop
            end try
            
        on error errMsg
            -- Top-level error handling
            do shell script "echo " & quoted form of ("Dev top-level error: " & errMsg) & " >> " & quoted form of (POSIX path of (path to home folder) & "Library/Logs/Mac-letterhead/droplet.log")
            display dialog "Error processing file (dev mode): " & errMsg buttons {"OK"} default button "OK" with icon stop
        end try
    end repeat
end open

on run
    display dialog "Development Letterhead Applier" & return & return & "This is a development version using local code." & return & return & "To apply a letterhead to a document:" & return & "1. Drag and drop a PDF or Markdown (.md) file onto this application icon" & return & "2. The letterhead will be applied automatically" & return & "3. You'll be prompted to save the merged document" & return & return & "Supported file types:" & return & "• PDF files (.pdf)" & return & "• Markdown files (.md, .markdown)" buttons {"OK"} default button "OK"
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
