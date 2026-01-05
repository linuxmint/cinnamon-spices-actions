#!/usr/bin/python3
"""
Base converter class for file conversion operations.

This module provides the base Converter class that handles all file conversions
using a template-based command building system.

Classes:
    Converter: Base class providing common conversion functionality,
              progress tracking, error handling, and subprocess management.
"""

import contextlib
import subprocess
from pathlib import Path
from typing import List, Optional

from converters.helpers import (
    ConversionManager,
    ErrorManager,
    FileManager,
    ProgressTracker,
    TemplateProcessor,
)
from ui import notification
from utils.logging import logger
from utils.validation import FileValidator


class Converter:
    """Base class for all file converters.

    Provides the common functionality needed by all converter types including
    subprocess management, progress tracking, error handling, and file validation.

    This class implements the core conversion workflow using template-based
    command building from user settings.

    Attributes:
        command: List of command arguments to execute for conversion.
        file: Input file path to be converted.
        format: Target format for conversion (uppercase).
        target_file: Output file path after conversion.
        batch_mode: Whether converter is running in batch mode.
        output_dir: Directory for output files in batch mode.
        timeout_ms: Timeout in milliseconds for conversion process.
        is_shell_command: Whether command requires shell execution.
        chained_commands: List of chained command arrays for multi-step conversions.
        file_manager: Handles file operations and temporary file management.
        error_manager: Manages error collection and user feedback.
        progress_tracker: Handles conversion progress and cancellation.
        conversion_manager: Orchestrates the conversion execution process.
        template_processor: Processes command templates from settings.

    Class Attributes:
        SHELL_BUILTINS: Set of shell builtin commands requiring shell execution.
    """

    SHELL_BUILTINS = {"cd", "export", "source", "alias"}

    notification = notification

    def __init__(
        self,
        file: Path,
        format: str,
        batch_mode: bool = False,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> None:
        """Initialize the converter with file and format information.

        Sets up all necessary managers and initializes the conversion environment.
        Creates the target file path and builds the initial conversion command.

        Args:
            file: Path to the input file to be converted.
            format: Target format for conversion (will be uppercased).
            batch_mode: Whether this conversion is part of a batch operation.
            output_dir: Optional output directory for batch conversions.
            **kwargs: Additional configuration options including:
                     - timeout_ms: Conversion timeout in milliseconds (default: 30000)
                     - cancel_check: Optional callable for cancellation checking

        Returns:
            None

        Note:
            The build_command() method is called automatically during initialization.
        """
        self.command: List[str] = []
        self.file: Path = file
        self.format: str = format.upper()
        self.batch_mode: bool = batch_mode
        self.output_dir: Optional[Path] = output_dir

        self.file_manager = FileManager(self.file, self.format, self.output_dir)
        self.error_manager = ErrorManager(self.batch_mode)
        self.progress_tracker = ProgressTracker(kwargs.get("cancel_check"))

        self.target_file: Path = self.file_manager.get_target_file()

        self.timeout_ms: int = kwargs.get("timeout_ms", 30000)  # 30 seconds default
        self._process: Optional[subprocess.Popen] = None

        self.template_processor = TemplateProcessor(
            self.get_converter_type(), self.format
        )
        self.conversion_manager = ConversionManager(
            batch_mode=self.batch_mode,
            external_cancel_check=self.progress_tracker._external_cancel_check,
        )

        self.is_shell_command: bool = False

        self.chained_commands: List[List[str]] = []

        self._chained_step: int = 0
        self._chained_started: bool = False
        self._chained_needs_shell: bool = False

        self.target_file = self.file_manager.ensure_unique_filename(self.target_file)

        self.build_command()

    def build_command(self) -> None:
        """Build the command for the conversion process.

        Uses the template system from settings to build conversion commands.
        This method attempts to load command templates from user settings,
        falling back to defaults when no custom template is configured.

        Returns:
            None
        """
        template_used = self.build_command_from_template()
        if not template_used and not self.command:
            logger.warning(
                "No command template found for {} conversion to {}",
                self.get_converter_type(),
                self.format,
            )

    def get_converter_type(self) -> str:
        """Get the converter type name for template loading.

        Determines the converter type based on the source file's format group
        or special conversion rules, used for loading appropriate command templates
        from settings. Handles compound extensions like .tar.bz2 properly.

        Returns:
            str: The converter type (e.g., 'audio', 'video', 'image', 'office', 'archive').

        Examples:
            >>> converter = Converter(Path("test.jpg"), "PNG")
            >>> converter.get_converter_type()
            'image'
        """
        from config import format_config
        source_format = FileValidator.get_file_format(self.file)

        rule = format_config.get_conversion_rule(source_format, self.format)
        if rule and rule.converter_type:
            return rule.converter_type.value

        converter_type = format_config.get_default_converter_type(
            source_format, self.format
        )
        if converter_type:
            return converter_type.value

        class_name = self.__class__.__name__.lower()
        return class_name.replace("converter", "")

    def build_command_from_template(self) -> bool:
        """Build command using template system.

        Attempts to build the conversion command using user-configured templates
        from settings. Passes source format for multi-file detection.

        Returns:
            bool: True if a template was used, False if no template was found.

        Note:
            Updates self.command, self.chained_commands, and related attributes
            based on the template results.
        """
        (
            self.command,
            template_used,
            self.chained_commands,
            self.is_shell_command,
            temp_manager,
        ) = self.template_processor.build_command_from_template(
            None, self.file, self.target_file
        )

        if temp_manager:
            self.file_manager.set_temp_manager(temp_manager)

        return template_used

    def convert(self) -> bool:
        """Execute the conversion process with progress tracking.

        Initiates the complete conversion workflow including tool validation,
        command execution, progress monitoring, and error handling.

        Returns:
            bool: True if conversion succeeded, False if it failed or was cancelled.

        Note:
            Handles all user interaction including progress dialogs and error messages.
            Automatically cleans up temporary files on completion.
        """
        logger.info("Starting conversion: {} -> {}", self.file, self.target_file)
        logger.debug(
            "Converter: {}, Batch mode: {}", self.__class__.__name__, self.batch_mode
        )
        try:
            self.progress_tracker.reset()

            validation_error = self.conversion_manager.validate_tools(
                self.command, self.chained_commands
            )
            if validation_error:
                logger.error("Tool validation failed: {}", validation_error)
                if self.chained_commands:
                    full_command_parts = []
                    for cmd in self.chained_commands:
                        if isinstance(cmd, list):
                            full_command_parts.append(" ".join(str(arg) for arg in cmd))
                        else:
                            full_command_parts.append(str(cmd))
                    command_str = " && ".join(full_command_parts)
                else:
                    command_str = (
                        " ".join(str(arg) for arg in self.command)
                        if self.command
                        else None
                    )

                logger.debug("Command that failed validation: {}", command_str)

                if self.batch_mode:
                    self.error_manager.set_error(validation_error, command_str)
                else:
                    missing_tool_name = "unknown_tool"
                    install_command = ""

                    if "Missing Tool:" in validation_error:
                        tool_line = (
                            validation_error.split("Missing Tool:")[1]
                            .split("\n")[0]
                            .strip()
                        )
                        missing_tool_name = tool_line
                        if "Install Command:" in validation_error:
                            install_command = validation_error.split(
                                "Install Command:\n"
                            )[1].split("\n\n")[0]
                    elif "Missing required tools:" in validation_error:
                        lines = validation_error.split("\n")
                        for line in lines:
                            if line.startswith("• "):
                                parts = line.split(": ", 1)
                                if len(parts) == 2:
                                    missing_tool_name = (
                                        parts[0].replace("• ", "").strip()
                                    )
                                    install_command = parts[1].strip()
                                break

                    self.conversion_manager.show_missing_tool_dialog(
                        missing_tool_name,
                        install_command,
                        self.batch_mode,
                        attempted_command=command_str,
                    )
                return False

            cancel_callback = self.progress_tracker.create_cancel_callback()

            logger.debug("Executing conversion command")
            result = self.conversion_manager.execute_conversion(
                self.command,
                self.chained_commands,
                self.is_shell_command,
                self.file.name,
                self.format,
                cancel_callback,
            )

            if result.success:
                logger.info("Conversion completed successfully")
                return True
            elif result.cancelled:
                logger.info("Conversion was cancelled by user")
                self.conversion_manager.handle_cancellation(self.format)
                self._delete_target_file()
                return False
            else:
                logger.error("Conversion failed")
                error_message = self.conversion_manager.handle_conversion_error(
                    result, self.file.name, self.format, self.batch_mode
                )
                existing_error = self.error_manager.get_last_error()
                if existing_error and existing_error != error_message:
                    error_message = existing_error
                command_str = (
                    " ".join(str(arg) for arg in self.command) if self.command else None
                )
                if self.batch_mode:
                    self.error_manager.set_error(error_message, command_str)
                else:
                    self.error_manager.set_error(error_message, command_str)
                    self._error_dialog(error_message)
                self._delete_target_file()
                return False

        finally:
            self._cleanup_temp_files()

    def valid_target_file(self) -> None:
        """Generate a valid unique target file name.

        Ensures the target file has a unique name by appending numbers
        if a file with the same name already exists (e.g., file_1.jpg, file_2.jpg).

        Returns:
            None

        Note:
            Modifies self.target_file in place to ensure uniqueness.
        """
        if not self.target_file.exists():
            return

        counter = 1
        original_stem = self.target_file.stem
        original_suffix = self.target_file.suffix
        parent_dir = self.target_file.parent

        while self.target_file.exists():
            new_name = f"{original_stem} ({counter}){original_suffix}"
            self.target_file = parent_dir / new_name
            counter += 1

    def _error_dialog(self, error_message: str = "") -> None:
        """Display an error dialog with conversion details.

        Shows a comprehensive error dialog including the source file,
        target format, executed command, and error details.

        Args:
            error_message: Additional error message to display.

        Returns:
            None
        """
        source_format = FileValidator.get_file_format(self.file)

        self.error_manager.show_error_dialog(
            error_message or "Conversion failed",
            self.file,
            source_format or "UNKNOWN",
            self.format,
            self.command,
            self.get_last_command(),
        )

    def _cleanup_temp_files(self) -> None:
        """Clean up any temporary files created during conversion.

        Removes temporary files and directories created by the file manager
        during the conversion process.

        Returns:
            None
        """
        self.file_manager.cleanup_temp_files()

    def _delete_target_file(self) -> None:
        """Delete the target file and temporary files if they exist.

        Removes the output file and any associated temporary files
        in case of conversion failure or cancellation.

        Returns:
            None
        """
        self.file_manager.delete_target_file(self.target_file, self.output_dir)

    def cancel(self) -> None:
        """Cancel the currently running conversion.

        Terminates any running conversion process and sets cancellation flags.
        Safe to call even if no conversion is currently running.

        Returns:
            None
        """
        self.progress_tracker.cancel()
        if self._process:
            with contextlib.suppress(Exception):
                self._process.kill()
                self._process.wait(timeout=1.0)

    def get_last_error(self) -> Optional[str]:
        """Get the last error message from the conversion process.

        Returns:
            Optional[str]: The last error message, or None if no error occurred.

        Note:
            Useful for debugging and error reporting after conversion.
        """
        return self.error_manager.get_last_error()

    def get_last_command(self) -> Optional[str]:
        """Get the last executed command string.

        Returns:
            Optional[str]: The command that was executed, or None if no command
                          was executed.

        Note:
            Useful for debugging and showing command details in error dialogs.
        """
        return self.error_manager.get_last_command()

    def __repr__(self) -> str:
        """String representation for debugging and logging.

        Returns:
            str: String representation showing the conversion operation.

        Examples:
            >>> converter = Converter(Path("input.jpg"), "PNG")
            >>> repr(converter)
            "Converter(input.jpg -> output.png)"
        """
        return f"{self.__class__.__name__}({self.file} -> {self.target_file})"
