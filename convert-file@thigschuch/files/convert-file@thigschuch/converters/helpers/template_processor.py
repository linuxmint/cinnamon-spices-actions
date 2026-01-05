#!/usr/bin/python3
"""
Template processing utilities for converters.

This module provides template parsing, formatting, and command building
functionality extracted from the base converter.
"""

import contextlib
from pathlib import Path
from typing import Optional

from config.settings import get_converter_template, settings_manager
from converters.helpers.commands import CommandParser
from converters.helpers.temp_file import TempFileManager
from utils import text
from utils.logging import logger


class TemplateProcessor:
    """Handles template-based command building and parsing.

    This class encapsulates all template-related logic previously in the
    Converter class, providing a clean separation of concerns. It manages
    command template retrieval, formatting with file paths, and fallback
    to custom command building methods.

    Attributes:
        converter_type: The type of converter (e.g., "image", "video").
        target_format: The target format extension in uppercase.

    Examples:
        >>> processor = TemplateProcessor("video", "MP4")
        >>> cmd, used_template, chained, shell, temp_mgr = processor.build_command_from_template(
        ...     input_file=Path("/tmp/input.avi"),
        ...     output_file=Path("/tmp/output.mp4")
        ... )
    """

    def __init__(self, converter_type: str, target_format: str) -> None:
        """Initialize the template processor.

        Args:
            converter_type: The converter type identifier (e.g., "image", "video").
            target_format: The target format extension (converted to uppercase).
        """
        self.converter_type = converter_type
        self.target_format = target_format.upper()

    def build_command_from_template(
        self,
        fallback_method=None,
        input_file: Optional[Path] = None,
        output_file: Optional[Path] = None,
    ) -> tuple:
        """Build command using template system with fallback to custom method.

        Retrieves and processes command templates from configuration, with automatic
        fallback to custom command building methods if templates are unavailable
        or fail to process.

        Args:
            fallback_method: Optional method to call if no template is found or
                           template processing fails.
            input_file: Path to the input file for template placeholder replacement.
            output_file: Path to the output file for template placeholder replacement.

        Returns:
            tuple: A 5-tuple containing:
                - list: The parsed command as a list of strings
                - bool: Whether a template was successfully used
                - list: List of chained commands (if any)
                - bool: Whether shell execution is required
                - Optional[TempFileManager]: Temporary file manager (if created)

        Examples:
            >>> processor = TemplateProcessor("image", "PNG")
            >>> result = processor.build_command_from_template(
            ...     input_file=Path("/tmp/input.jpg"),
            ...     output_file=Path("/tmp/output.png")
            ... )
            >>> cmd_list, used_template, chained, shell, temp_mgr = result
        """
        logger.debug(
            "Building command from template for converter: {}, format: {}",
            self.converter_type,
            self.target_format,
        )
        template, rule = get_converter_template(
            self.converter_type, self.target_format, input_file=input_file
        )
        if template:
            logger.debug("Found template: {}", template)
            try:
                result = self._process_template(template, input_file, output_file, rule)
                logger.debug("Template processed successfully")
                return result
            except (KeyError, ValueError) as e:
                logger.error("Template processing failed: {}", str(e))
                error_msg = text.Conversion.TEMPLATE_ERROR_MESSAGE.format(error=str(e))
                if fallback_method:
                    return self._use_fallback(fallback_method, error_msg)
                return [], False, [], False, error_msg

        logger.debug("No template found, using fallback method")
        if fallback_method:
            return self._use_fallback(fallback_method)
        return [], False, [], False, None

    def _process_template(
        self,
        template: str,
        input_file: Optional[Path],
        output_file: Optional[Path],
        rule: Optional[dict],
    ) -> tuple:
        """Process a command template and return parsed command data.

        Handles template formatting with file paths, temporary file creation,
        and command parsing for both simple and chained commands.

        Args:
            template: The command template string with placeholders.
            input_file: Path to the input file.
            output_file: Path to the output file.
            rule: Optional rule dictionary with template configuration.

        Returns:
            tuple: Parsed command data (command_list, True, chained_commands,
                  is_shell_command, temp_manager).

        Raises:
            Exception: If template processing or temporary file creation fails.
        """
        logger.debug("Processing template: {}", template)
        temp_manager = None

        temp_manager = None
        temp_dir_path = None
        temp_file_path = None
        try:
            if isinstance(template, list):
                logger.debug("Template is a list, joining with ' && '")
                template = " && ".join(template)
                logger.debug("Joined template: {}", template)

            if "{temp_dir}" in template:
                logger.debug("Template requires temp directory")
                temp_manager = TempFileManager(is_dir=True)
                temp_dir_path = temp_manager.__enter__()
                logger.debug("Created temp dir: {}", temp_dir_path)

            if "{temp_file}" in template:
                logger.debug("Template requires temp file")
                suffix: str = settings_manager.get("temporary", {}).get(
                    "file_suffix", ".tmp"
                )
                if rule:
                    suffix = rule.get("temp_file_suffix", suffix)
                temp_manager = TempFileManager(suffix=suffix)
                temp_file_path = temp_manager.__enter__()
                logger.debug("Created temp file: {}", temp_file_path)

            command_str = CommandParser.format_template(
                template,
                input_file=input_file,
                output_file=output_file,
                temp_dir=temp_dir_path,
                temp_file=temp_file_path,
            )
            logger.debug("Formatted command string: {}", command_str)

            if (temp_dir_path or temp_file_path) and "&&" in command_str:
                command_str = self._inject_file_validation(
                    command_str, temp_dir_path, temp_file_path
                )
                logger.debug("Injected file validation: {}", command_str)

            command_list, chained_commands, is_shell_command = (
                self._parse_command_string(command_str)
            )
            logger.debug(
                "Parsed command - list: {}, chained: {}, shell: {}",
                command_list,
                len(chained_commands),
                is_shell_command,
            )
            return command_list, True, chained_commands, is_shell_command, temp_manager

        except Exception as e:
            logger.error("Template processing failed: {}", str(e))
            if temp_manager:
                with contextlib.suppress(Exception):
                    temp_manager.__exit__(None, None, None)
            raise e

    def _parse_command_string(self, command_str: str) -> tuple:
        """Parse command string and return command components.

        Analyzes command strings to determine if they contain chained commands,
        shell operators, or simple executable commands.

        Args:
            command_str: The command string to parse.

        Returns:
            tuple: A 3-tuple containing:
                - list: The primary command as a list
                - list: List of chained commands (empty if not chained)
                - bool: Whether shell execution is required
        """
        if not command_str or not command_str.strip():
            logger.warning("Empty command string provided")
            return [], [], False

        if "&&" in command_str:
            commands = CommandParser.split_chained_commands(command_str)
            chained_commands = []
            for cmd in commands:
                parsed_cmd, _ = CommandParser.parse_command(cmd)
                if parsed_cmd:
                    chained_commands.append(parsed_cmd)
            command_list = chained_commands[0] if chained_commands else []
            return command_list, chained_commands, False

        elif CommandParser.is_shell_command(command_str):
            first_tool = command_str.split()[0] if command_str.strip() else "sh"
            return [first_tool, command_str], [], True

        else:
            try:
                command_list, _ = CommandParser.parse_command(command_str)
                return command_list, [], False
            except Exception as e:
                logger.error(
                    "Error parsing command string '{}': {}", command_str, str(e)
                )
                return [], [], False

    def _inject_file_validation(
        self,
        command_str: str,
        temp_dir_path: Optional[Path],
        temp_file_path: Optional[Path],
    ) -> str:
        """Automatically inject file existence checks in chained commands.

        When commands use temporary files/directories and chain operations with &&,
        this method automatically inserts 'test -f' checks before file-moving
        operations (like mv, cp, cat). This prevents the second step from running
        when the first step fails but returns exit code 0 (like LibreOffice).

        Args:
            command_str: The command string with && chains.
            temp_dir_path: Path to temporary directory (if used).
            temp_file_path: Path to temporary file (if used).

        Returns:
            str: Command string with automatic file validation injected.

        Examples:
            >>> # Before:
            >>> # "libreoffice --convert-to pdf --outdir /tmp/xyz file.docx && mv /tmp/xyz/file.pdf out.pdf"
            >>> # After:
            >>> # "libreoffice --convert-to pdf --outdir /tmp/xyz file.docx && test -f '/tmp/xyz/file.pdf' && mv /tmp/xyz/file.pdf out.pdf"
        """
        import re

        if not (temp_dir_path or temp_file_path) or " && " not in command_str:
            return command_str

        steps = command_str.split(" && ")
        if not steps:
            return command_str

        validated_steps = [steps[0]]

        for i, step in enumerate(steps[1:], start=1):
            step_stripped = step.strip()

            if any(step_stripped.startswith(cmd) for cmd in ["mv ", "cp ", "cat "]):
                match = re.match(
                    r"(mv|cp|cat)\s+['\"]?([^'\"]+?)['\"]?\s+", step_stripped
                )
                if match:
                    source_file = match.group(2).strip()

                    if temp_dir_path and str(temp_dir_path) in source_file:
                        validated_steps.append(f"test -f '{source_file}'")
                    elif temp_file_path and str(temp_file_path) in source_file:
                        validated_steps.append(f"test -f '{source_file}'")

            validated_steps.append(step)

        return " && ".join(validated_steps)

    def _use_fallback(self, fallback_method, error_msg: Optional[str] = None) -> tuple:
        """Use fallback method when template processing fails.

        Executes a fallback command building method when template-based
        processing is not available or fails.

        Args:
            fallback_method: The fallback method to execute.
            error_msg: Optional error message from template processing failure.

        Returns:
            tuple: Fallback result data (empty command, False, empty chains,
                  False, error_msg).
        """
        try:
            fallback_method()
            return [], False, [], False, error_msg
        except Exception as e:
            error_msg = f"Fallback method failed: {str(e)}"
            return [], False, [], False, error_msg
