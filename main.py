#!/usr/bin/env python3
"""
Main entry point for the Arbitrage Finder application.
Can run as console application or Discord bot.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.arbitrage_finder import main as finder_main

if __name__ == "__main__":
    finder_main()

