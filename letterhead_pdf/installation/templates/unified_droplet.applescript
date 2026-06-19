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
                    -- Production mode: use the resolved uvx binary. Pinned droplets always
                    -- run the version they were built with; unpinned droplets run whatever
                    -- uvx considers current (auto-update at the cost of reproducibility).
                    if {{PINNED}} then
                        set pkg_spec to "mac-letterhead@{{VERSION}}"
                    else
                        set pkg_spec to "mac-letterhead"
                    end if
                    if file_extension is "pdf" then
                        set cmd to quoted form of uvx_bin & " " & pkg_spec & " merge " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
                    else
                        set cmd to quoted form of uvx_bin & " " & pkg_spec & " merge-md " & quoted form of letterhead_posix & " " & quoted form of file_name & " " & quoted form of file_dir & " " & quoted form of posix_path
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

    -- About-dialog: bold title from the droplet name+version, short plain-language
    -- message body, mode line only when not Production. Using `display alert` so the
    -- droplet's bundled Mac-letterhead.icns is used as the dialog icon (rather than
    -- AppleScript's default generic note icon).
    if is_dev_mode then
        set dialog_title to "Mac-letterhead Droplet v{{VERSION}}"
        set dialog_buttons to {"Show Letterhead", "OK"}
        set dialog_body to "Mode: Development" & return & return & "Drop PDF or Markdown files onto the droplet to apply your letterhead."
    else if {{PINNED}} then
        set dialog_title to "Mac-letterhead Droplet v{{VERSION}}"
        set dialog_buttons to {"Show Letterhead", "OK"}
        set dialog_body to "Drop PDF or Markdown files onto the droplet to apply your letterhead."
    else
        set dialog_buttons to {"Show Letterhead", "Refresh", "OK"}
        -- Probe live version via uvx. Strict regex against `mac-letterhead X.Y.Z[...]`
        -- so any other stdout noise (e.g. WeasyPrint diagnostics on macOS 27 beta when
        -- pango/cairo aren't installed) cannot leak into the title.
        set live_version to "unknown"
        try
            set uvx_probe to do shell script "PATH=\"$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH\" command -v uvx 2>/dev/null || true"
            if uvx_probe is not "" then
                set live_version to do shell script quoted form of uvx_probe & " mac-letterhead --version 2>/dev/null | /usr/bin/sed -nE 's/^mac-letterhead ([0-9][0-9.a-z-]*).*/\\1/p' | head -1"
                if live_version is "" then set live_version to "unknown"
            end if
        end try
        set dialog_title to "Mac-letterhead Droplet v" & live_version & " (unpinned)"
        set dialog_body to "Drop PDF or Markdown files onto the droplet to apply your letterhead." & return & return & "Updates arrive automatically on every drop. Click Refresh to update right now."
    end if

    set dialog_result to display alert dialog_title message dialog_body buttons dialog_buttons default button "OK"

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
    else if chosen_button is "Refresh" then
        my refresh_unpinned()
    end if
end run

-- Unpinned-droplet refresh: re-resolves uv's tool env so the next drop runs the
-- newest published mac-letterhead. The .app on disk is not modified — no TCC dance.
on refresh_unpinned()
    set uvx_bin to my resolve_uvx()
    if uvx_bin is "" then
        display alert "uvx not found" message "Mac-letterhead requires uv/uvx. Install with:" & return & return & "curl -LsSf https://astral.sh/uv/install.sh | sh" as critical
        return
    end if
    -- Same strict regex as the dialog probe: only accept the canonical "mac-letterhead X.Y.Z" line.
    set before_version to ""
    try
        set before_version to do shell script quoted form of uvx_bin & " mac-letterhead --version 2>/dev/null | /usr/bin/sed -nE 's/^mac-letterhead ([0-9][0-9.a-z-]*).*/\\1/p' | head -1"
    end try
    try
        set after_version to do shell script quoted form of uvx_bin & " --refresh mac-letterhead --version 2>/dev/null | /usr/bin/sed -nE 's/^mac-letterhead ([0-9][0-9.a-z-]*).*/\\1/p' | head -1"
    on error refresh_error
        display alert "Refresh failed" message "Could not refresh mac-letterhead:" & return & return & refresh_error as critical
        return
    end try
    if after_version is "" then
        display alert "Refresh failed" message "uvx did not return a version after refresh." as critical
        return
    end if
    if before_version is after_version then
        display dialog "You're up to date." & return & return & "Mac-letterhead v" & after_version & " is the latest published version." buttons {"OK"} default button "OK" with icon note
    else
        display dialog "Refreshed." & return & return & "Was: v" & before_version & return & "Now: v" & after_version & return & return & "Next drop will use the new version." buttons {"OK"} default button "OK" with icon note
    end if
end refresh_unpinned

-- Resolve the uvx binary by probing the install locations uv supports. Returns "" if missing.
on resolve_uvx()
    try
        return do shell script "PATH=\"$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH\" command -v uvx 2>/dev/null || true"
    on error
        return ""
    end try
end resolve_uvx

-- Self-update was previously implemented here, but macOS 26+ App Management
-- restrictions prevent a droplet from rewriting its own .app bundle on Desktop
-- (every approach we tried — backgrounded helper, synchronous `do shell script`,
-- nohup, double-fork — hit "Operation not permitted" on `rm -rf` of the bundle).
-- Pinned droplets are now updated by re-running `mac-letterhead install` from
-- Terminal; unpinned droplets auto-update via uvx on every drop. The Refresh
-- button (unpinned only) pokes uv's cache without touching the .app.
