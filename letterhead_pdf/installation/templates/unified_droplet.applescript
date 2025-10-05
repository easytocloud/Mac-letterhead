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
                    -- Use shell commands instead of System Events to avoid permission requirements
                    set dev_mode_posix to POSIX path of dev_mode_path
                    set is_dev_mode to (do shell script "test -f " & quoted form of dev_mode_posix & " && echo 'true' || echo 'false'") is "true"
                    if is_dev_mode then
                        -- Read the python path from the dev_mode file
                        set python_path to do shell script "cat " & quoted form of dev_mode_posix & " | tr -d '\\n'"
                    end if
                end try
                
                -- Check for custom CSS file in app bundle
                set css_path to app_path & "Contents:Resources:style.css"
                set css_exists to false
                set css_posix to ""
                try
                    -- Use shell command instead of System Events to avoid permission requirements
                    set css_posix_check to POSIX path of css_path
                    set css_exists to (do shell script "test -f " & quoted form of css_posix_check & " && echo 'true' || echo 'false'") is "true"

                    -- If CSS file exists, convert path
                    if css_exists then
                        try
                            set css_posix_source to POSIX path of css_path
                            
                            -- Debug: log the path conversion
                            do shell script "echo " & quoted form of ("CSS Path Debug: HFS=" & css_path & ", POSIX=" & css_posix_source) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                            
                            -- For production mode, copy CSS to temp location to avoid sandboxing issues
                            if not is_dev_mode then
                                -- Create temp CSS file that uvx can access
                                set temp_css_path to "/tmp/mac-letterhead-" & (random number from 10000 to 99999) & ".css"
                                do shell script "cp " & quoted form of css_posix_source & " " & quoted form of temp_css_path
                                set css_posix to temp_css_path
                            else
                                set css_posix to css_posix_source
                            end if
                        on error path_error
                            do shell script "echo " & quoted form of ("CSS Path Conversion Error: " & path_error) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                        end try
                    end if
                end try
                
                -- Get file info using shell commands instead of System Events
                set file_name to do shell script "basename " & quoted form of posix_path
                set file_extension to do shell script "echo " & quoted form of file_name & " | sed 's/.*\\.//'"
                
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
                
                -- Debug: Log the final command for troubleshooting
                do shell script "echo " & quoted form of ("AppleScript Debug: CSS exists=" & (css_exists as string) & ", CSS path=" & css_posix & ", Final command: " & cmd) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                
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
    -- Check if this is development mode using shell command instead of System Events
    set app_path to path to me as string
    set dev_mode_path to app_path & "Contents:Resources:dev_mode"
    set mode_text to "Production"
    try
        set dev_mode_posix to POSIX path of dev_mode_path
        if (do shell script "test -f " & quoted form of dev_mode_posix & " && echo 'true' || echo 'false'") is "true" then
            set mode_text to "Development"
        end if
    end try
    
    -- Show dialog with two buttons
    set dialog_result to display dialog "Mac-letterhead Droplet v{{VERSION}}" & return & "Mode: " & mode_text & return & return & "Drag and drop PDF or Markdown files to apply letterhead." buttons {"Show Letterhead", "OK"} default button "OK" with icon note
    
    -- Handle button response
    if button returned of dialog_result is "Show Letterhead" then
        -- Get letterhead path from app bundle
        set letterhead_path to app_path & "Contents:Resources:letterhead.pdf"
        
        -- Check if letterhead exists and open it using shell command instead of System Events
        try
            set letterhead_posix to POSIX path of letterhead_path
            set letterhead_exists to (do shell script "test -f " & quoted form of letterhead_posix & " && echo 'true' || echo 'false'") is "true"

            if letterhead_exists then
                do shell script "open " & quoted form of letterhead_posix
            else
                -- Critical error - app bundle is corrupted
                display alert "Missing Letterhead File" message "The letterhead file is missing from the app bundle. This droplet may be corrupted and should be reinstalled." as critical
            end if
        on error error_message
            display alert "Error Opening Letterhead" message "Could not open letterhead file: " & error_message as critical
        end try
    end if
end run
