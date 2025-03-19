#!/usr/bin/env python3

import os
import logging
import sys

# Define log location constants
LOG_DIR = os.path.expanduser("~/Library/Logs/Mac-letterhead")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "letterhead.log")

def configure_logging(level=logging.INFO):
    """Configure logging with the specified level"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stderr)  # Log to stderr for PDF Service context
        ]
    )
