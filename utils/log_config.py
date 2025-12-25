# utils/log_config.py

import sys
from pathlib import Path

from loguru import logger


def setup_logging(logs_dir: Path) -> None:
    """Set up Loguru logging with console and file handlers."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    app_log_file = logs_dir / "app.log"

    # Remove default handler
    logger.remove()

    # Add console handler with INFO level
    logger.add(sys.stdout, level="INFO", format="{message}", colorize=True, backtrace=True, diagnose=True)

    # Add file handler with DEBUG level, JSON format
    logger.add(
        app_log_file,
        level="DEBUG",
        rotation="5 MB",  # Rotate every 5 MB
        retention="5 days",  # Keep logs for 5 days
        compression="zip",  # Compress old log files
        format="{time} {level} {message}",
        serialize=True,  # Output logs in JSON format
        enqueue=True,  # Use a queue for non-blocking logging
        backtrace=True,
        diagnose=True,
    )

    logger.info(f"Logging initialized with Loguru. Console level: INFO, File level: DEBUG, Log file: {app_log_file}")
