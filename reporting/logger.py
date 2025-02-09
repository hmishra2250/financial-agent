# reporting/logger.py
import logging
import os

def setup_logger(log_file_path, log_level=logging.INFO):
    """
    Sets up the logger for the application.

    Args:
        log_file_path (str):  The path to the log file.
        log_level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
    """

    # Create the logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create a file handler and set the level
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)

    # Create a console handler with a higher log level (e.g., WARNING)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Show warnings and errors on the console

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger