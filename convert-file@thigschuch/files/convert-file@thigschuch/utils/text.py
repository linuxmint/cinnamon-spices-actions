#!/usr/bin/python3
"""
Internationalization and text utilities for the file converter.

This module handles all text localization and provides a centralized
location for all user-facing strings in the application.
"""

import gettext
from pathlib import Path

UUID = "convert-file@thigschuch"
HOME = Path.home()

gettext.bindtextdomain(UUID, str(HOME / ".local" / "share" / "locale"))
gettext.textdomain(UUID)


def _(message) -> str:
    """Translate a message using gettext.

    Args:
        message: The message to translate.

    Returns:
        str: The translated message, or the original if no translation available.
    """
    return gettext.gettext(message)


class Text:
    """Centralized text constants for the application.

    All user-facing strings are defined here to facilitate internationalization
    and maintain consistency across the application. Strings are wrapped with
    gettext _() function for translation support.

    This class contains constants organized into categories for:
    - UI elements and labels
    - File validation messages
    - Conversion process messages
    - Error handling and notifications
    - Application constants

    All messages support string formatting with named placeholders.

    Examples:
        >>> text.UI.APPLICATION_TITLE
        'File Converter'
        >>> text.Validation.FILE_NOT_FOUND_MESSAGE.format(path="/tmp/test.jpg")
        "File not found:\n/tmp/test.jpg\n\nCheck if the file exists."
    """

    class UI:
        """UI elements, labels, and button text."""

        APPLICATION_TITLE = _("File Converter")
        FORMAT_SELECTION_LABEL = _("Choose output format:")
        CONVERSION_PROGRESS_LABEL = _("Converting\n{file} to {extension}")
        COPY_ERROR_BUTTON_LABEL = _("Copy Error")
        COPY_COMMAND_BUTTON_LABEL = _("Copy Command")
        REPORT_ERROR_BUTTON_LABEL = _("Report Error")
        OK_BUTTON_LABEL = _("OK")
        CANCEL_BUTTON_LABEL = _("Cancel")
        CANCELLING_BUTTON_LABEL = _("Cancelling...")
        START_BUTTON_LABEL = _("Start")
        ERROR_DETAILS_COPIED_MESSAGE = _("Error details copied to clipboard")
        INSTALL_COMMAND_COPIED_MESSAGE = _("Install command copied to clipboard")
        MANUAL_INSTALLATION_REQUIRED_MESSAGE = _(
            "No installation instructions available. Please install '{dependency}' manually."
        )
        MIXED_FORMATS_PLACEHOLDER = _("multiple files selected")

    class Validation:
        """File and input validation messages."""

        INVALID_USAGE_MESSAGE = _("Select one or more files to convert.")
        FILE_NOT_FOUND_MESSAGE = _(
            "File not found:\n{path}\n\nCheck if the file exists."
        )
        INVALID_FILE_MESSAGE = _(
            "Invalid file:\n{path}\n\nSelect a file, not a folder."
        )
        MISSING_EXTENSION_MESSAGE = _(
            "No file extension:\n{path}\n\n"
            "Add an extension (e.g., .jpg, .mp4, .pdf) to determine the format."
        )
        UNSUPPORTED_FORMAT_ERROR_MESSAGE = _("Unsupported file format: {extension}")
        UNSUPPORTED_FORMAT_DETAILS_MESSAGE = _(
            "The file '{filename}' has an unsupported format ({extension}).\n\n"
            "This format is not recognized by the converter or the required "
            "tools are not installed on your system."
        )
        ERRORS_MESSAGE = _(
            "Found {error_count} validation error(s) in the selected files:\n\n"
            "{errors}\n\n"
            "The process will continue with valid files only."
        )

    class Conversion:
        """Conversion process related messages."""

        ERROR_MESSAGE = _("Conversion failed.")
        NO_SUITABLE_CONVERTER_MESSAGE = _("No converter found for this format")
        NO_CONVERSION_OPTIONS_MESSAGE = _(
            "No converters available for {extension} files.\n\n"
            "File: {filename}\n\n"
            "Possible causes:\n"
            "• Missing rules\n"
            "• Missing required tools\n"
            "• Unsupported format\n"
            "• Installation issue\n\n"
            "Check system dependencies."
        )
        CONVERTER_ERROR_DETAILS_MESSAGE = _(
            "Failed to create converter for {source} → {target}\n\n"
            "File: {file}\n\n"
            "This could indicate:\n"
            "• Missing conversion tools\n"
            "• Incompatible format combination\n"
            "• System configuration issue"
        )
        BATCH_CONVERSION_PROGRESS_MESSAGE = _(
            "Converting {current} of {total} files to {extension}\n{file}"
        )
        OUTPUT_DIRECTORY_ERROR_MESSAGE = _(
            "Failed to create or access output directory.\n\n" "Error: {error}"
        )
        FAILED_MESSAGE = _("Conversion failed: {error}")
        CANCELLED_BY_USER_MESSAGE = _("Conversion cancelled by user")
        FAILED_CHECK_TOOLS_MESSAGE = _(
            "Conversion failed - check if required tools are installed "
            "(e.g., ffmpeg, convert, 7z, rar, etc.) and the file format is supported"
        )
        TEMPLATE_ERROR_MESSAGE = _("Template error: {error}")

    class Errors:
        """General error messages and tool-related errors."""

        MISSING_TOOL_MESSAGE = _("Required tool '{tool}' is not installed.")
        MISSING_TOOL_MAIN_MESSAGE = _(
            "The conversion tool '{tool}' is required but not found on your system."
        )
        MISSING_TOOL_ERROR_DETAILS = _(
            "Missing Tool: {tool}\n\n"
            "Install Command:\n{install_command}\n\n"
            "Instructions:\n"
            "Copy the install command above and run it in your terminal. "
            "If the command does not work, please refer to your distribution's "
            "package manager or the tool's official installation instructions."
        )
        UNEXPECTED_ERROR_MESSAGE = _("An unexpected error occurred during conversion.")
        REQUIRED_TOOL_NOT_FOUND_MESSAGE = _(
            "Required tool not found. Please make sure all required "
            "conversion tools are installed (e.g., ffmpeg, convert, etc.)"
        )
        SHELL_COMMAND_EXECUTION_FAILED_MESSAGE = _(
            "Shell command execution failed.\n\nError: {error}\n\nCommand: {command}"
        )
        CHAINED_COMMAND_EXECUTION_FAILED_MESSAGE = _(
            "Chained command execution failed.\n\nError: {error}\n\nCommand: {command}"
        )
        FAILED_CONVERSIONS_PLACEHOLDER = _("Failed conversions:\n\n{errors}")
        FAILED_TO_CREATE_TEMP_DIR_MESSAGE = _("Failed to create temporary directory")
        TEMP_DIR_NOT_AVAILABLE_MESSAGE = _("Temporary directory not available")
        TEMP_DIR_DOES_NOT_EXIST_MESSAGE = _("Temporary directory does not exist")
        NO_ARCHIVE_TEMPLATE_MESSAGE = _("No archive template available in settings")
        NO_CONTENTS_IN_ARCHIVE_MESSAGE = _("No contents found in extracted archive")

    class Operations:
        """Operation status and batch processing messages."""

        FAILED_MESSAGE = _("Operation failed")
        CANCELLED_BY_USER_MESSAGE = _("Operation cancelled by user")
        CHAINED_COMMAND_STEP_FAILED_MESSAGE = _(
            "Step {step}/{total} failed.\n\nError: {error}\n\nCommand: {command}"
        )
        FILE_VALIDATION_FAILED_MESSAGE = _(
            "File validation failed: {file}\n\n"
            "The previous conversion step likely failed.\n\n"
            "Previous step output:\n{previous_error}"
        )
        BATCH_CONVERSION_CANCELLED_MESSAGE = _("Batch conversion cancelled")
        BATCH_CONVERSION_COMPLETED_WITH_ERRORS_MESSAGE = _(
            "Batch conversion completed with {error_count} error(s)."
        )

    class Notifications:
        """Desktop notification titles and messages."""

        SUCCESS_TITLE = _("Conversion Complete")
        SUCCESS_MESSAGE = _("Successfully converted {filename} to {extension}")
        FAILURE_TITLE = _("Conversion Failed")
        FAILURE_MESSAGE = _("Failed to convert {filename} to {extension}")
        BATCH_SUCCESS_TITLE = _("Batch Conversion Complete")
        BATCH_SUCCESS_MESSAGE = _(
            "Successfully converted {successful} of {total} files to {extension}"
        )
        BATCH_FAILURE_TITLE = _("Batch Conversion Failed")
        BATCH_FAILURE_MESSAGE = _(
            "Failed to convert {failed} of {total} files to {extension}"
        )
        CONVERSION_STARTED_TITLE = _("Conversion Started")
        CONVERSION_STARTED_MESSAGE = _(
            "Conversion started for {filename} to {extension}"
        )
        BATCH_CONVERSION_STARTED_TITLE = _("Batch Conversion Started")
        BATCH_CONVERSION_STARTED_MESSAGE = _(
            "Batch conversion of {total} files to {extension} has started"
        )
        BATCH_STEP_CONVERSION_STARTED_TITLE = _("Batch Step Conversion Started")
        BATCH_STEP_CONVERSION_STARTED_MESSAGE = _(
            "Converting {filename} to {extension}"
        )
        BATCH_CONVERSION_CANCELLED_TITLE = _("Batch Conversion Cancelled")
        BATCH_CONVERSION_CANCELLED_MESSAGE = _(
            "Conversion cancelled after processing {completed} of {total} files to {extension}"
        )
        SINGLE_CONVERSION_CANCELLED_TITLE = _("Conversion Cancelled")
        SINGLE_CONVERSION_CANCELLED_MESSAGE = _(
            "File conversion to {extension} was cancelled"
        )
        USER_SETTINGS_CORRUPTED_TITLE = _("Settings Error")
        USER_SETTINGS_CORRUPTED_MESSAGE = _(
            "User settings file is corrupted\n"
            "(~/.config/convert-file@thigschuch/user_settings.json)\n"
            "Using default settings instead."
        )
        MISSING_TOOL_TITLE = _("Missing Conversion Tool")
        MISSING_TOOL_MESSAGE = _("Required tool '{tool}' is not installed.")


text = Text()
