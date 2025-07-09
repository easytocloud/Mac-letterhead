-- Mac-letterhead Development Droplet
-- This droplet uses the local development environment
-- Version: {{VERSION}}

on open dropped_items
    repeat with item_path in dropped_items
        set item_path to item_path as string
        if item_path ends with ".pdf" or item_path ends with ".md" or item_path ends with ".markdown" then
            try
                -- Convert file path to POSIX path
                set posix_path to POSIX path of item_path
                
                -- Set letterhead path (passed as parameter)
                set letterhead_posix to "{{LETTERHEAD_PATH}}"
                
                -- Get file info
                tell application "System Events"
                    set file_name to name of disk item item_path
                    set file_extension to name extension of disk item item_path
                end tell
                
                -- Get directory of the file
                set file_dir to do shell script "dirname " & quoted form of posix_path
                
                -- Determine command based on file type
                if file_extension is "pdf" then
                    set cmd to python_path & " -m letterhead_pdf.main merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                else
                    set cmd to python_path & " -m letterhead_pdf.main merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                end if
                
                -- Execute command
                do shell script cmd
                
                display notification "Letterhead applied successfully (dev mode)" with title "Mac-letterhead Development"
                
            on error error_message
                display alert "Error processing file" message error_message as critical
            end try
        else
            display alert "Unsupported file type" message "Please drop PDF or Markdown files only." as warning
        end if
    end repeat
end open

on run
    display dialog "Mac-letterhead Development Droplet v{{VERSION}}" & return & return & "Drag and drop PDF or Markdown files to apply letterhead." & return & return & "This is a DEVELOPMENT version using local code." buttons {"OK"} default button "OK" with icon note
end run
