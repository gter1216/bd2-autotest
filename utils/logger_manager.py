"""
Description: This module provides a logger manager for handling logging configurations
             and ensuring a single logger instance.

Changelog:
- 2025-03-07: Initial Creation.
"""

import logging
import sys
import os
from config import (
    LOG_LEVEL,
    LOG_TO_CONSOLE,
    LOG_TO_FILE,
    LOG_FORMAT,
    DATE_FORMAT,
    get_log_file_path,
)


class LoggerManager:
    _instance = (
        None  # Singleton pattern to ensure only one LoggerManager instance globally
    )
    _logger = None  # Shared logger object
    _log_env = None  # Log environment (WebClient / pytest)

    def __new__(cls, env="webclient"):
        """
        Singleton pattern: Ensure only one instance of LoggerManager and decide log storage
        location based on environment
        """
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._log_env = env
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize Logger"""
        if LoggerManager._logger is None:
            LoggerManager._logger = logging.getLogger("UnifiedLogger")
            LoggerManager._logger.setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))

            formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

            # Console log
            if LOG_TO_CONSOLE:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                console_handler.setFormatter(formatter)
                LoggerManager._logger.addHandler(console_handler)

            # File log
            if LOG_TO_FILE:
                log_file_path = get_log_file_path(self._log_env)
                file_handler = logging.FileHandler(log_file_path)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                LoggerManager._logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, file_path, env="webclient"):
        """
        Get Logger and use `filename` as log prefix
        - file_path: Pass `__file__` to automatically extract filename
        - env: Running environment ("webclient" or "pytest")
        """
        instance = cls(
            env
        )  # Ensure LoggerManager is initialized according to environment
        filename = os.path.basename(file_path).replace(
            ".py", ""
        )  # Extract filename (remove .py)
        return logging.getLogger(filename)
