#!/usr/bin/python3
"""
Error handling utilities for converters.

Provides common error handling patterns and utilities used across different
converter implementations.
"""

from typing import Callable, Optional

from utils import text


class ErrorHandler:
    """Handles error reporting and management for converters.

    Provides centralized error state management and dialog display logic
    for both single-file and batch conversion operations. Prevents duplicate
    error dialogs and maintains error history for debugging.

    Attributes:
        batch_mode: Whether operating in batch mode (affects dialog behavior).
        last_error: The most recent error message encountered.
        last_command: The command string associated with the last error.
        _dialog_shown: Internal flag to prevent duplicate error dialogs.

    Examples:
        >>> handler = ErrorHandler(batch_mode=False)
        >>> handler.set_error("Conversion failed", "ffmpeg -i input.mp4 output.mp3")
        >>> print(handler.last_error)
        Conversion failed
    """

    def __init__(self, batch_mode: bool = False) -> None:
        """Initialize the error handler.

        Args:
            batch_mode: Whether running in batch mode, which suppresses
                       individual error dialogs in favor of batch reporting.
        """
        self.batch_mode = batch_mode
        self.last_error: Optional[str] = None
        self.last_command: Optional[str] = None
        self._dialog_shown: bool = False

    def set_error(self, error: str, command: Optional[str] = None) -> None:
        """Set the current error state with message and optional command.

        Updates the error handler's state with the provided error information,
        storing both the error message and the command that caused it.

        Args:
            error: Error message describing what went wrong.
            command: The command string that caused the error (optional).

        Examples:
            >>> handler.set_error("File not found", "convert input.jpg output.png")
            >>> print(handler.last_error)
            File not found
        """
        self.last_error = error
        if command:
            self.last_command = command

    def show_error_if_needed(
        self, error: str, show_dialog_fn: Optional[Callable[[str], None]] = None
    ) -> None:
        """Show error dialog if appropriate for the current mode and state.

        Displays an error dialog only if not in batch mode and no dialog has
        been shown yet for this operation. This prevents duplicate dialogs
        during single-file conversions.

        Args:
            error: Error message to display in the dialog.
            show_dialog_fn: Callback function to display the error dialog.
                           Should accept a single string parameter.

        Examples:
            >>> def show_dialog(msg): print(f"Dialog: {msg}")
            >>> handler.show_error_if_needed("Command failed", show_dialog)
            Dialog: Command failed
        """
        if not self.batch_mode and not self._dialog_shown and show_dialog_fn:
            show_dialog_fn(error)
            self._dialog_shown = True
        self.last_error = error

    def handle_missing_tool(
        self,
        tool_name: str,
        show_dialog_fn: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Handle errors related to missing conversion tools.

        Formats and stores an error message for a missing tool dependency,
        and optionally displays an error dialog with installation guidance.

        Args:
            tool_name: Name of the tool that is not installed or available.
            show_dialog_fn: Optional callback to display the error dialog.

        Examples:
            >>> handler.handle_missing_tool("ffmpeg", lambda msg: print(msg))
            >>> print(handler.last_error)
            Tool 'ffmpeg' is not installed or not available in PATH.
        """
        error_msg = text.Errors.MISSING_TOOL_MESSAGE.format(tool=tool_name)
        self.set_error(error_msg, tool_name)
        self.show_error_if_needed(error_msg, show_dialog_fn)

    def handle_file_not_found(
        self,
        error: FileNotFoundError,
        show_dialog_fn: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Handle FileNotFoundError exceptions and extract tool information.

        Processes FileNotFoundError exceptions to identify missing tools,
        formats appropriate error messages, and optionally shows dialogs.

        Args:
            error: The FileNotFoundError exception that was raised.
            show_dialog_fn: Optional callback to display the error dialog.

        Returns:
            str: The name of the tool that was not found.

        Examples:
            >>> try:
            ...     subprocess.run(["nonexistent_tool"])
            ... except FileNotFoundError as e:
            ...     tool = handler.handle_file_not_found(e)
            ...     print(f"Missing tool: {tool}")
            Missing tool: nonexistent_tool
        """
        tool_name = str(error).split("'")[1] if "'" in str(error) else "unknown"
        self.handle_missing_tool(tool_name, show_dialog_fn)
        return tool_name
