"""
DropletBuilder - Main orchestrator for droplet creation.

This class coordinates all aspects of droplet creation, providing a clean
interface for both production and development droplet creation.
"""

import os
import logging
import shutil
import tempfile
from typing import Optional

from letterhead_pdf import __version__
from letterhead_pdf.exceptions import InstallerError
from .resource_manager import ResourceManager
from .applescript_generator import AppleScriptGenerator
from .macos_integration import MacOSIntegration
from .validator import DropletValidator


class DropletBuilder:
    """Main orchestrator for creating Mac-letterhead droplets."""
    
    def __init__(self, development_mode: bool = False, python_path: str = None):
        """
        Initialize the DropletBuilder.
        
        Args:
            development_mode: If True, create a development droplet using local code
            python_path: Path to Python interpreter (for development mode)
        """
        self.development_mode = development_mode
        self.python_path = python_path or (os.sys.executable if development_mode else None)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.resource_manager = ResourceManager()
        self.applescript_generator = AppleScriptGenerator(development_mode)
        self.macos_integration = MacOSIntegration()
        self.validator = DropletValidator()
        
        self.logger.info(f"DropletBuilder initialized (dev_mode={development_mode})")
    
    def create_droplet(
        self,
        letterhead_path: str,
        app_name: str = "Letterhead Applier",
        output_dir: str = None,
        css_path: str = None
    ) -> str:
        """
        Create a droplet application.
        
        Args:
            letterhead_path: Path to the letterhead PDF file
            app_name: Name for the droplet application
            output_dir: Directory to save the droplet (defaults to Desktop)
            css_path: Path to custom CSS file for Markdown styling
            
        Returns:
            str: Path to the created droplet application
            
        Raises:
            InstallerError: If droplet creation fails
        """
        self.logger.info(f"Creating droplet: {app_name}")
        self.logger.info(f"Letterhead: {letterhead_path}")
        self.logger.info(f"Development mode: {self.development_mode}")
        
        try:
            # Validate inputs
            self._validate_inputs(letterhead_path, app_name, output_dir, css_path)
            
            # Determine output location
            output_dir = self._resolve_output_dir(output_dir)
            app_path = os.path.join(output_dir, f"{app_name}.app")
            
            # Remove existing app if it exists
            self._cleanup_existing_app(app_path)
            
            # Create droplet in temporary directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_app_path = os.path.join(temp_dir, f"{app_name}.app")
                
                # Step 1: Generate AppleScript
                applescript_content = self.applescript_generator.generate_script(
                    letterhead_path, self.python_path
                )
                
                # Step 2: Compile AppleScript to app bundle
                self.macos_integration.compile_applescript(
                    applescript_content, temp_app_path
                )
                
                # Step 3: Set up resources
                self.resource_manager.setup_app_resources(
                    temp_app_path, letterhead_path, css_path
                )
                
                # Step 4: Configure macOS integration
                self.macos_integration.configure_app_bundle(temp_app_path)
                
                # Step 5: Validate the droplet
                if not self.validator.validate_droplet(temp_app_path, letterhead_path):
                    raise InstallerError("Droplet validation failed")
                
                # Step 6: Move to final location
                shutil.move(temp_app_path, app_path)
            
            self.logger.info(f"Successfully created droplet: {app_path}")
            self._print_success_message(app_path, letterhead_path)
            
            return app_path
            
        except Exception as e:
            error_msg = f"Failed to create droplet: {str(e)}"
            self.logger.error(error_msg)
            raise InstallerError(error_msg) from e
    
    def _validate_inputs(self, letterhead_path: str, app_name: str, output_dir: str, css_path: str = None) -> None:
        """Validate input parameters."""
        # Validate letterhead file
        abs_letterhead_path = os.path.abspath(letterhead_path)
        if not os.path.exists(abs_letterhead_path):
            raise InstallerError(f"Letterhead file not found: {abs_letterhead_path}")
        
        if not abs_letterhead_path.lower().endswith('.pdf'):
            raise InstallerError(f"Letterhead must be a PDF file: {abs_letterhead_path}")
        
        # Validate CSS file if provided
        if css_path:
            abs_css_path = os.path.abspath(css_path)
            if not os.path.exists(abs_css_path):
                raise InstallerError(f"CSS file not found: {abs_css_path}")
            
            if not abs_css_path.lower().endswith('.css'):
                raise InstallerError(f"CSS file must have .css extension: {abs_css_path}")
        
        # Validate app name
        if not app_name or not app_name.strip():
            raise InstallerError("App name cannot be empty")
        
        # Check for invalid characters in app name
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in app_name for char in invalid_chars):
            raise InstallerError(f"App name contains invalid characters: {app_name}")
        
        # Validate python path in development mode
        if self.development_mode and self.python_path:
            if not os.path.exists(self.python_path):
                raise InstallerError(f"Python interpreter not found: {self.python_path}")
    
    def _resolve_output_dir(self, output_dir: str) -> str:
        """Resolve and create output directory."""
        if output_dir is None:
            # Default to Desktop
            output_dir = os.path.expanduser("~/Desktop")
        else:
            output_dir = os.path.expanduser(output_dir)
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def _cleanup_existing_app(self, app_path: str) -> None:
        """Remove existing app bundle if it exists."""
        if os.path.exists(app_path):
            self.logger.info(f"Removing existing app: {app_path}")
            try:
                shutil.rmtree(app_path)
            except Exception as e:
                self.logger.warning(f"Could not remove existing app: {e}")
                # Continue anyway - might still work
    
    def _print_success_message(self, app_path: str, letterhead_path: str) -> None:
        """Print success message with usage instructions."""
        mode_str = "Development" if self.development_mode else "Production"
        
        print(f"\n✅ {mode_str} Letterhead Droplet created successfully!")
        print(f"📁 Location: {app_path}")
        print(f"📄 Letterhead: {letterhead_path}")
        print(f"🔧 Version: {__version__}")
        
        if self.development_mode:
            print(f"🐍 Python: {self.python_path}")
            print("\n⚠️  This is a DEVELOPMENT droplet using local code.")
        
        print("\n📋 Usage Instructions:")
        print("1. Drag and drop PDF or Markdown files onto the app")
        print("2. On first use, macOS may ask for file access permissions - please allow them")
        print("3. Test by double-clicking the app (shows info dialog)")
        
        if not self.development_mode:
            print("\n🔍 Troubleshooting:")
            print("• Check System Preferences > Security & Privacy > Privacy > Files and Folders")
            print(f"• Look for logs in ~/Library/Logs/Mac-letterhead/droplet.log")
