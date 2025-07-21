#!/usr/bin/env python3
"""
Logging configuration for Mac-letterhead application.

This module provides centralized logging configuration to ensure
consistent logging behavior across all modules.
"""

import os
import logging
import sys
from typing import Optional

# Define log location constants
LOG_DIR = os.path.expanduser("~/Library/Logs/Mac-letterhead")
LOG_FILE = os.path.join(LOG_DIR, "letterhead.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)


def configure_logging(level: int = logging.INFO, enable_file_logging: bool = True) -> None:
    """
    Configure logging with the specified level and handlers.
    
    Args:
        level: Logging level (default: logging.INFO)
        enable_file_logging: Whether to enable file logging (default: True)
    """
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Configure handlers
    handlers = []
    
    # File handler (if enabled)
    if enable_file_logging:
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(detailed_formatter)
            handlers.append(file_handler)
        except (OSError, PermissionError) as e:
            # If we can't write to the log file, continue without file logging
            print(f"Warning: Could not create log file {LOG_FILE}: {e}", file=sys.stderr)
    
    # Console handler - use stderr for PDF Service context compatibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    handlers.append(console_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    logging.getLogger(__name__).info(f"Logging configured at level {logging.getLevelName(level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
