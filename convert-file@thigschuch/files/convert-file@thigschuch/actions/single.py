#!/usr/bin/python3
"""
Single file conversion action.

This module provides the Action class for handling single file conversions
with a clean separation of concerns between validation, format selection,
conversion execution, and user notifications.
"""

from pathlib import Path
from typing import Optional

from actions import BaseAction
from converters import Converter
from core import ConverterFactory
from utils import text
from utils.logging import logger


class Action(BaseAction):
    """Single file conversion action handler.

    Handles the complete workflow for converting individual files with
    comprehensive validation, user interaction, and error handling.

    The conversion process follows these steps:
    1. File validation (existence, permissions, format support)
    2. Source format detection
    3. Target format selection via user dialog
    4. Converter creation and execution
    5. Success/failure notifications

    Attributes:
        file: Path to the file being converted.
        last_converter: Reference to the converter used for the last conversion,
                       useful for error reporting and debugging.

    Examples:
        >>> action = Action(Path("document.pdf"))
        >>> success = action.run()
        >>> if success:
        ...     print("Conversion completed successfully")
    """

    def __init__(self, file: Path) -> None:
        """Initialize the single file conversion action.

        Args:
            file: Path to the file to be converted.

        Returns:
            None

        Note:
            The file path is stored but not validated until run() is called.
        """
        self.file: Path = file
        self.last_converter: Optional[Converter] = None

    def run(self) -> bool:
        """Execute the complete single file conversion workflow.

        Performs the full conversion process including validation, format
        detection, user interaction for format selection, and conversion
        execution with progress tracking and notifications.

        Returns:
            bool: True if conversion completed successfully, False if it
                  failed or was cancelled.

        Raises:
            No exceptions are raised - all errors are handled internally
            with user dialogs.

        Note:
            This method handles all user interaction and error reporting
            automatically. Success/failure is indicated only by the return value.
        """
        logger.info("Starting single file conversion for: {}", self.file)
        try:
            if not self._validate_single_file(self.file):
                logger.error("File validation failed for: {}", self.file)
                return False

            source_format: str = self._get_file_format(self.file) or "unknown"
            logger.debug(
                "Detected source format: {} for file: {}", source_format, self.file
            )

            target_formats = self._get_available_formats(source_format)
            if not target_formats:
                logger.warning(
                    "No target formats available for source format: {}", source_format
                )
                self._show_no_conversion_options_error(self.file, source_format)
                return False

            logger.debug("Available target formats: {}", target_formats)

            target_format: Optional[str] = self._select_format(
                source_format, target_formats
            )
            if not target_format:
                logger.info("User cancelled format selection for: {}", self.file)
                return False

            logger.info("Creating converter for {} -> {}", source_format, target_format)
            converter = ConverterFactory.create_converter(self.file, target_format)
            if not converter:
                logger.error(
                    "Failed to create converter for {} -> {}",
                    source_format,
                    target_format,
                )
                self._show_error(
                    message=text.Conversion.NO_SUITABLE_CONVERTER_MESSAGE,
                    details=text.Conversion.CONVERTER_ERROR_DETAILS_MESSAGE.format(
                        source=source_format, target=target_format, file=self.file
                    ),
                )
                return False

            self.last_converter = converter
            logger.debug("Converter created successfully: {}", type(converter).__name__)

            self.notification.notify_conversion_started(
                file_name=self.file.name, extension=target_format
            )

            logger.info("Starting conversion process")
            success: bool = converter.convert()

            if success:
                logger.info("Conversion completed successfully for: {}", self.file)
                self.notification.notify_conversion_success(
                    file_name=self.file.name, extension=target_format
                )
            else:
                logger.error("Conversion failed for: {}", self.file)

            return success

        except Exception as e:
            error_msg: str = str(e).lower()
            logger.error("Exception during conversion: {}", str(e))
            if "cancel" in error_msg or error_msg == "error":
                return False
            self._show_unexpected_error(e)
            return False
