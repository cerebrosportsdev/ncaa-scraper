#!/usr/bin/env python3
"""
Main entry point for the refactored NCAA scraper.
This is a simple wrapper that imports and runs the main function from the ncaa_scraper package.
"""

from ncaa_scraper.main import main

if __name__ == "__main__":
    exit(main())
