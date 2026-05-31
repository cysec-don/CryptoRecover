"""
Logger for CryptoRecover.
"""

import logging
import os
import sys
from rich.logging import RichHandler


def setup_logger(level: str = "INFO", log_file: str = None) -> logging.Logger:
    """Set up the application logger."""
    logger = logging.getLogger("cryptorecover")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers to prevent duplicates on repeated calls
    logger.handlers.clear()
    

    # Rich console handler
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    return logger


# Global logger instance
log = setup_logger()
