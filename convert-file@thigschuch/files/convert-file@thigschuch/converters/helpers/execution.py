#!/usr/bin/python3
"""
Command execution manager for converters.

This module provides a centralized command execution system that handles
progress tracking, cancellation, and different execution modes.
"""

import contextlib
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional, Union

from ui import Gtk, ProgressbarDialogWindow
from utils import text
from utils.logging import logger

from .constants import SHELL_OPERATORS


class CommandExecutionResult:
    """Result of command execution with metadata.

    Encapsulates the outcome of a command execution, including success status,
    error messages, the command that was run, and cancellation state.

    Attributes:
        success: Whether the command executed successfully.
        error_message: Error message if execution failed.
        command: The command string that was executed.
        cancelled: Whether the execution was cancelled by the user.

    Examples:
        >>> result = CommandExecutionResult(
        ...     success=True,
        ...     command="ffmpeg -i input.mp4 output.mp3"
        ... )
        >>> print(result.success)
        True
    """

    def __init__(
        self,
        success: bool,
        error_message: Optional[str] = None,
        command: Optional[str] = None,
        cancelled: bool = False,
    ):
        """Initialize command execution result.

        Args:
            success: True if the command completed successfully.
            error_message: Error message if the command failed.
            command: The command string that was executed.
            cancelled: True if the execution was cancelled.
        """
        self.success = success
        self.error_message = error_message
        self.command = command
        self.cancelled = cancelled


