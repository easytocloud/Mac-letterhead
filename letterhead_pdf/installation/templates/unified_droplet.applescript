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

                -- Check for debug marker file (enables verbose logging to /tmp)
                set debug_log_path to app_path & "Contents:Resources:debug"
                set is_debug to false
                try
                    set debug_posix to POSIX path of debug_log_path
                    set is_debug to (do shell script "test -f " & quoted form of debug_posix & " && echo 'true' || echo 'false'") is "true"
                end try

                -- Resolve uvx path (production mode only) by probing common install locations.
                -- `do shell script` runs with a minimal PATH, so we must look explicitly in
                -- ~/.local/bin (uv's default since 2024), /opt/homebrew/bin (Apple Silicon),
                -- /usr/local/bin (Intel/legacy), and finally fall back to the login PATH.
                set uvx_bin to ""
                if not is_dev_mode then
                    try
                        set uvx_bin to do shell script "PATH=\"$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH\" command -v uvx 2>/dev/null || true"
                    end try
                    if uvx_bin is "" then
                        display alert "uvx not found" message "Mac-letterhead requires uv/uvx to run. Install it with:" & return & return & "curl -LsSf https://astral.sh/uv/install.sh | sh" & return & return & "Then re-open this droplet." as critical
                        return
                    end if
                end if

                -- Check for custom CSS file in app bundle
                set css_path to app_path & "Contents:Resources:style.css"
                set css_exists to false
                set css_posix to ""
                set temp_css_path to ""
                try
                    -- Use shell command instead of System Events to avoid permission requirements
                    set css_posix_check to POSIX path of css_path
                    set css_exists to (do shell script "test -f " & quoted form of css_posix_check & " && echo 'true' || echo 'false'") is "true"

                    -- If CSS file exists, convert path
                    if css_exists then
                        try
                            set css_posix_source to POSIX path of css_path

                            if is_debug then
                                do shell script "echo " & quoted form of ("CSS Path Debug: HFS=" & css_path & ", POSIX=" & css_posix_source) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                            end if

                            -- For production mode, copy CSS to temp location to avoid sandboxing issues.
                            -- Use mktemp so the path is unpredictable and not vulnerable to symlink attacks.
                            if not is_dev_mode then
                                set temp_css_path to do shell script "mktemp -t mac-letterhead.css"
                                do shell script "cp " & quoted form of css_posix_source & " " & quoted form of temp_css_path
                                set css_posix to temp_css_path
                            else
                                set css_posix to css_posix_source
                            end if
                        on error path_error
                            if is_debug then
                                do shell script "echo " & quoted form of ("CSS Path Conversion Error: " & path_error) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                            end if
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
                    -- Production mode: use the resolved uvx binary
                    if file_extension is "pdf" then
                        set cmd to quoted form of uvx_bin & " mac-letterhead@{{VERSION}} merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                    else
                        set cmd to quoted form of uvx_bin & " mac-letterhead@{{VERSION}} merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                        -- Add CSS parameter for Markdown processing if CSS file exists
                        if css_exists then
                            set cmd to cmd & " --css " & quoted form of css_posix
                        end if
                    end if
                end if

                if is_debug then
                    do shell script "echo " & quoted form of ("AppleScript Debug: CSS exists=" & (css_exists as string) & ", CSS path=" & css_posix & ", Final command: " & cmd) & " >> /tmp/mac-letterhead-applescript-debug.txt"
                end if

                -- Execute command
                try
                    do shell script cmd
                on error exec_error
                    -- Clean up temp CSS before propagating the error
                    if temp_css_path is not "" then
                        try
                            do shell script "rm -f " & quoted form of temp_css_path
                        end try
                    end if
                    error exec_error
                end try

                -- Clean up temp CSS file after successful run
                if temp_css_path is not "" then
                    try
                        do shell script "rm -f " & quoted form of temp_css_path
                    end try
                end if

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
    set is_dev_mode to false
    try
        set dev_mode_posix to POSIX path of dev_mode_path
        if (do shell script "test -f " & quoted form of dev_mode_posix & " && echo 'true' || echo 'false'") is "true" then
            set mode_text to "Development"
            set is_dev_mode to true
        end if
    end try

    -- Show dialog. Dev droplets get no "Check for Updates" button — they run from local code.
    if is_dev_mode then
        set dialog_buttons to {"Show Letterhead", "OK"}
    else
        set dialog_buttons to {"Show Letterhead", "Check for Updates", "OK"}
    end if
    set dialog_result to display dialog "Mac-letterhead Droplet v{{VERSION}}" & return & "Mode: " & mode_text & return & return & "Drag and drop PDF or Markdown files to apply letterhead." buttons dialog_buttons default button "OK" with icon note

    set chosen_button to button returned of dialog_result

    if chosen_button is "Show Letterhead" then
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
    else if chosen_button is "Check for Updates" then
        my check_for_updates(app_path)
    end if
end run

-- Resolve the uvx binary by probing the install locations uv supports. Returns "" if missing.
on resolve_uvx()
    try
        return do shell script "PATH=\"$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH\" command -v uvx 2>/dev/null || true"
    on error
        return ""
    end try
end resolve_uvx

-- In-place self-update. Compares the baked-in version to PyPI's latest, asks the user,
-- then re-runs `mac-letterhead install` with the same name + letterhead + CSS so the
-- droplet is rebuilt at the new version with all of its current resources preserved.
on check_for_updates(app_path)
    set uvx_bin to my resolve_uvx()
    if uvx_bin is "" then
        display alert "uvx not found" message "Mac-letterhead requires uv/uvx to check for updates. Install it with:" & return & return & "curl -LsSf https://astral.sh/uv/install.sh | sh" as critical
        return
    end if

    set current_version to "{{VERSION}}"
    set droplet_name to "{{NAME}}"
    if droplet_name is "" then
        display alert "Cannot self-update" message "This droplet was built without a name and cannot self-update. Re-run `mac-letterhead install --name <name>` to enable updates." as warning
        return
    end if

    -- Ask PyPI for the latest version. 15s timeout so a slow/missing network doesn't hang the dialog.
    set latest_version to ""
    try
        set latest_version to do shell script "/usr/bin/curl --max-time 15 -fsSL https://pypi.org/pypi/Mac-letterhead/json 2>/dev/null | /usr/bin/python3 -c 'import json,sys; print(json.load(sys.stdin)[\"info\"][\"version\"])' 2>/dev/null || true"
    end try

    if latest_version is "" then
        display alert "Update check failed" message "Could not reach PyPI to check for the latest version. Check your internet connection and try again." as warning
        return
    end if

    if latest_version is current_version then
        display dialog "You're up to date." & return & return & "Mac-letterhead v" & current_version buttons {"OK"} default button "OK" with icon note
        return
    end if

    set confirm to display dialog "A new version is available." & return & return & "Current: v" & current_version & return & "Latest:  v" & latest_version & return & return & "Update this droplet now? The droplet will close and re-open automatically." buttons {"Cancel", "Update"} default button "Update" with icon note
    if button returned of confirm is not "Update" then return

    -- Resolve letterhead + CSS paths inside the bundle so the rebuild preserves them.
    set letterhead_posix to POSIX path of (app_path & "Contents:Resources:letterhead.pdf")
    set css_posix to POSIX path of (app_path & "Contents:Resources:style.css")
    set css_exists to (do shell script "test -f " & quoted form of css_posix & " && echo 'true' || echo 'false'") is "true"

    -- Final destination = parent of the running .app
    set app_posix to POSIX path of app_path
    set final_dir to do shell script "dirname " & quoted form of app_posix
    -- Strip trailing slash that POSIX path of a folder leaves behind
    set app_posix_clean to do shell script "echo " & quoted form of app_posix & " | sed 's:/$::'"

    set log_path to "/tmp/mac-letterhead-update.log"
    set app_basename to do shell script "basename " & quoted form of app_posix_clean

    -- Stage the rebuild in a temp dir so we don't fight the running .app for the same path.
    -- The launcher then waits for the droplet's applet process to exit (we `quit` ourselves
    -- right after launching this), removes the old .app, moves the new one into place,
    -- and re-opens it.
    set stage_cmd to "set -e; STAGE=$(mktemp -d -t mac-letterhead-update); " & ¬
        quoted form of uvx_bin & " mac-letterhead@" & latest_version & " install" & ¬
        " --name " & quoted form of droplet_name & ¬
        " --letterhead " & quoted form of letterhead_posix & ¬
        " --output-dir \"$STAGE\""
    if css_exists then
        set stage_cmd to stage_cmd & " --css " & quoted form of css_posix
    end if
    -- After build: verify the new .app exists, wait up to 15s for the running droplet to exit
    -- (pgrep matches anything running from inside the bundle), swap the bundles, re-open.
    set stage_cmd to stage_cmd & "; NEW_APP=\"$STAGE/" & app_basename & "\"; " & ¬
        "if [ ! -d \"$NEW_APP\" ]; then echo \"build did not produce $NEW_APP\" >&2; exit 1; fi; " & ¬
        "for i in $(seq 1 30); do pgrep -f " & quoted form of (app_posix_clean & "/Contents/MacOS/") & " >/dev/null || break; sleep 0.5; done; " & ¬
        "rm -rf " & quoted form of app_posix_clean & "; " & ¬
        "mv \"$NEW_APP\" " & quoted form of app_posix_clean & "; " & ¬
        "rm -rf \"$STAGE\"; " & ¬
        "open " & quoted form of app_posix_clean

    try
        do shell script "nohup sh -c " & quoted form of (stage_cmd & " > " & quoted form of log_path & " 2>&1") & " >/dev/null 2>&1 &"
    on error rebuild_error
        display alert "Update failed" message "Could not start the update: " & rebuild_error & return & return & "See " & log_path & " for details." as critical
        return
    end try

    -- Quit so the running .app's bundle is free to be replaced. The launcher will re-open
    -- the new droplet automatically once we've exited.
    tell me to quit
end check_for_updates
