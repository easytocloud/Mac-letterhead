-- Letterhead Applier AppleScript Droplet
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
                
                -- Get the application path
                set app_path to POSIX path of (path to me)
                set app_container to do shell script "dirname " & quoted form of app_path
                
                -- Path to letterhead in the Contents/Resources folder of the app bundle
                set letterhead_path to app_container & "/Contents/Resources/letterhead.pdf"
                
                -- For better UX, use the filename for the output
                set quoted_input_pdf to quoted form of input_pdf
                set file_basename to do shell script "basename " & quoted_input_pdf & " .pdf"
                
                -- Display progress dialog
                display dialog "Applying letterhead to " & file_basename & ".pdf..." buttons {} giving up after 1
                
                -- Run the command with error handling
                try
                    -- Pass explicit HOME to ensure environment is correct
                    set home_path to POSIX path of (path to home folder)
                    
                    -- Create logs directory
                    do shell script "mkdir -p " & quoted form of home_path & "/Library/Logs/Mac-letterhead"
                    
                    -- Build the command
                    set cmd to "export HOME=" & quoted form of home_path & " && cd " & quoted form of home_path
                    set cmd to cmd & " && /usr/bin/env PATH=$HOME/.local/bin:$HOME/Library/Python/*/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin uvx mac-letterhead print "
                    set cmd to cmd & quoted form of letterhead_path & " " & quoted form of file_basename & " \"\" " & quoted_input_pdf & " --strategy darken"
                    
                    -- Log the full command and paths for diagnostics
                    do shell script "echo 'Letterhead path: " & letterhead_path & "' > " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'App container: " & app_container & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Input PDF: " & input_pdf & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Command: " & cmd & "' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "echo 'Checking letterhead exists: ' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    do shell script "ls -la " & quoted form of letterhead_path & " >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log 2>&1 || echo 'FILE NOT FOUND' >> " & quoted form of home_path & "/Library/Logs/Mac-letterhead/applescript.log"
                    
                    -- Execute the command
                    do shell script cmd
                    
                    -- Success message
                    display dialog "Letterhead applied successfully to " & file_basename & ".pdf!" buttons {"OK"} default button "OK"
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
