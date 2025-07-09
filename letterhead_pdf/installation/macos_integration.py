"""
MacOSIntegration - Handles macOS-specific operations.

This class manages macOS-specific functionality:
- AppleScript compilation
- App bundle configuration
- File associations and permissions
"""

import os
import logging
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
        """Configure Info.plist for file associations."""
        info_plist_path = os.path.join(app_path, "Contents", "Info.plist")
        
        if not os.path.exists(info_plist_path):
            self.logger.warning("Info.plist not found")
            return
        
        try:
            # Read existing plist
            with open(info_plist_path, 'r') as f:
                plist_content = f.read()
            
            # Add document types if not already present
            if 'CFBundleDocumentTypes' not in plist_content:
                document_types = '''	<key>CFBundleDocumentTypes</key>
	<array>
		<dict>
			<key>CFBundleTypeExtensions</key>
			<array>
				<string>pdf</string>
			</array>
			<key>CFBundleTypeName</key>
			<string>PDF Document</string>
			<key>CFBundleTypeRole</key>
			<string>Viewer</string>
			<key>LSHandlerRank</key>
			<string>Alternate</string>
		</dict>
		<dict>
			<key>CFBundleTypeExtensions</key>
			<array>
				<string>md</string>
				<string>markdown</string>
			</array>
			<key>CFBundleTypeName</key>
			<string>Markdown Document</string>
			<key>CFBundleTypeRole</key>
			<string>Viewer</string>
			<key>LSHandlerRank</key>
			<string>Alternate</string>
		</dict>
	</array>
	<key>NSHighResolutionCapable</key>
	<true/>'''
                
                # Insert before closing dict tag
                plist_content = plist_content.replace(
                    '</dict>\n</plist>', 
                    document_types + '\n</dict>\n</plist>'
                )
                
                # Write back
                with open(info_plist_path, 'w') as f:
                    f.write(plist_content)
                
                self.logger.info("Updated Info.plist with file associations")
            
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
