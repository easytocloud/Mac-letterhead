"""
Installation module for Mac-letterhead droplet creation.

This module provides a clean separation of concerns for droplet installation:
- DropletBuilder: Main orchestrator for droplet creation
- ResourceManager: Handles stationery files and resource bundling
- AppleScriptGenerator: Generates AppleScript from templates
- MacOSIntegration: Handles macOS-specific operations
- DropletValidator: Validates droplet functionality
"""

from .droplet_builder import DropletBuilder
from .resource_manager import ResourceManager
from .applescript_generator import AppleScriptGenerator
from .macos_integration import MacOSIntegration
from .validator import DropletValidator

__all__ = [
    'DropletBuilder',
    'ResourceManager', 
    'AppleScriptGenerator',
    'MacOSIntegration',
    'DropletValidator'
]
