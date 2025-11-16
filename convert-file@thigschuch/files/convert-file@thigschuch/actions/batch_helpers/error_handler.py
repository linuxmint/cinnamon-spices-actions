#!/usr/bin/python3
"""
Error handling for batch conversions.

This module provides centralized error collection and reporting
for batch file conversion operations.
"""

from pathlib import Path
from typing import Dict, List, Optional

from converters.base import Converter
from utils.logging import logger
from utils.validation import FileValidator


class BatchErrorHandler:
    """Handles error collection and reporting for batch conversions.

    Provides consistent error formatting and display for failed conversions
    during batch processing operations. Collects detailed error information
    including file paths, conversion details, commands, and error output.

    Attributes:
        errors: List of error dictionaries containing detailed error information.

    Examples:
        >>> handler = BatchErrorHandler()
        >>> handler.record_error(
        ...     Path("/tmp/video.mp4"),
        ...     "Conversion failed",
        ...     command="ffmpeg -i video.mp4 output.mp3"
        ... )
        >>> print(f"Errors recorded: {handler.get_error_count()}")
    """

    def __init__(self) -> None:
        """Initialize the batch error handler."""
        self.errors: List[Dict[str, str]] = []

    def record_error(
        self,
        file_path: Path,
        error_msg: str,
        command: Optional[str] = None,
        stderr: Optional[str] = None,
        converter: Optional[Converter] = None,
    ) -> None:
        """Record a conversion error with detailed information.

        Stores comprehensive error details including file information,
        conversion type, executed command, and error output for later
        display or logging.

        Args:
            file_path: Path to the file that failed conversion.
            error_msg: Primary error message describing the failure.
            command: The command that was executed (optional).
            stderr: Standard error output from the command (optional).
            converter: Converter instance with format information (optional).

        Examples:
            >>> handler = BatchErrorHandler()
            >>> handler.record_error(
            ...     Path("/tmp/corrupted.mp4"),
            ...     "Invalid file format",
            ...     command="ffmpeg -i corrupted.mp4 output.mp3",
            ...     stderr="ffmpeg: Invalid data found when processing input"
            ... )
        """
        logger.debug("Recording batch conversion error for file: {}", file_path)
        conversion_info = ""
        if converter:
            source_format = FileValidator.get_file_format(converter.file) or "UNKNOWN"
            target_format = converter.format
            conversion_info = f"{source_format} → {target_format}"
            logger.debug("Error conversion info: {}", conversion_info)

        error_parts = [f"Error: {error_msg}"]

        if command:
            error_parts.append(f"\nCommand:\n{command}")
            logger.debug("Error command: {}", command)

        if stderr and stderr != error_msg:
            error_parts.append(f"\n\nCommand output:\n{stderr}")
            logger.debug("Error stderr captured")

        self.errors.append(
            {
                "conversion": conversion_info,
                "file": file_path.name,
                "message": "\n".join(error_parts),
            }
        )
        logger.info("Batch error recorded for file: {} - {}", file_path.name, error_msg)

    def has_errors(self) -> bool:
        """Check if any errors have been recorded.

        Returns:
            bool: True if one or more errors have been recorded, False otherwise.

        Examples:
            >>> handler = BatchErrorHandler()
            >>> handler.record_error(Path("/tmp/test.mp4"), "Failed")
            >>> print(handler.has_errors())  # True
        """
        return len(self.errors) > 0

    def get_error_count(self) -> int:
        """Get the number of recorded errors.

        Returns:
            int: The total number of errors that have been recorded.

        Examples:
            >>> handler = BatchErrorHandler()
            >>> handler.record_error(Path("/tmp/file1.mp4"), "Error 1")
            >>> handler.record_error(Path("/tmp/file2.mp4"), "Error 2")
            >>> print(handler.get_error_count())  # 2
        """
        return len(self.errors)

    def get_formatted_errors(self) -> str:
        """Get all errors formatted for display.

        Formats all recorded errors into a human-readable string with
        proper separation and structure for user display.

        Returns:
            str: Formatted error string with file information, conversion
                 details, and error messages. Empty string if no errors.

        Examples:
            >>> handler = BatchErrorHandler()
            >>> handler.record_error(Path("/tmp/video.mp4"), "Conversion failed")
            >>> formatted = handler.get_formatted_errors()
            >>> print("Errors found:" in formatted)  # True
        """
        if not self.errors:
            return ""

        error_entries = []

        for error in self.errors:
            entry_parts = [
                f"File: {error['file']}",
                "",  # Add an empty line for better readability
            ]

            if error.get("conversion"):
                entry_parts.extend([f"Conversion: {error['conversion']}", ""])

            entry_parts.append(error["message"])
            error_entries.append("\n".join(entry_parts))

        separator = "\n\n" + "─" * 60 + "\n\n"
        return separator.join(error_entries)
