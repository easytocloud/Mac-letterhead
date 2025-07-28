#!/usr/bin/env python3
"""
Entry point for Mac-letterhead MCP Server
"""

import asyncio
import sys
import os

# Add the package directory to Python path for development
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from letterhead_pdf.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())