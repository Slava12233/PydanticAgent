#!/usr/bin/env python
"""
Entry point for the Telegram bot.
This file is used to run the bot from the command line.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main function from the src module
from src.main import main

if __name__ == "__main__":
    try:
        logger.info("Starting Pydantic AI Telegram Bot")
        main()
    except Exception as e:
        logger.error(f"Unhandled exception in run.py: {e}")
        sys.exit(1) 