#!/usr/bin/env python3
"""
DnD GM Toolkit - Terminal UI Launcher

Launch the terminal user interface.

Usage:
    python -m tui
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tui.app import main

if __name__ == "__main__":
    main()
