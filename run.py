#!/usr/bin/env python3
"""
CryptoRecover - AI-Enhanced Crypto Wallet Recovery Tool

Quick launcher script for the application.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli.app import main

if __name__ == "__main__":
    main()
