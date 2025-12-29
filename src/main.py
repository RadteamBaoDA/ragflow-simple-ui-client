#!/usr/bin/env python3
"""
Development entry point for RAGFlow Client.

This script allows running the CLI directly during development without
needing to install the package first.

Usage:
    python main.py [COMMAND] [OPTIONS]
    
Examples:
    python main.py --help
    python main.py status
    python main.py run
    python main.py convert ./input_docs --output ./pdfs

Note:
    For production use, install the package and use:
        simple-client [COMMAND] [OPTIONS]
"""

import sys
from pathlib import Path

# Add the src directory to Python path so imports work without installation
# This allows running the CLI directly: python main.py
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Import and run the CLI application
from ragflow_client.cli.commands import app

if __name__ == "__main__":
    app()
