-- Mac-letterhead Production Droplet
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
                
                -- Get file info
                tell application "System Events"
                    set file_name to name of disk item item_path
                    set file_extension to name extension of disk item item_path
                end tell
                
                -- Get directory of the file
                set file_dir to do shell script "dirname " & quoted form of posix_path
                
                -- Determine command based on file type
                if file_extension is "pdf" then
                    set cmd to "DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH /usr/local/bin/uvx mac-letterhead@{{VERSION}} merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                else
                    set cmd to "DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH /usr/local/bin/uvx mac-letterhead@{{VERSION}} merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
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
    display dialog "Mac-letterhead Droplet v{{VERSION}}" & return & return & "Drag and drop PDF or Markdown files to apply letterhead." buttons {"OK"} default button "OK" with icon note
end run
