#!/usr/bin/python3
"""
Command utilities for converters.

This module provides utilities for parsing, building, and validating shell commands
used in file conversion operations. It handles command template formatting, shell
operator detection, and multi-step command construction.
"""

import re
import shlex
from pathlib import Path
from typing import List, Optional, Tuple

from utils.logging import logger

from .constants import SHELL_OPERATORS


class CommandParser:
    """Parses and builds commands from templates with shell operator support.

    Provides utilities for handling complex shell commands including chained operations,
    template formatting with file paths, and tool extraction for dependency checking.

    Attributes:
        SHELL_OPERATORS: List of shell operators that require shell execution.

    Examples:
        >>> parser = CommandParser()
        >>> is_shell = parser.is_shell_command("ffmpeg -i input.mp4 output.mp3")
        >>> print(is_shell)
        False
    """

    @staticmethod
    def is_shell_command(command: str) -> bool:
        """Check if a command requires shell execution due to shell operators.

        Analyzes the command string for shell operators that cannot be handled
        by direct subprocess execution without shell=True. Ignores operators
        that appear inside quoted strings or as part of parameter values.

        Args:
            command: Command string to analyze for shell operators.

        Returns:
            bool: True if the command contains shell operators requiring shell
                  execution, False if it can be executed directly.

        Examples:
            >>> CommandParser.is_shell_command("ffmpeg -i input.mp4 output.mp3")
            False
            >>> CommandParser.is_shell_command("convert image.jpg && rm temp.jpg")
            True
            >>> CommandParser.is_shell_command("pandoc input.md --metadata=<title>")
            False
        """
        try:
            if any(op in command for op in ["&&", "||"]):
                return True

            if " | " in command:
                return True

            for op in [">", ">>", "<", "<<"]:
                if f" {op} " in command:
                    return True
                if command.rstrip().endswith(f" {op}"):
                    return True
                if command.lstrip().startswith(f"{op} "):
                    return True

            return False
        except Exception:
            return any(op in command for op in SHELL_OPERATORS)

    @staticmethod
    def extract_tools_from_shell(command: str) -> List[str]:
        """Extract all tool names from a shell command string.

        Parses shell commands to identify executable tools, handling chained
        commands and shell operators. Used for dependency checking before
        command execution.

        Args:
            command: Shell command string containing one or more tool calls.

        Returns:
            List[str]: List of tool names found in the command, excluding
                      shell operators and arguments.

        Examples:
            >>> cmd = "ffmpeg -i input.mp4 output.mp3 && rm temp.mp4"
            >>> tools = CommandParser.extract_tools_from_shell(cmd)
            >>> print(tools)
            ['ffmpeg', 'rm']
        """
        tools = re.findall(r"(?:^|\||&&|\|\|)\s*([a-zA-Z0-9_-]+)", command)
        return [tool for tool in tools if tool]

    @staticmethod
    def split_chained_commands(command: str) -> List[str]:
        """Split a command string by the && operator into individual commands.

        Breaks down multi-step conversion commands into separate executable
        parts for sequential processing.

        Args:
            command: Command string potentially containing && chains.

        Returns:
            List[str]: List of individual command strings, stripped of whitespace.

        Examples:
            >>> cmd = "ffmpeg -i input.mp4 temp.mp3 && lame temp.mp3 output.mp3"
            >>> commands = CommandParser.split_chained_commands(cmd)
            >>> print(len(commands))
            2
        """
        return [cmd.strip() for cmd in command.split(" && ")]

    @staticmethod
    def parse_command(command_str: str) -> Tuple[List[str], bool]:
        """Parse a command string into executable format and shell requirement.

        Converts command strings into the appropriate format for subprocess execution,
        determining whether shell execution is needed based on command complexity.

        Args:
            command_str: Raw command string to parse.

        Returns:
            Tuple[List[str], bool]: A tuple containing:
                - List[str]: Parsed command as a list for subprocess execution
                - bool: True if shell execution is required, False otherwise

        Examples:
            >>> cmd, needs_shell = CommandParser.parse_command("ls -la")
            >>> print(cmd, needs_shell)
            ['ls', '-la'] False

            >>> cmd, needs_shell = CommandParser.parse_command("echo 'hello' > file.txt")
            >>> print(needs_shell)
            True
        """
        if not CommandParser.is_shell_command(command_str):
            return shlex.split(command_str), False
        first_tool = command_str.split()[0] if command_str.strip() else "sh"
        return [first_tool, command_str], True

    @staticmethod
    def format_template(
        template: str,
        input_file: Optional[Path] = None,
        output_file: Optional[Path] = None,
        temp_file: Optional[Path] = None,
        temp_dir: Optional[Path] = None,
        **kwargs,
    ) -> str:
        """Format a command template with file paths and additional arguments.

        Replaces placeholders in command templates with actual file paths and
        derived values like filenames, directories, and custom parameters.

        Args:
            template: Command template string with placeholders like {input},
                     {output}, {temp_file}, etc.
            input_file: Path to the input file for conversion.
            output_file: Path to the output file for conversion.
            temp_file: Path to a temporary file if needed.
            temp_dir: Path to a temporary directory if needed.
            **kwargs: Additional format arguments as key-value pairs.

        Returns:
            str: Formatted command string with all placeholders replaced.

        Examples:
            >>> template = "convert {input} {output}"
            >>> cmd = CommandParser.format_template(
            ...     template,
            ...     input_file=Path("/tmp/input.jpg"),
            ...     output_file=Path("/tmp/output.png")
            ... )
            >>> print(cmd)
            'convert /tmp/input.jpg /tmp/output.png'
        """
        logger.debug("Formatting command template: {}", template)
        format_args = {}

        if input_file:
            format_args["input"] = str(input_file)
            format_args["input_name"] = input_file.name
            format_args["input_stem"] = input_file.stem
            logger.debug(
                "Input file: {}, name: {}, stem: {}",
                input_file,
                input_file.name,
                input_file.stem,
            )

        if output_file:
            format_args["output"] = str(output_file)
            format_args["output_dir"] = str(output_file.parent)
            logger.debug("Output file: {}, dir: {}", output_file, output_file.parent)

        if temp_file:
            format_args["temp_file"] = str(temp_file)
            logger.debug("Temp file: {}", temp_file)

        if temp_dir:
            format_args["temp_dir"] = str(temp_dir)
            logger.debug("Temp dir: {}", temp_dir)

        for key, value in kwargs.items():
            format_args[key] = str(value) if isinstance(value, Path) else value

        formatted = template.format(**format_args)
        logger.debug("Formatted command: {}", formatted)
        return formatted
