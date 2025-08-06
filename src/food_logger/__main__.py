#!/usr/bin/env python3
"""
Main entry point for food_logger module
Allows running: python -m src.food_logger "food description"
"""

import sys
from .gemini_client import main

if __name__ == '__main__':
    sys.exit(main())
