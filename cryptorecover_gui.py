#!/usr/bin/env python3
"""
CryptoRecover GUI Entry Point
"""

import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).parent))

from gui.main import main

if __name__ == "__main__":
    main()
