"""
MacOSIntegration - Handles macOS-specific operations.

This class manages macOS-specific functionality:
- AppleScript compilation
- App bundle configuration
- File associations and permissions
"""

import os
import logging
import plistlib
from subprocess import run, PIPE

from letterhead_pdf.exceptions import InstallerError


class MacOSIntegration:
    """Handles macOS-specific operations for droplet creation."""
    
    def __init__(self):
        """Initialize the MacOSIntegration."""
        self.logger = logging.getLogger(__name__)
    
    def compile_applescript(self, script_content: str, app_path: str) -> None:
        """
        Compile AppleScript to an application bundle.
        
        Args:
            script_content: AppleScript source code
            app_path: Output path for the app bundle
            
        Raises:
            InstallerError: If compilation fails
        """
        self.logger.info(f"Compiling AppleScript to: {app_path}")
        
        try:
            # Use osacompile to create the app
            result = run(
                ["osacompile", "-o", app_path, "-x"],
                input=script_content,
                text=True,
                capture_output=True
            )
            
            if result.returncode != 0:
                error_msg = f"AppleScript compilation failed: {result.stderr}"
                self.logger.error(error_msg)
                raise InstallerError(error_msg)
            
            self.logger.info("AppleScript compilation successful")
            
        except FileNotFoundError:
            raise InstallerError("osacompile not found - macOS developer tools required")
        except Exception as e:
            error_msg = f"Failed to compile AppleScript: {str(e)}"
            self.logger.error(error_msg)
            raise InstallerError(error_msg) from e
    
    def configure_app_bundle(self, app_path: str) -> None:
        """
        Configure app bundle for file associations and permissions.
        
        Args:
            app_path: Path to the app bundle
        """
        self.logger.info(f"Configuring app bundle: {app_path}")
        
        try:
            # Configure Info.plist for file associations
            self._configure_info_plist(app_path)
            
            # Set executable permissions
            self._set_executable_permissions(app_path)
            
            self.logger.info("App bundle configuration completed")
            
        except Exception as e:
            self.logger.warning(f"App bundle configuration failed: {e}")
            # Don't fail the installation for configuration issues
    
    def _configure_info_plist(self, app_path: str) -> None:
        """Configure Info.plist for file associations and bundle identifier."""
        info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
        
        if not os.path.exists(info_plist_path):
            self.logger.warning("Info.plist not found")
            return
        
        try:
            # Read and parse existing plist
            with open(info_plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
            
            # Add bundle identifier if not present
            if 'CFBundleIdentifier' not in plist_data:
                # Generate unique bundle identifier from app name
                app_name = os.path.basename(app_path).replace('.app', '')
                # Sanitize name for bundle identifier (alphanumeric and hyphens only)
                sanitized_name = ''.join(c.lower() if c.isalnum() else '-' for c in app_name)
                sanitized_name = '-'.join(filter(None, sanitized_name.split('-')))  # Remove empty parts
                bundle_id = f"com.mac-letterhead.droplet.{sanitized_name}"
                
                plist_data['CFBundleIdentifier'] = bundle_id
                self.logger.info(f"Added bundle identifier: {bundle_id}")
            
            # Add display name to show proper name in Privacy & Security
            if 'CFBundleDisplayName' not in plist_data:
                app_name = os.path.basename(app_path).replace('.app', '')
                plist_data['CFBundleDisplayName'] = app_name
                self.logger.info(f"Added display name: {app_name}")
            
            # Add document types if not present
            if 'CFBundleDocumentTypes' not in plist_data:
                document_types = [
                    {
                        'CFBundleTypeExtensions': ['pdf'],
                        'CFBundleTypeName': 'PDF Document',
                        'CFBundleTypeRole': 'Viewer',
                        'LSHandlerRank': 'Alternate'
                    },
                    {
                        'CFBundleTypeExtensions': ['md', 'markdown'],
                        'CFBundleTypeName': 'Markdown Document',
                        'CFBundleTypeRole': 'Viewer',
                        'LSHandlerRank': 'Alternate'
                    }
                ]
                plist_data['CFBundleDocumentTypes'] = document_types
                self.logger.info("Added document type associations")
            
            # Add high resolution support
            if 'NSHighResolutionCapable' not in plist_data:
                plist_data['NSHighResolutionCapable'] = True
            
            # Write back the modified plist
            with open(info_plist_path, 'wb') as f:
                plistlib.dump(plist_data, f)
            
            self.logger.info("Successfully updated Info.plist")
            
        except Exception as e:
            self.logger.warning(f"Could not configure Info.plist: {e}")
    
    def _set_executable_permissions(self, app_path: str) -> None:
        """Set appropriate executable permissions on the app bundle."""
        try:
            # Find the main executable
            contents_dir = os.path.join(app_path, "Contents")
            macos_dir = os.path.join(contents_dir, "MacOS")
            
            if os.path.exists(macos_dir):
                for item in os.listdir(macos_dir):
                    executable_path = os.path.join(macos_dir, item)
                    if os.path.isfile(executable_path):
                        os.chmod(executable_path, 0o755)
                        self.logger.info(f"Set executable permissions on: {executable_path}")
            
        except Exception as e:
            self.logger.warning(f"Could not set executable permissions: {e}")
