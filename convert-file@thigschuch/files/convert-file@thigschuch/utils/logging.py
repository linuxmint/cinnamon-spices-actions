#!/usr/bin/python3
"""
Conditional logging utilities for the file converter.

This module provides lightweight logging functionality that activates
only when a DEBUG file exists in the user configuration directory.
When enabled, log messages are printed to stdout with color coding
by log level. When disabled, all logging operations are no-ops for
optimal performance.

The logging system is designed to have zero performance impact when
debugging is not active, making it safe to include in production code.
"""

import contextlib
from functools import lru_cache
from pathlib import Path


class LogColors:
    """ANSI color codes for different log levels."""

    RESET = "\033[0m"

    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[31;1m"  # Red + Bold


class Logger:
    """Conditional logger activated by DEBUG file presence.

    The logger checks for the existence of a DEBUG file in the user config
    directory (~/.config/convert-file@thigschuch/DEBUG). When present, it
    prints formatted log messages to stdout with color coding by log level:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red (bold)

    When absent, all logging methods become no-ops.

    This design ensures debugging can be enabled on-demand without
    performance penalties in normal operation.

    Attributes:
        _debug_file_path: Path to the DEBUG trigger file.

    Examples:
        >>> logger = Logger()
        >>> logger.debug("Processing file: {}", "example.jpg")
        >>> logger.error("Conversion failed: {}", str(error))
    """

    def __init__(self) -> None:
        """Initialize the conditional logger.

        Sets up the path to the DEBUG trigger file.
        """
        config_dir = Path.home() / ".config" / "convert-file@thigschuch"
        self._debug_file_path = config_dir / "DEBUG"

    @lru_cache(maxsize=1)
    def _is_debug_enabled(self) -> bool:
        """Check if debug logging is currently enabled.

        Uses functools.lru_cache to memoize the result of checking
        whether the DEBUG file exists. This provides efficient caching
        with a built-in Python mechanism.

        Returns:
            bool: True if DEBUG file exists and logging is active.
        """
        return self._debug_file_path.exists()

    def _print_log_message(self, level: str, message: str, *args) -> None:
        """Print a formatted log message to stdout with color coding.

        Formats the message with provided arguments and prints it to stdout
        with a colored log level prefix in brackets. Only prints
        when debugging is enabled.

        Args:
            level: Log level string (e.g., 'DEBUG', 'INFO', 'ERROR').
            message: Log message with optional format placeholders.
            *args: Arguments to format into the message.

        Note:
            Silently ignores any formatting or printing errors to prevent
            logging failures from disrupting the main application flow.
            Only the [LEVEL] part is colored, the message uses default color.
        """
        if not self._is_debug_enabled():
            return

        with contextlib.suppress(Exception):
            if args:
                formatted_message = message.format(*args)
            else:
                formatted_message = message

            color = getattr(LogColors, level, LogColors.RESET)
            log_entry = f"{color}[{level}]{LogColors.RESET}: {formatted_message}\n"
            print(log_entry, end="")

    def debug(self, message: str, *args) -> None:
        """Log a debug-level message.

        Records detailed information useful for debugging and development.
        Only outputs when debug mode is active.

        Args:
            message: Debug message with optional format placeholders.
            *args: Arguments to format into the message.

        Examples:
            >>> logger.debug("Processing file: {}", filename)
            >>> logger.debug("Conversion started for format: {}", format_type)
        """
        self._print_log_message("DEBUG", message, *args)

    def info(self, message: str, *args) -> None:
        """Log an informational message.

        Records general information about application operation and
        significant events during normal execution.

        Args:
            message: Info message with optional format placeholders.
            *args: Arguments to format into the message.

        Examples:
            >>> logger.info("Conversion completed successfully")
            >>> logger.info("Batch processing {} files", file_count)
        """
        self._print_log_message("INFO", message, *args)

    def warning(self, message: str, *args) -> None:
        """Log a warning message.

        Records potentially harmful situations or unusual conditions
        that don't prevent normal operation but may require attention.

        Args:
            message: Warning message with optional format placeholders.
            *args: Arguments to format into the message.

        Examples:
            >>> logger.warning("File not found: {}", filepath)
            >>> logger.warning("Using fallback conversion method")
        """
        self._print_log_message("WARNING", message, *args)

    def error(self, message: str, *args) -> None:
        """Log an error message.

        Records error conditions that prevent normal operation or
        indicate failed operations that should be investigated.

        Args:
            message: Error message with optional format placeholders.
            *args: Arguments to format into the message.

        Examples:
            >>> logger.error("Conversion failed: {}", str(error))
            >>> logger.error("Invalid format: {}", extension)
        """
        self._print_log_message("ERROR", message, *args)

    def critical(self, message: str, *args) -> None:
        """Log a critical error message.

        Records severe error conditions that may cause application
        instability or complete failure. Use sparingly for the most
        serious issues.

        Args:
            message: Critical message with optional format placeholders.
            *args: Arguments to format into the message.

        Examples:
            >>> logger.critical("Application encountered fatal error")
            >>> logger.critical("Required system dependency missing: {}", tool_name)
        """
        self._print_log_message("CRITICAL", message, *args)


logger = Logger()
