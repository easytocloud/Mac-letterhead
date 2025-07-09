#!/usr/bin/env python3

"""
Legacy installer interface for backward compatibility.

This module provides backward compatibility with the old installer interface
while delegating to the new installation module structure.
"""

import sys
import os
import logging
from typing import Optional

from letterhead_pdf.installation import DropletBuilder
from letterhead_pdf.exceptions import InstallerError
from letterhead_pdf import __version__


def create_applescript_droplet(
    letterhead_path: str,
    app_name: str = "Letterhead Applier",
    output_dir: str = None,
    local: bool = False,
    python_path: str = None
) -> str:
    """
    Create an AppleScript droplet application for the given letterhead.
    
    This is a legacy compatibility function that delegates to the new
    DropletBuilder class.
    
    Args:
        letterhead_path: Path to the letterhead PDF file
        app_name: Name for the droplet application
        output_dir: Directory to save the droplet (defaults to Desktop)
        local: If True, create a development droplet using local code
        python_path: Path to Python interpreter (for development mode)
        
    Returns:
        str: Path to the created droplet application
    """
    logging.info(f"Creating droplet via legacy interface: {letterhead_path}")
    logging.info(f"App name: {app_name}, local: {local}")
    
    try:
        # Create droplet builder
        builder = DropletBuilder(
            development_mode=local,
            python_path=python_path
        )
        
        # Create the droplet
        return builder.create_droplet(
            letterhead_path=letterhead_path,
            app_name=app_name,
            output_dir=output_dir
        )
        
    except Exception as e:
        logging.error(f"Legacy installer failed: {str(e)}")
        raise InstallerError(f"Failed to create droplet: {str(e)}") from e