class SubprocessResult:
    """Result of subprocess execution with captured output.

    Contains the complete result of a subprocess execution, including return code,
    stdout, stderr, and the command that was run.

    Attributes:
        returncode: The process return code (0 for success).
        stdout: Standard output captured from the process.
        stderr: Standard error captured from the process.
        command: The command string that was executed.
        success: Boolean indicating if the process succeeded (returncode == 0).

    Examples:
        >>> result = SubprocessResult(
        ...     returncode=0,
        ...     stdout="Conversion complete",
        ...     command="ffmpeg -version"
        ... )
        >>> print(result.success)
        True
    """

    def __init__(
        self,
        returncode: int,
        stdout: str = "",
        stderr: str = "",
        command: str = "",
    ):
        """Initialize subprocess result.

        Args:
            returncode: The exit code from the subprocess.
            stdout: Captured standard output.
            stderr: Captured standard error.
            command: The command that was executed.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.command = command
        self.success = returncode == 0

    @property
    def error_output(self) -> str:
        """Get error output, preferring stderr but falling back to stdout.

        Returns the most relevant error output for user display. If stderr
        is empty, falls back to stdout. If both are empty, returns a generic
        failure message.

        Returns:
            str: The error output string for display.

        Examples:
            >>> result = SubprocessResult(1, "", "ffmpeg: command not found")
            >>> print(result.error_output)
            ffmpeg: command not found
        """
        return self.stderr or self.stdout or text.Operations.FAILED_MESSAGE


class CommandExecutor:
    """Manages command execution with progress tracking and cancellation support.

    Handles the complexity of executing commands (regular, chained, shell)
    while providing progress feedback and proper cancellation handling.
    Supports both single commands and multi-step chained operations.

    Attributes:
        cancel_check: Optional callback to check for cancellation requests.
        batch_mode: Whether operating in batch mode (affects progress display).
        _cancelled: Internal flag tracking cancellation state.

    Examples:
        >>> def cancel_check(): return False
        >>> executor = CommandExecutor(cancel_check=cancel_check, batch_mode=False)
        >>> result = executor.execute_single_command(["echo", "hello"])
        >>> print(result.success)
        True
    """

    def __init__(
        self,
        cancel_check: Optional[Callable[[], bool]] = None,
        batch_mode: bool = False,
    ):
        """Initialize the command executor.

        Args:
            cancel_check: Optional callback function that returns True if
                         the operation should be cancelled.
            batch_mode: Whether operating in batch mode, affecting progress
                       display behavior.
        """
        self.cancel_check = cancel_check
        self.batch_mode = batch_mode
        self._cancelled = False

    def execute_single_command(
        self,
        command: Union[str, List[str]],
        shell: bool = False,
    ) -> CommandExecutionResult:
        """Execute a single command with progress tracking and cancellation.

        Runs a single command (either as a string for shell execution or as
        a list for direct execution) with support for cancellation and error
        handling.

        Args:
            command: Command to execute, either as a string (for shell) or
                    list of arguments (for direct execution).
            shell: Whether to use shell execution mode.

        Returns:
            CommandExecutionResult: Result object containing success status,
                                  error message, command string, and cancellation
                                  state.

        Examples:
            >>> result = executor.execute_single_command(["ls", "-la"])
            >>> if not result.success:
            ...     print(f"Error: {result.error_message}")
        """
        logger.debug("Executing single command: {}, shell: {}", command, shell)
        if self._is_cancelled():
            logger.info("Command execution cancelled before start")
            return CommandExecutionResult(
                success=False, cancelled=True, error_message="Operation cancelled"
            )

        result = self.run_cancellable_command(
            command, shell=shell, cancel_check=self._is_cancelled
        )

        error_message = None if result.success else result.error_output
        logger.debug(
            "Command execution result: success={}, cancelled={}",
            result.success,
            self._cancelled,
        )

        return CommandExecutionResult(
            success=result.success,
            error_message=error_message,
            command=result.command,
            cancelled=self._cancelled,
        )

    def execute_chained_commands(
        self,
        commands: List[List[str]],
        shell_builtins: Optional[set] = None,
        progress_callback: Optional[Callable] = None,
    ) -> CommandExecutionResult:
        """Execute multiple commands sequentially as a chained operation.

        Runs a series of commands in sequence, handling both shell-based
        chained commands (using && operators) and regular sequential execution.
        Provides progress tracking for multi-step operations.

        Args:
            commands: List of command lists to execute in sequence.
            shell_builtins: Set of shell builtin commands that require shell
                           execution mode.
            progress_callback: Optional callback for progress updates during
                              multi-step execution.

        Returns:
            CommandExecutionResult: Result of the chained execution, with
                                  success status and error details.

        Examples:
            >>> commands = [["echo", "step 1"], ["echo", "step 2"]]
            >>> result = executor.execute_chained_commands(commands)
            >>> print(f"Steps completed: {result.success}")
        """
        if not commands:
            return CommandExecutionResult(
                success=False, error_message="No commands to execute"
            )

        if self._is_cancelled():
            return CommandExecutionResult(
                success=False, cancelled=True, error_message="Operation cancelled"
            )

        shell_builtins = shell_builtins or set()
        needs_shell = any(
            (cmd[0] in shell_builtins if cmd else False)
            or (len(cmd) > 1 and any(op in cmd[1] for op in SHELL_OPERATORS))
            for cmd in commands
        )

        if needs_shell:
            return self._execute_shell_chained_commands(commands)
        else:
            return self._execute_regular_chained_commands(commands, progress_callback)

    def _execute_shell_chained_commands(
        self, commands: List[List[str]]
    ) -> CommandExecutionResult:
        """Execute chained commands as a single shell command with && operators.

        Combines multiple commands into a single shell command string joined
        with && operators, executing them as one atomic operation.

        Args:
            commands: List of command lists to combine and execute.

        Returns:
            CommandExecutionResult: Result of the shell chained execution.
        """
        import shlex

        command_parts = []
        for cmd in commands:
            if len(cmd) == 2 and any(op in cmd[1] for op in SHELL_OPERATORS):
                command_parts.append(cmd[1])
            else:
                command_parts.append(shlex.join(cmd))

        command_str = " && ".join(command_parts)

        result = self.run_cancellable_command(
            command_str, shell=True, cancel_check=self._is_cancelled
        )

        error_message = None if result.success else result.error_output

        return CommandExecutionResult(
            success=result.success,
            error_message=error_message,
            command=result.command,
            cancelled=self._cancelled,
        )

    def _execute_regular_chained_commands(
        self, commands: List[List[str]], progress_callback: Optional[Callable]
    ) -> CommandExecutionResult:
        """Execute chained commands step by step with individual progress tracking.

        Runs each command in sequence, stopping at the first failure and
        providing detailed progress feedback for each step.

        Args:
            commands: List of command lists to execute sequentially.
            progress_callback: Optional callback for step-by-step progress updates.

        Returns:
            CommandExecutionResult: Result of the sequential execution.
        """
        total_steps = len(commands)
        previous_result = None

        for step_index, cmd in enumerate(commands):
            if self._is_cancelled():
                return CommandExecutionResult(
                    success=False, cancelled=True, error_message="Operation cancelled"
                )

            if progress_callback:
                progress_callback(
                    step_index, total_steps, f"Step {step_index + 1}/{total_steps}"
                )

            result = self.run_cancellable_command(
                cmd, shell=False, cancel_check=self._is_cancelled
            )

            if not result.success:
                is_validation_step = (
                    len(cmd) >= 3 and cmd[0] == "test" and cmd[1] == "-f"
                )

                if is_validation_step and previous_result:
                    validated_file = cmd[2] if len(cmd) > 2 else "output file"
                    error_msg = text.Operations.FILE_VALIDATION_FAILED_MESSAGE.format(
                        file=validated_file,
                        previous_error=previous_result.error_output or "",
                    )
                else:
                    error_msg = (
                        text.Operations.CHAINED_COMMAND_STEP_FAILED_MESSAGE.format(
                            step=step_index + 1,
                            total=total_steps,
                            error=result.error_output,
                            command=" ".join(cmd),
                        )
                    )

                return CommandExecutionResult(
                    success=False,
                    error_message=error_msg,
                    command=result.command,
                )

            previous_result = result

        return CommandExecutionResult(success=True)

    @staticmethod
    def run_cancellable_command(
        command: Union[str, List[str]],
        shell: bool = False,
        cwd: Optional[Path] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        poll_interval: float = 0.05,
    ) -> SubprocessResult:
        """Run a command with cancellation support and output capture.

        Executes a subprocess with the ability to cancel mid-execution,
        capturing both stdout and stderr for error reporting.

        Args:
            command: Command to run, either as string (shell mode) or list
                    (direct execution).
            shell: Whether to execute in shell mode.
            cwd: Optional working directory for the command.
            cancel_check: Callback function that returns True to cancel.
            poll_interval: Time interval between cancellation checks.

        Returns:
            SubprocessResult: Complete result including return code, outputs,
                            and command string.

        Examples:
            >>> result = CommandExecutor.run_cancellable_command(
            ...     ["echo", "hello"],
            ...     cancel_check=lambda: False
            ... )
            >>> print(result.stdout.strip())
            hello
        """
        if isinstance(command, str):
            cmd_str = command
        elif len(command) == 2 and isinstance(command[1], str) and shell:
            cmd_str = command[1]
        else:
            cmd_str = " ".join(command)

        logger.debug(
            "Running cancellable command: {}, shell: {}, cwd: {}", cmd_str, shell, cwd
        )

        if cancel_check and cancel_check():
            logger.info("Command cancelled before execution")
            return SubprocessResult(
                returncode=-1,
                stderr=text.Operations.CANCELLED_BY_USER_MESSAGE,
                command=cmd_str,
            )

        try:
            logger.debug("Starting subprocess")
            process = subprocess.Popen(
                command,
                shell=shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(cwd) if cwd else None,
            )

            while process.poll() is None:
                for _ in range(5):
                    if cancel_check and cancel_check():
                        logger.info("Command cancelled during execution")
                        with contextlib.suppress(Exception):
                            process.kill()
                        return SubprocessResult(
                            returncode=-1,
                            stderr=text.Operations.CANCELLED_BY_USER_MESSAGE,
                            command=cmd_str,
                        )
                    time.sleep(
                        poll_interval / 5
                    )

            stdout, stderr = process.communicate()
            logger.debug("Command completed with return code: {}", process.returncode)

            return SubprocessResult(
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                command=cmd_str,
            )

        except Exception as e:
            logger.error("Exception during command execution: {}", str(e))
            return SubprocessResult(
                returncode=-1,
                stderr=str(e),
                command=cmd_str,
            )

    def _is_cancelled(self) -> bool:
        """Check if the current operation has been cancelled.

        Internal method that checks both internal cancellation state and
        external cancellation callback.

        Returns:
            bool: True if the operation should be cancelled.
        """
        if self._cancelled:
            return True
        if self.cancel_check and self.cancel_check():
            self._cancelled = True
            return True
        return False


class ProgressManager:
    """Manages progress dialogs and execution with UI feedback.

    Handles the complexity of progress dialog management, GTK event processing,
    and coordination between background execution and UI updates. Provides
    cancellation support and proper cleanup.

    Attributes:
        batch_mode: Whether operating in batch mode (no UI dialogs).
        _progress_window: The GTK progress dialog window.
        _cancelled: Internal cancellation flag.
        _cancelling: Flag indicating cancellation is in progress.
        _cancel_callback: Callback to execute on cancellation.
        _cancelling_timeout_counter: Counter for cancellation timeout.
        _max_cancelling_timeouts: Maximum timeouts before forced cleanup.

    Examples:
        >>> manager = ProgressManager(batch_mode=False)
        >>> def execution(): return CommandExecutionResult(success=True)
        >>> result = manager.execute_with_progress(
        ...     execution, "Converting file..."
        ... )
    """

    def __init__(
        self, batch_mode: bool = False, cancel_callback: Optional[Callable] = None
    ):
        """Initialize the progress manager.

        Args:
            batch_mode: Whether to operate in batch mode without UI dialogs.
            cancel_callback: Optional callback to execute when cancelled.
        """
        self.batch_mode = batch_mode
        self._progress_window: Optional[ProgressbarDialogWindow] = None
        self._cancelled = False
        self._cancelling = False
        self._cancel_callback = cancel_callback
        self._cancelling_timeout_counter = 0
        self._max_cancelling_timeouts = 50

    def execute_with_progress(
        self,
        execution_func: Callable[[], CommandExecutionResult],
        message: str,
        timeout_callback: Optional[Callable] = None,
        timeout_ms: int = 100,
    ) -> CommandExecutionResult:
        """Execute a function with progress dialog and UI feedback.

        Runs the provided execution function in a background thread while
        showing a progress dialog to the user. Handles cancellation and
        proper cleanup.

        Args:
            execution_func: Function to execute in the background.
            message: Progress message to display in the dialog.
            timeout_callback: Optional progress update callback.
            timeout_ms: Milliseconds between progress updates.

        Returns:
            CommandExecutionResult: Result of the background execution.

        Examples:
            >>> def convert_file():
            ...     # Long-running conversion
            ...     return CommandExecutionResult(success=True)
            >>> result = manager.execute_with_progress(
            ...     convert_file, "Converting video.mp4..."
            ... )
        """
        if self.batch_mode:
            return execution_func()

        self._progress_window = ProgressbarDialogWindow(
            message=message,
            timeout_callback=self._make_progress_callback(timeout_callback),
            timeout_ms=timeout_ms,
        )

        def on_response(dialog, response_id) -> None:
            if response_id in (Gtk.ResponseType.CANCEL, Gtk.ResponseType.DELETE_EVENT):
                self._cancelled = True
                self._cancelling = True
                if self._cancel_callback:
                    self._cancel_callback()

                self._handle_cancellation_ui()

        self._progress_window.dialog.connect("response", on_response)

        def on_delete_event(dialog, event) -> bool:
            self._cancelled = True
            self._cancelling = True
            if self._cancel_callback:
                self._cancel_callback()
            self._handle_cancellation_ui()
            return False

        self._progress_window.dialog.connect("delete-event", on_delete_event)
        self._progress_window.progressbar.set_pulse_step(0.1)

        self._execution_result = None
        self._execution_thread = None
        self._execution_started = False

        def run_execution() -> None:
            try:
                self._execution_result = execution_func()
            except Exception as e:
                self._execution_result = CommandExecutionResult(
                    success=False,
                    error_message=str(e),
                )

        self._execution_thread = threading.Thread(target=run_execution, daemon=True)
        self._execution_thread.start()

        response = self._progress_window.run()
        self._progress_window.destroy()

        if (
            response in (Gtk.ResponseType.CANCEL, Gtk.ResponseType.DELETE_EVENT)
            or self._cancelled
        ):
            return CommandExecutionResult(
                success=False,
                cancelled=True,
                error_message="Operation cancelled by user",
            )

        return self._execution_result or CommandExecutionResult(success=False)

    def _handle_cancellation_ui(self) -> None:
        """Update UI to show cancellation is in progress.

        Changes the cancel button text and disables it to indicate
        that cancellation is being processed.
        """
        if not self._progress_window:
            return

        action_area = self._progress_window.dialog.get_action_area()
        if action_area:
            buttons = action_area.get_children()
            for button in buttons:
                if isinstance(button, Gtk.Button):
                    label = button.get_label()
                    if label == text.UI.CANCEL_BUTTON_LABEL:
                        button.set_label(text.UI.CANCELLING_BUTTON_LABEL)
                        button.set_sensitive(False)
                        break

        while Gtk.events_pending():
            Gtk.main_iteration()

    def _force_cancellation_cleanup(self) -> None:
        """Force cleanup when cancellation times out.

        Performs emergency cleanup when cancellation takes too long,
        abandoning the execution thread and relying on converter cleanup.
        """
        pass

    def _final_cancellation_cleanup(self) -> None:
        """Final cleanup when thread finishes normally during cancellation.

        Performs cleanup when the execution thread completes during
        the cancellation process.
        """
        pass

    def _make_progress_callback(self, user_callback: Optional[Callable]) -> Callable:
        """Create progress callback that handles cancellation and completion checking.

        Returns a callback function that manages progress updates, cancellation
        detection, and dialog lifecycle.

        Args:
            user_callback: Optional user-provided progress callback.

        Returns:
            Callable: Progress callback function for GTK timeout.
        """

        def progress_callback(*args, **kwargs) -> bool:
            if self._cancelling:
                if self._execution_thread and self._execution_thread.is_alive():
                    self._cancelling_timeout_counter += 1

                    if (
                        self._cancelling_timeout_counter
                        >= self._max_cancelling_timeouts
                    ):
                        self._force_cancellation_cleanup()
                        if self._progress_window:
                            self._progress_window.dialog.emit(
                                "response", Gtk.ResponseType.CANCEL
                            )
                        return False

                    if self._progress_window:
                        self._progress_window.progressbar.pulse()
                    return True
                else:
                    self._final_cancellation_cleanup()
                    if self._progress_window:
                        self._progress_window.dialog.emit(
                            "response", Gtk.ResponseType.CANCEL
                        )
                    return False

            if self._cancelled:
                return False

            while Gtk.events_pending():
                Gtk.main_iteration()

            if self._execution_thread and self._execution_thread.is_alive():
                if self._progress_window:
                    self._progress_window.progressbar.pulse()
                return True
            elif self._execution_result is not None:
                if self._progress_window:
                    self._progress_window.dialog.emit("response", Gtk.ResponseType.OK)
                return False

            if user_callback:
                return user_callback(*args, **kwargs)

            if self._progress_window:
                self._progress_window.progressbar.pulse()
            return True

        return progress_callback
