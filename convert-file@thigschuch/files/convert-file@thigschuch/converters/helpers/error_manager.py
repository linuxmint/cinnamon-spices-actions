#!/usr/bin/python3
"""
Error management utilities for converters.

This module provides centralized error handling and dialog management
for converter operations.
"""

from pathlib import Path
from typing import Optional

from converters.helpers.errors import ErrorHandler
from ui import ErrorDialogWindow
from utils import text


class ErrorManager:
    """Manages error handling and dialog display for converters.

    Provides consistent error formatting and dialog creation across
    different converter implementations. Handles both single-file and
    batch conversion error scenarios with appropriate user feedback.

    Attributes:
        batch_mode: Whether operating in batch mode for multiple files.
        error_handler: Underlying ErrorHandler instance for error storage.

    Examples:
        >>> manager = ErrorManager(batch_mode=False)
        >>> manager.show_error_dialog(
        ...     "Command failed",
        ...     Path("/tmp/input.mp4"),
        ...     "MP4",
        ...     "MP3",
        ...     command=["ffmpeg", "-i", "input.mp4", "output.mp3"]
        ... )
    """

    def __init__(self, batch_mode: bool = False) -> None:
        """Initialize the error manager.

        Args:
            batch_mode: Whether this manager operates in batch mode,
                       affecting error display behavior.
        """
        self.batch_mode = batch_mode
        self.error_handler = ErrorHandler(batch_mode)

    def set_error(self, error_message: str, command: Optional[str] = None) -> None:
        """Set an error message for batch mode error collection.

        Stores error information for later retrieval in batch operations,
        allowing multiple errors to be accumulated and displayed together.

        Args:
            error_message: The error message describing what went wrong.
            command: The command string that failed (optional).

        Examples:
            >>> manager = ErrorManager(batch_mode=True)
            >>> manager.set_error("File not found", "ffmpeg -i missing.mp4 output.mp3")
        """
        self.error_handler.set_error(error_message, command)

    def show_error_dialog(
        self,
        error_message: str,
        source_file: Path,
        source_format: str,
        target_format: str,
        command: Optional[list] = None,
        last_command: Optional[str] = None,
    ) -> None:
        """Show an error dialog with formatted error details.

        Displays a user-friendly error dialog containing conversion details,
        error message, and the command that failed. In batch mode, errors
        are stored instead of immediately displayed.

        Args:
            error_message: The primary error message describing the failure.
            source_file: Path to the source file that was being converted.
            source_format: The source file format (e.g., "MP4").
            target_format: The target format being converted to (e.g., "MP3").
            command: The command list that was executed (optional).
            last_command: Alternative command string if command list unavailable.

        Examples:
            >>> manager.show_error_dialog(
            ...     "Conversion failed: invalid format",
            ...     Path("/home/user/video.mp4"),
            ...     "MP4",
            ...     "AVI",
            ...     command=["ffmpeg", "-i", "video.mp4", "output.avi"]
            ... )
        """
        if self.batch_mode:
            self.error_handler.set_error(
                error_message or "Conversion failed",
                last_command
                or (" ".join(str(arg) for arg in command) if command else None),
            )
            return

        error_details = self._format_error_details(
            error_message,
            source_file,
            source_format,
            target_format,
            command,
            last_command,
        )

        ErrorDialogWindow(
            message=text.Conversion.ERROR_MESSAGE,
            error_details=error_details,
        ).run()

    def _format_error_details(
        self,
        error_message: str,
        source_file: Path,
        source_format: str,
        target_format: str,
        command: Optional[list] = None,
        last_command: Optional[str] = None,
    ) -> str:
        """Format error details for display in error dialogs.

        Creates a comprehensive error details string including file information,
        conversion attempt details, and the command that was executed.

        Args:
            error_message: The primary error message.
            source_file: Path to the source file.
            source_format: Source format extension.
            target_format: Target format extension.
            command: Command list that was executed.
            last_command: Alternative command string.

        Returns:
            str: Formatted error details string for dialog display.

        Examples:
            >>> details = manager._format_error_details(
            ...     "Command not found",
            ...     Path("/tmp/test.mp4"),
            ...     "MP4",
            ...     "MP3",
            ...     command=["ffmpeg", "-i", "test.mp4", "output.mp3"]
            ... )
            >>> print(details)
            File: test.mp4
            Conversion: MP4 → MP3
            Error: Command not found
            <BLANKLINE>
            Command:
            ffmpeg -i test.mp4 output.mp3
        """
        error_details = (
            f"File: {source_file.name}\n"
            f"Conversion: {source_format} → {target_format}\n"
            f"Error: {error_message or text.Conversion.FAILED_CHECK_TOOLS_MESSAGE}"
        )

        command_str = last_command
        if not command_str and command:
            if len(command) == 2 and isinstance(command[1], str):
                if command[1].startswith(command[0]):
                    command_str = command[1]
                else:
                    command_str = " ".join(str(arg) for arg in command)
            else:
                command_str = " ".join(str(arg) for arg in command)
        
        if command_str:
            error_details += f"\n\nCommand:\n{command_str}"

        return error_details

    def get_last_error(self) -> Optional[str]:
        """Get the last error message from the error handler.

        Returns:
            Optional[str]: The last error message, or None if no specific
                          error was recorded.

        Examples:
            >>> manager.set_error("File corrupted")
            >>> error = manager.get_last_error()
            >>> print(error)
            File corrupted
        """
        error = self.error_handler.last_error
        if error and error.strip():
            return error
        return None

    def get_last_command(self) -> Optional[str]:
        """Get the last executed command string.

        Returns:
            Optional[str]: The command string that was last executed,
                          or None if no command was recorded.

        Examples:
            >>> manager.set_error("Command failed", "ffmpeg -i input.mp4 output.mp3")
            >>> cmd = manager.get_last_command()
            >>> print(cmd)
            ffmpeg -i input.mp4 output.mp3
        """
        return self.error_handler.last_command
