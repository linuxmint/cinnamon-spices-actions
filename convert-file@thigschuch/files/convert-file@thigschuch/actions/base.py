#!/usr/bin/python3
"""
Base classes for file conversion actions.

This module provides the foundational classes and common functionality
shared between single file and batch file conversion operations.

Classes:
    BaseAction: Abstract base class providing common validation, error handling,
               and format detection methods used by all conversion actions.
"""

import traceback
from pathlib import Path
from typing import Optional, Tuple

from config.settings import settings_manager
from ui import (
    ErrorDialogWindow,
    Gtk,
    InfoDialogWindow,
    SelectDropdownDialogWindow,
    notification,
)
from utils import text
from utils.logging import logger
from utils.validation import FileValidator


class BaseAction:
    """Base class for file conversion actions.

    Provides common functionality for validation, error handling, and format
    detection shared between single and batch file conversion operations.

    This class implements the core validation logic and user interaction
    patterns used by both single-file and batch conversion workflows.

    Attributes:
        notification: Reference to the notification system for user feedback.

    Note:
        This is an abstract base class and should not be instantiated directly.
        Use Action for single files or BatchAction for multiple files instead.
    """

    notification = notification

    def _show_error(self, message: str, details: Optional[str] = None) -> None:
        """Display an error dialog to the user.

        Shows an error dialog with the specified message. If additional details
        are provided, displays them in an expandable error details section.

        Args:
            message: The main error message to display.
            details: Optional additional error details for debugging.

        Returns:
            None

        Examples:
            >>> self._show_error("File not found")
            >>> self._show_error("Conversion failed", "ffmpeg returned error code 1")
        """
        dialog = (
            ErrorDialogWindow(message=message, error_details=details)
            if details
            else InfoDialogWindow(message=message)
        )
        dialog.run()
        dialog.destroy()

    def _show_unexpected_error(self, error: Exception) -> None:
        """Display a dialog for unexpected runtime errors.

        Shows a standardized unexpected error dialog with the provided error
        message and full traceback as additional details for debugging.

        Args:
            error: The exception that was raised.

        Returns:
            None
        """
        error_msg = str(error)
        traceback_str = traceback.format_exc()

        logger.error("Unexpected error occurred: {}", error_msg)
        logger.error("Traceback:\n{}", traceback_str)

        self._show_error(
            message=text.Errors.UNEXPECTED_ERROR_MESSAGE,
            details=f"Error: {error_msg}\n\nTraceback:\n{traceback_str}",
        )

    def _get_file_format(self, file_path: Path) -> Optional[str]:
        """Get the format of a file based on its extension.

        Determines the file format by examining the file extension and
        mapping it to known format types.

        Args:
            file_path: Path to the file whose format should be determined.

        Returns:
            Optional[str]: The file format (e.g., 'JPEG', 'MP4') if recognized,
                          None if the format cannot be determined.

        Examples:
            >>> self._get_file_format(Path("image.jpg"))
            'JPEG'
            >>> self._get_file_format(Path("document.pdf"))
            'PDF'
        """
        return FileValidator.get_file_format(file_path)

    def _validate_single_file(self, file_path: Path) -> bool:
        """Validate that a single file exists and is convertible.

        Performs comprehensive validation on a single file including:
        - File existence
        - Read permissions
        - Supported format detection
        - File size limits

        Args:
            file_path: Path to the file to validate.

        Returns:
            bool: True if the file is valid and convertible, False otherwise.

        Note:
            Displays an error dialog to the user if validation fails.
        """
        logger.debug("Validating single file: {}", file_path)
        is_valid, error_msg = FileValidator.validate_single_file(file_path)
        if not is_valid and error_msg:
            logger.error("File validation failed: {}", error_msg)
            self._show_error(message=error_msg)
        else:
            logger.debug("File validation passed for: {}", file_path)
        return is_valid

    def _show_no_conversion_options_error(
        self, file_path: Path, source_format: str
    ) -> None:
        """Display error when no conversion options are available for a format.

        Shows a user-friendly error message when the source format has no
        available target formats for conversion.

        Args:
            file_path: Path to the file that cannot be converted.
            source_format: The source format that has no conversion options.

        Returns:
            None
        """
        self._show_error(
            message=text.Conversion.NO_CONVERSION_OPTIONS_MESSAGE.format(
                extension=source_format, filename=file_path.name
            ),
        )

    def _get_available_formats(self, source_format: str) -> Tuple[str, ...]:
        """Get available target formats for a given source format.

        Retrieves all supported target formats that the source format can be
        converted to, based on the configured conversion rules.

        Args:
            source_format: The source file format (e.g., 'JPEG', 'MP4').

        Returns:
            Tuple[str, ...]: Tuple of available target format names.

        Examples:
            >>> self._get_available_formats('JPEG')
            ('PNG', 'BMP', 'TIFF', 'WebP')
        """
        return FileValidator.get_available_formats(source_format)

    def _select_format(
        self, source_format: str, available_formats: Tuple[str, ...]
    ) -> Optional[str]:
        """Display a dialog for the user to select the target format.

        Presents a dropdown dialog allowing the user to choose the desired
        target format from the available options. Uses intelligent defaults
        based on the source format and optionally pre-selects based on usage history.

        Args:
            source_format: The source file format being converted from.
            available_formats: Tuple of available target formats to choose from.

        Returns:
            Optional[str]: The selected target format, or None if the user
                          cancelled the dialog.

        Note:
            The dialog pre-selects the most common target format for the
            source format when possible. If preselect_format_by_usage is enabled,
            it will pre-select based on usage history.
        """
        logger.debug(
            "Selecting target format for source format: {} with available formats: {}",
            source_format,
            available_formats,
        )

        if not source_format or not available_formats:
            logger.warning("No source format or available formats provided")
            return None


        preselect_format_by_usage = settings_manager.get(
            "preselect_format_by_usage", False
        )
        default_choice = ""
        from utils.usage_tracker import usage_tracker

        if preselect_format_by_usage:
            most_used = usage_tracker.get_most_used_format(source_format)
            if most_used and most_used in available_formats:
                default_choice = most_used
                logger.debug("Using most used format from history: {}", default_choice)

        if not default_choice:
            default_format = FileValidator.get_default_format(source_format)
            default_choice = (
                default_format
                if default_format in available_formats
                else available_formats[0] if available_formats else ""
            )
            logger.debug("Using default choice from configuration: {}", default_choice)

        logger.debug("Final default choice: {}", default_choice)

        dialog = SelectDropdownDialogWindow(
            label=text.UI.FORMAT_SELECTION_LABEL,
            choices=available_formats,
            default_choice=default_choice,
            ok_button_label=text.UI.START_BUTTON_LABEL,
        )

        response = dialog.run()
        target_format = (
            dialog.get_selected() if response == Gtk.ResponseType.OK else None
        )
        dialog.destroy()

        if target_format:
            logger.info(
                "User selected target format: {} for source: {}",
                target_format,
                source_format,
            )
            if preselect_format_by_usage:
                usage_tracker.record_conversion(source_format, target_format)
        else:
            logger.info("User cancelled format selection")

        return target_format
