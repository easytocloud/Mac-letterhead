"""
DropletValidator - Validates droplet functionality.

This class validates that created droplets work correctly:
- Basic app bundle structure validation
- Resource validation
- Functional testing
"""

import os
import logging
from typing import Optional

from letterhead_pdf.exceptions import InstallerError


class DropletValidator:
    """Validates droplet functionality."""
    
    def __init__(self):
        """Initialize the DropletValidator."""
        self.logger = logging.getLogger(__name__)
    
    def validate_droplet(self, app_path: str, letterhead_path: str) -> bool:
        """
        Validate a created droplet.
        
        Args:
            app_path: Path to the app bundle
            letterhead_path: Original letterhead file path
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        self.logger.info(f"Validating droplet: {app_path}")
        
        try:
            # Basic structure validation
            if not self._validate_app_structure(app_path):
                return False
            
            # Resource validation
            if not self._validate_resources(app_path, letterhead_path):
                return False
            
            # Executable validation
            if not self._validate_executable(app_path):
                return False
            
            self.logger.info("Droplet validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Droplet validation failed: {e}")
            return False
    
    def _validate_app_structure(self, app_path: str) -> bool:
        """Validate basic app bundle structure."""
        required_dirs = [
            os.path.join(app_path, "Contents"),
            os.path.join(app_path, "Contents", "Resources"),
            os.path.join(app_path, "Contents", "MacOS")
        ]
        
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                self.logger.error(f"Missing required directory: {dir_path}")
                return False
        
        # Check for Info.plist
        info_plist = os.path.join(app_path, "Contents", "Info.plist")
        if not os.path.exists(info_plist):
            self.logger.error(f"Missing Info.plist: {info_plist}")
            return False
        
        self.logger.info("App bundle structure validation passed")
        return True
    
    def _validate_resources(self, app_path: str, letterhead_path: str) -> bool:
        """Validate app resources."""
        resources_dir = os.path.join(app_path, "Contents", "Resources")
        
        # Check letterhead file
        app_letterhead = os.path.join(resources_dir, "letterhead.pdf")
        if not os.path.exists(app_letterhead):
            self.logger.error(f"Missing letterhead in app bundle: {app_letterhead}")
            return False
        
        # Validate letterhead file size (should match original)
        try:
            original_size = os.path.getsize(letterhead_path)
            app_size = os.path.getsize(app_letterhead)
            
            if original_size != app_size:
                self.logger.error(f"Letterhead size mismatch: {original_size} vs {app_size}")
                return False
                
        except Exception as e:
            self.logger.error(f"Could not validate letterhead size: {e}")
            return False
        
        # Check for icons (optional, just warn if missing)
        icon_files = ["applet.icns", "droplet.icns", "icon.png"]
        for icon_file in icon_files:
            icon_path = os.path.join(resources_dir, icon_file)
            if not os.path.exists(icon_path):
                self.logger.warning(f"Optional icon missing: {icon_path}")
        
        self.logger.info("Resource validation passed")
        return True
    
    def _validate_executable(self, app_path: str) -> bool:
        """Validate app executable."""
        macos_dir = os.path.join(app_path, "Contents", "MacOS")
        
        # Find executable files
        executables = []
        if os.path.exists(macos_dir):
            for item in os.listdir(macos_dir):
                item_path = os.path.join(macos_dir, item)
                if os.path.isfile(item_path):
                    executables.append(item_path)
        
        if not executables:
            self.logger.error("No executable found in MacOS directory")
            return False
        
        # Check permissions on executables
        for executable in executables:
            if not os.access(executable, os.X_OK):
                self.logger.error(f"Executable not executable: {executable}")
                return False
        
        self.logger.info("Executable validation passed")
        return True
    
    def validate_letterhead_compatibility(self, letterhead_path: str) -> Optional[str]:
        """
        Validate letterhead file for common issues.
        
        Args:
            letterhead_path: Path to the letterhead file
            
        Returns:
            str: Warning message if issues found, None if OK
        """
        try:
            if not os.path.exists(letterhead_path):
                return "Letterhead file not found"
            
            # Check file size
            file_size = os.path.getsize(letterhead_path)
            if file_size == 0:
                return "Letterhead file is empty"
            
            if file_size > 50 * 1024 * 1024:  # 50MB
                return f"Letterhead file is very large ({file_size // (1024*1024)}MB) - may cause performance issues"
            
            # Check PDF signature
            with open(letterhead_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    return "File does not appear to be a valid PDF"
            
            # TODO: Could add more sophisticated PDF analysis here
            # - Check for transparency
            # - Check page count
            # - Check dimensions
            
            return None
            
        except Exception as e:
            return f"Error validating letterhead: {str(e)}"
    
    def quick_functional_test(self, app_path: str) -> bool:
        """
        Perform a quick functional test of the droplet.
        
        Args:
            app_path: Path to the app bundle
            
        Returns:
            bool: True if basic functionality works
        """
        try:
            # This is a basic test - just check if we can execute the app
            # In a more comprehensive test, we might actually test file processing
            
            executable_path = self._find_main_executable(app_path)
            if not executable_path:
                self.logger.error("Could not find main executable for testing")
                return False
            
            # For now, just check that the executable exists and is executable
            if not os.access(executable_path, os.X_OK):
                self.logger.error("Main executable is not executable")
                return False
            
            self.logger.info("Quick functional test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Functional test failed: {e}")
            return False
    
    def _find_main_executable(self, app_path: str) -> Optional[str]:
        """Find the main executable in the app bundle."""
        macos_dir = os.path.join(app_path, "Contents", "MacOS")
        
        if not os.path.exists(macos_dir):
            return None
        
        # Look for executable files
        for item in os.listdir(macos_dir):
            item_path = os.path.join(macos_dir, item)
            if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                return item_path
        
        return None
