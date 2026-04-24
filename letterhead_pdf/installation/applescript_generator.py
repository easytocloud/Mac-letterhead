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
    
