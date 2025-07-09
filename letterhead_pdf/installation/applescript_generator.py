"""
AppleScriptGenerator - Generates AppleScript from templates.

This class handles the generation of AppleScript code for droplets:
- Template loading and processing
- Variable substitution
- Development vs production script generation
"""

import os
import logging
from typing import Optional

from letterhead_pdf import __version__
from letterhead_pdf.exceptions import InstallerError


class AppleScriptGenerator:
    """Generates AppleScript code for droplets."""
    
    def __init__(self, development_mode: bool = False):
        """
        Initialize the AppleScriptGenerator.
        
        Args:
            development_mode: If True, generate development script
        """
        self.development_mode = development_mode
        self.logger = logging.getLogger(__name__)
    
    def generate_script(self, letterhead_path: str, python_path: str = None) -> str:
        """
        Generate AppleScript content for the droplet using unified template.
        
        Args:
            letterhead_path: Path to the letterhead PDF file
            python_path: Path to Python interpreter (for development mode)
            
        Returns:
            str: Generated AppleScript content
            
        Raises:
            InstallerError: If script generation fails
        """
        self.logger.info(f"Generating unified AppleScript (dev_mode={self.development_mode})")
        
        try:
            return self._generate_unified_script(letterhead_path, python_path)
                
        except Exception as e:
            error_msg = f"Failed to generate AppleScript: {str(e)}"
            self.logger.error(error_msg)
            raise InstallerError(error_msg) from e
    
    def _generate_unified_script(self, letterhead_path: str, python_path: str = None) -> str:
        """Generate unified AppleScript that handles both development and production modes."""
        template_path = self._get_template_path("unified_droplet.applescript")
        
        if not os.path.exists(template_path):
            # Fall back to legacy methods if unified template doesn't exist
            if self.development_mode:
                return self._generate_development_script(letterhead_path, python_path)
            else:
                return self._generate_production_script(letterhead_path)
        
        template_content = self._load_template(template_path)
        
        # Substitute variables
        script_content = template_content.replace("{{VERSION}}", __version__)
        
        return script_content
    
    def _generate_development_script(self, letterhead_path: str, python_path: str) -> str:
        """Generate development AppleScript that uses local Python environment."""
        template_path = self._get_template_path("development_droplet.applescript")
        
        if not os.path.exists(template_path):
            # Fall back to existing local template
            template_path = self._get_fallback_template_path("droplet_template_local.applescript")
        
        template_content = self._load_template(template_path)
        
        # Substitute variables
        script_content = template_content.replace("{{PYTHON}}", python_path or "python3")
        script_content = script_content.replace("{{LETTERHEAD_PATH}}", os.path.abspath(letterhead_path))
        script_content = script_content.replace("{{VERSION}}", __version__)
        
        return script_content
    
    def _generate_production_script(self, letterhead_path: str) -> str:
        """Generate production AppleScript that uses uvx."""
        template_path = self._get_template_path("production_droplet.applescript")
        
        if not os.path.exists(template_path):
            # Fall back to existing template
            template_path = self._get_fallback_template_path("droplet_template.applescript")
        
        template_content = self._load_template(template_path)
        
        # Substitute variables
        script_content = template_content.replace("{{VERSION}}", __version__)
        script_content = script_content.replace("{{LETTERHEAD_PATH}}", os.path.abspath(letterhead_path))
        
        return script_content
    
    def _get_template_path(self, template_name: str) -> str:
        """Get path to a template file in the installation templates directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(current_dir, "templates")
        return os.path.join(templates_dir, template_name)
    
    def _get_fallback_template_path(self, template_name: str) -> str:
        """Get path to a template file in the legacy resources directory."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        package_dir = os.path.dirname(current_dir)  # letterhead_pdf/
        resources_dir = os.path.join(package_dir, "resources")
        return os.path.join(resources_dir, template_name)
    
    def _load_template(self, template_path: str) -> str:
        """Load template content from file."""
        if not os.path.exists(template_path):
            raise InstallerError(f"AppleScript template not found: {template_path}")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Loaded template: {template_path}")
            return content
            
        except Exception as e:
            raise InstallerError(f"Failed to load template {template_path}: {str(e)}")
    
    def create_template_files(self) -> None:
        """Create default template files if they don't exist."""
        templates_dir = os.path.dirname(self._get_template_path(""))
        os.makedirs(templates_dir, exist_ok=True)
        
        # Create development template if it doesn't exist
        dev_template_path = self._get_template_path("development_droplet.applescript")
        if not os.path.exists(dev_template_path):
            self._create_development_template(dev_template_path)
        
        # Create production template if it doesn't exist
        prod_template_path = self._get_template_path("production_droplet.applescript")
        if not os.path.exists(prod_template_path):
            self._create_production_template(prod_template_path)
    
    def _create_development_template(self, template_path: str) -> None:
        """Create a development template file."""
        content = '''-- Mac-letterhead Development Droplet
-- This droplet uses the local development environment
-- Version: {{VERSION}}

on open dropped_items
    repeat with item_path in dropped_items
        set item_path to item_path as string
        if item_path ends with ".pdf" or item_path ends with ".md" or item_path ends with ".markdown" then
            try
                -- Convert file path to POSIX path
                set posix_path to POSIX path of item_path
                
                -- Get file info
                tell application "System Events"
                    set file_name to name of disk item item_path
                    set file_extension to name extension of disk item item_path
                end tell
                
                -- Determine command based on file type
                if file_extension is "pdf" then
                    set cmd to "{{PYTHON}} -m letterhead_pdf.main merge \\"{{LETTERHEAD_PATH}}\\" \\"" & file_name & "\\" ~/Desktop \\"" & posix_path & "\\""
                else
                    set cmd to "{{PYTHON}} -m letterhead_pdf.main merge-md \\"{{LETTERHEAD_PATH}}\\" \\"" & file_name & "\\" ~/Desktop \\"" & posix_path & "\\""
                end if
                
                -- Execute command
                do shell script cmd
                
                display notification "Letterhead applied successfully" with title "Mac-letterhead Development"
                
            on error error_message
                display alert "Error processing file" message error_message as critical
            end try
        else
            display alert "Unsupported file type" message "Please drop PDF or Markdown files only." as warning
        end if
    end repeat
end open

on run
    display dialog "Mac-letterhead Development Droplet v{{VERSION}}\\n\\nDrag and drop PDF or Markdown files to apply letterhead.\\n\\nThis is a DEVELOPMENT version using local code." buttons {"OK"} default button "OK" with icon note
end run
'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Created development template: {template_path}")
    
    def _create_production_template(self, template_path: str) -> None:
        """Create a production template file."""
        content = '''-- Mac-letterhead Production Droplet
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
                
                -- Get CSS path from app bundle
                set css_path to app_path & "Contents:Resources:style.css"
                set css_posix to POSIX path of css_path
                
                -- Get file info
                tell application "System Events"
                    set file_name to name of disk item item_path
                    set file_extension to name extension of disk item item_path
                end tell
                
                -- Determine command based on file type
                if file_extension is "pdf" then
                    set cmd to "uvx mac-letterhead@{{VERSION}} merge \\"" & letterhead_posix & "\\" \\"" & file_name & "\\" ~/Desktop \\"" & posix_path & "\\""
                else
                    -- For Markdown files, include CSS parameter
                    set cmd to "uvx mac-letterhead@{{VERSION}} merge-md \\"" & letterhead_posix & "\\" \\"" & file_name & "\\" ~/Desktop \\"" & posix_path & "\\" --css \\"" & css_posix & "\\""
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
    display dialog "Mac-letterhead Droplet v{{VERSION}}\\n\\nDrag and drop PDF or Markdown files to apply letterhead." buttons {"OK"} default button "OK" with icon note
end run
'''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"Created production template: {template_path}")
