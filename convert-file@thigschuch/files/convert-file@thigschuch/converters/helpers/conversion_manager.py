#!/usr/bin/python3
"""
Conversion execution manager for converters.

This module provides centralized command execution and progress tracking
functionality extracted from the base converter.
"""

from typing import Callable, List, Optional

from converters.helpers.execution import (
    CommandExecutionResult,
    CommandExecutor,
    ProgressManager,
)
from ui import ErrorDialogWindow, notification
from utils import dependency_manager, text

from .commands import CommandParser
from .constants import SHELL_OPERATORS


class ConversionManager:
    """Manages the execution of conversion commands with progress tracking.

    This class encapsulates the complex conversion execution logic previously
    in the Converter.convert() method, providing clean separation of concerns.
    It handles command validation, progress tracking, cancellation, and error
    handling for both single and batch conversion operations.

    Attributes:
        SHELL_BUILTINS: Set of shell builtin commands that require shell execution.
        batch_mode: Whether this manager is operating in batch mode.
        external_cancel_check: Optional external callback for cancellation checks.
        notification: Notification service for user feedback.

    Examples:
        >>> manager = ConversionManager(batch_mode=False)
        >>> result = manager.execute_conversion(
        ...     command=["ffmpeg", "-i", "input.mp4", "output.mp3"],
        ...     chained_commands=[],
        ...     is_shell_command=False,
        ...     input_file_name="video.mp4",
        ...     target_format="MP3"
        ... )
    """

    SHELL_BUILTINS = {"cd", "export", "source", "alias"}

    def __init__(
        self,
        batch_mode: bool = False,
        external_cancel_check: Optional[Callable[[], bool]] = None,
    ):
        """Initialize the conversion manager.

        Args:
            batch_mode: Whether this manager operates in batch mode for
                       multiple file conversions.
            external_cancel_check: Optional callback function that returns
                                 True if conversion should be cancelled.
        """
        self.batch_mode = batch_mode
        self.external_cancel_check = external_cancel_check
        self.notification = notification

    def execute_conversion(
        self,
        command: List[str],
        chained_commands: List[List[str]],
        is_shell_command: bool,
        input_file_name: str,
        target_format: str,
        cancel_callback: Optional[Callable[[], None]] = None,
    ) -> CommandExecutionResult:
        """Execute the conversion with progress tracking and error handling.

        Orchestrates the complete conversion process including command execution,
        progress monitoring, cancellation handling, and result reporting.

        Args:
            command: Main command to execute as a list of strings.
            chained_commands: List of additional chained commands if any.
            is_shell_command: Whether the main command requires shell execution.
            input_file_name: Name of the input file for progress messages.
            target_format: Target format extension for progress messages.
            cancel_callback: Optional callback to execute on cancellation.

        Returns:
            CommandExecutionResult: Result object containing success status,
                                  error message (if any), and cancellation flag.

        Raises:
            Exception: Propagates any unexpected execution errors.
        """
        try:
            cancellation_state = {"cancelled": False}

            def internal_cancel_callback() -> None:
                cancellation_state["cancelled"] = True
                if cancel_callback:
                    cancel_callback()

            def cancel_check() -> bool:
                if cancellation_state["cancelled"]:
                    return True
                if self.external_cancel_check and self.external_cancel_check():
                    return True
                return False

            executor = CommandExecutor(
                cancel_check=cancel_check, batch_mode=self.batch_mode
            )

            progress_manager = ProgressManager(
                batch_mode=self.batch_mode, cancel_callback=internal_cancel_callback
            )

            result = self._perform_conversion_execution(
                executor,
                progress_manager,
                command,
                chained_commands,
                is_shell_command,
                input_file_name,
                target_format,
            )

            return result

        except Exception as e:
            return CommandExecutionResult(
                success=False,
                error_message=f"Conversion execution failed: {str(e)}",
                cancelled=False,
            )

    def _perform_conversion_execution(
        self,
        executor: CommandExecutor,
        progress_manager: ProgressManager,
        command: List[str],
        chained_commands: List[List[str]],
        is_shell_command: bool,
        input_file_name: str,
        target_format: str,
    ) -> CommandExecutionResult:
        """Perform the actual conversion execution with progress tracking.

        Internal method that handles the core execution logic, determining
        whether to execute single or chained commands and managing progress
        display.

        Args:
            executor: CommandExecutor instance for running commands.
            progress_manager: ProgressManager for UI feedback.
            command: Main command to execute.
            chained_commands: Additional chained commands.
            is_shell_command: Whether shell execution is required.
            input_file_name: Input filename for progress messages.
            target_format: Target format for progress messages.

        Returns:
            CommandExecutionResult: Execution result with success/error details.
        """
        message = text.UI.CONVERSION_PROGRESS_LABEL.format(
            file=input_file_name, extension=target_format
        )

        def execution_func() -> CommandExecutionResult:
            if chained_commands:
                return executor.execute_chained_commands(
                    chained_commands, self.SHELL_BUILTINS
                )
            shell = is_shell_command
            if shell and len(command) > 1:
                command_str = command[1]
            elif isinstance(command, list):
                command_str = command
            else:
                command_str = str(command)
            return executor.execute_single_command(command_str, shell=shell)

        return progress_manager.execute_with_progress(
            execution_func, message, timeout_ms=100
        )

    def validate_tools(
        self,
        command: List[str],
        chained_commands: List[List[str]],
    ) -> Optional[str]:
        """Validate that all required tools are available for command execution.

        Checks both main and chained commands for required tools, ensuring
        all dependencies are installed before attempting conversion.

        Args:
            command: Main command list to validate.
            chained_commands: List of chained command lists to validate.

        Returns:
            Optional[str]: Error message if any required tools are missing,
                          None if all tools are available.

        Examples:
            >>> manager = ConversionManager()
            >>> error = manager.validate_tools(
            ...     ["ffmpeg", "-i", "input.mp4", "output.mp3"],
            ...     []
            ... )
            >>> if error:
            ...     print(f"Missing tool: {error}")
        """
        missing_tools = []

        def check_tool(tool_name: str):
            if tool_name in self.SHELL_BUILTINS:
                return
            install_command = dependency_manager.get_install_instructions(tool_name)
            if install_command:
                missing_tools.append((tool_name, install_command))

        if command:
            if len(command) == 1 and CommandParser.is_shell_command(command[0]):
                tools = CommandParser.extract_tools_from_shell(command[0])
                for tool in tools:
                    check_tool(tool)
            elif len(command) == 2 and any(op in command[1] for op in SHELL_OPERATORS):
                tools = CommandParser.extract_tools_from_shell(command[1])
                for tool in tools:
                    check_tool(tool)
            else:
                tool_name = command[0]
                check_tool(tool_name)

        if chained_commands:
            for cmd in chained_commands:
                if not cmd:
                    continue
                if len(cmd) == 2 and any(op in cmd[1] for op in SHELL_OPERATORS):
                    tools = CommandParser.extract_tools_from_shell(cmd[1])
                    for tool in tools:
                        check_tool(tool)
                else:
                    tool_name = cmd[0]
                    check_tool(tool_name)

        if missing_tools:
            if len(missing_tools) == 1:
                tool_name, install_command = missing_tools[0]
                return self._format_missing_tool_error(tool_name, install_command)
            else:
                error_parts = ["Missing required tools:"]
                for tool_name, install_command in missing_tools:
                    error_parts.append(f"• {tool_name}: {install_command}")
                return "\n".join(error_parts)

        return None

    def _format_missing_tool_error(self, tool_name: str, install_command: str) -> str:
        """Format error message for a missing tool dependency.

        Args:
            tool_name: Name of the missing tool.
            install_command: Installation command for the tool.

        Returns:
            str: Formatted error message with installation instructions.
        """
        return text.Errors.MISSING_TOOL_ERROR_DETAILS.format(
            tool=tool_name, install_command=install_command
        )

    def handle_cancellation(self, target_format: str) -> None:
        """Handle conversion cancellation with user notification.

        Args:
            target_format: The target format that was being converted to.
        """
        self.notification.notify_cancelled_conversion(target_format)

    def handle_conversion_error(
        self,
        result: CommandExecutionResult,
        input_file_name: str,
        target_format: str,
        batch_mode: bool = False,
    ) -> str:
        """Handle conversion error and return formatted error message.

        Processes execution failures, sends appropriate notifications,
        and formats error messages for user display.

        Args:
            result: Execution result containing error details.
            input_file_name: Name of the input file that failed.
            target_format: Target format that was being converted to.
            batch_mode: Whether running in batch mode (affects notifications).

        Returns:
            str: Formatted error message for further processing or display.

        Examples:
            >>> result = CommandExecutionResult(success=False, error_message="Command failed")
            >>> error_msg = manager.handle_conversion_error(
            ...     result, "input.mp4", "MP3", batch_mode=False
            ... )
        """
        if not batch_mode:
            self.notification.notify_conversion_failure(
                file_name=input_file_name, extension=target_format
            )

        error_message = result.error_message or "Conversion failed"
        return error_message

    def show_missing_tool_dialog(
        self,
        tool_name: str,
        install_command: str,
        batch_mode: bool = False,
        attempted_command: Optional[str] = None,
    ) -> None:
        """Show dialog for missing tool dependency with installation instructions.

        Displays a user-friendly dialog explaining the missing dependency
        and providing installation commands.

        Args:
            tool_name: Name of the missing tool.
            install_command: Command to install the missing tool.
            batch_mode: Whether in batch mode (affects dialog behavior).
            attempted_command: Optional command that would be executed.

        Examples:
            >>> manager.show_missing_tool_dialog(
            ...     "ffmpeg",
            ...     "sudo apt install ffmpeg",
            ...     attempted_command="ffmpeg -i input.mp4 output.mp3"
            ... )
        """
        if batch_mode:
            return

        self.notification.notify_missing_dependency(tool_name)

        main_message = text.Errors.MISSING_TOOL_MAIN_MESSAGE.format(tool=tool_name)
        error_details = text.Errors.MISSING_TOOL_ERROR_DETAILS.format(
            tool=tool_name, install_command=install_command
        )

        if attempted_command:
            error_details += f"\n\nCommand that would be executed:\n{attempted_command}"

        ErrorDialogWindow(
            message=main_message,
            error_details=error_details,
            copy_content=install_command,
            copy_button_label=text.UI.COPY_COMMAND_BUTTON_LABEL,
            copy_confirmation_message=text.UI.INSTALL_COMMAND_COPIED_MESSAGE,
        ).run()
