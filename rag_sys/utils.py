import os
import logging

logger = logging.getLogger(__name__)

def validate_file_path(file_path):
    """Validates if given file path exists and is a file."""
    if not file_path:
        logger.error("File path cannot be empty.")
        return False
    if not os.path.exists(file_path):
        logger.error(f"File path does not exist: {file_path}")
        return False
    if not os.path.isfile(file_path):
        logger.error(f"Provided path is not a file: {file_path}")
        return False
    return True