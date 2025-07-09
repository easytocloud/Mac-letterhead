-- Mac-letterhead Unified Droplet
-- Version: {{VERSION}}

on open dropped_items
    repeat with item_path in dropped_items
        set item_path to item_path as string
        if item_path ends with ".pdf" or item_path ends with ".md" or item_path ends with ".markdown" then
            try
                -- Convert file path to POSIX path
                set posix_path to POSIX path of item_path
                
                -- Get letterhead path from app bundle
                set app_path to path to me as string
                set letterhead_path to app_path & "Contents:Resources:letterhead.pdf"
                set letterhead_posix to POSIX path of letterhead_path
                
                -- Check for development mode marker file
                set dev_mode_path to app_path & "Contents:Resources:dev_mode"
                set is_dev_mode to false
                set python_path to ""
                try
                    tell application "System Events"
                        if exists file dev_mode_path then
                            set is_dev_mode to true
                            -- Read the python path from the dev_mode file
                            set python_path to read file dev_mode_path as string
                            -- Remove any trailing newlines
                            set python_path to do shell script "echo " & quoted form of python_path & " | tr -d '\\n'"
                        end if
                    end tell
                end try
                
                -- Check for custom CSS file in app bundle
                set css_path to app_path & "Contents:Resources:style.css"
                set css_exists to false
                set css_posix to ""
                try
                    tell application "System Events"
                        if exists file css_path then
                            set css_exists to true
                            set css_posix to POSIX path of css_path
                        end if
                    end tell
                end try
                
                -- Get file info
                tell application "System Events"
                    set file_name to name of disk item item_path
                    set file_extension to name extension of disk item item_path
                end tell
                
                -- Get directory of the file
                set file_dir to do shell script "dirname " & quoted form of posix_path
                
                -- Build command based on mode and file type
                if is_dev_mode then
                    -- Development mode: use local python
                    if file_extension is "pdf" then
                        set cmd to quoted form of python_path & " -m letterhead_pdf merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                    else
                        set cmd to quoted form of python_path & " -m letterhead_pdf merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                        -- Add CSS parameter for Markdown processing if CSS file exists
                        if css_exists then
                            set cmd to cmd & " --css " & quoted form of css_posix
                        end if
                    end if
                else
                    -- Production mode: use uvx
                    if file_extension is "pdf" then
                        set cmd to "/usr/local/bin/uvx mac-letterhead@{{VERSION}} merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                    else
                        set cmd to "/usr/local/bin/uvx mac-letterhead@{{VERSION}} merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                        -- Add CSS parameter for Markdown processing if CSS file exists
                        if css_exists then
                            set cmd to cmd & " --css " & quoted form of css_posix
                        end if
                    end if
                end if
                
                -- Execute command
                do shell script cmd
                
                display notification "Letterhead applied successfully" with title "Mac-letterhead"
                
            on error error_message
                display alert "Error processing file" message error_message as critical
            end try
        else
            display alert "Unsupported file type" message "Please drop PDF or Markdown files only." as warning
        end if
    end repeat
end open

on run
    -- Check if this is development mode
    set app_path to path to me as string
    set dev_mode_path to app_path & "Contents:Resources:dev_mode"
    set mode_text to "Production"
    try
        tell application "System Events"
            if exists file dev_mode_path then
                set mode_text to "Development"
            end if
        end tell
    end try
    
    display dialog "Mac-letterhead Droplet v{{VERSION}}" & return & "Mode: " & mode_text & return & return & "Drag and drop PDF or Markdown files to apply letterhead." buttons {"OK"} default button "OK" with icon note
end run
