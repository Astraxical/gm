#!/usr/bin/env python3
"""
DnD GM Toolkit - Desktop GUI Launcher

Launch the desktop graphical user interface.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import main

if __name__ == "__main__":
    main()
