#!/usr/bin/python3
"""
Tool validation utilities for converters.

Provides utilities for checking tool availability and managing dependencies.
"""

from typing import Callable, List, Optional

from utils import dependency_manager

from .commands import CommandParser


class ToolValidator:
    """Validates tool availability and manages dependency checking.

    Provides centralized tool validation for converter operations, handling
    both single tools and complex shell commands. Supports batch mode operation
    and user-friendly dialog display for missing dependencies.

    Attributes:
        batch_mode: Whether operating in batch mode (affects dialog behavior).
        show_missing_dialog_fn: Optional callback to display missing tool dialogs.
        _dialog_shown: Internal flag to prevent duplicate error dialogs.

    Examples:
        >>> def show_dialog(msg): print(f"Missing tool: {msg}")
        >>> validator = ToolValidator(batch_mode=False, show_missing_dialog_fn=show_dialog)
        >>> available = validator.check_tool("ffmpeg")
        >>> if not available:
        ...     print("ffmpeg is not available")
    """

    def __init__(
        self,
        batch_mode: bool = False,
        show_missing_dialog_fn: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the tool validator.

        Args:
            batch_mode: Whether running in batch mode, which suppresses
                       individual error dialogs.
            show_missing_dialog_fn: Optional callback function to display
                                  dialogs for missing tools.
        """
        self.batch_mode = batch_mode
        self.show_missing_dialog_fn = show_missing_dialog_fn
        self._dialog_shown = False

    def check_tool(self, tool_name: str) -> bool:
        """Check if a single tool is available on the system.

        Verifies tool availability by checking for installation instructions,
        which are only available for tools that are not installed.

        Args:
            tool_name: Name of the tool to check for availability.

        Returns:
            bool: True if the tool is available, False if it's missing.

        Examples:
            >>> validator = ToolValidator()
            >>> available = validator.check_tool("convert")  # ImageMagick
            >>> print(f"ImageMagick available: {available}")
        """
        install_cmd = dependency_manager.get_install_instructions(tool_name)

        if install_cmd:
            if (
                not self.batch_mode
                and self.show_missing_dialog_fn
                and not self._dialog_shown
            ):
                self.show_missing_dialog_fn(install_cmd)
                self._dialog_shown = True
            return False
        return True

    def check_tools(self, tool_names: List[str]) -> bool:
        """Check if all tools in a list are available.

        Validates availability of multiple tools, returning False if any
        tool in the list is not available.

        Args:
            tool_names: List of tool names to check for availability.

        Returns:
            bool: True if all tools are available, False if any are missing.

        Examples:
            >>> validator = ToolValidator()
            >>> tools = ["ffmpeg", "ffprobe", "lame"]
            >>> all_available = validator.check_tools(tools)
            >>> print(f"All audio tools available: {all_available}")
        """
        return all(self.check_tool(tool) for tool in tool_names)

    def check_shell_command(self, command: str) -> bool:
        """Check all tools referenced in a shell command string.

        Parses shell commands to extract tool names and validates that
        all referenced tools are available on the system.

        Args:
            command: Shell command string containing tool calls.

        Returns:
            bool: True if all tools in the command are available, False otherwise.

        Examples:
            >>> validator = ToolValidator()
            >>> cmd = "ffmpeg -i input.mp4 output.mp3 && rm temp.mp4"
            >>> valid = validator.check_shell_command(cmd)
            >>> print(f"Command tools available: {valid}")
        """
        tools = CommandParser.extract_tools_from_shell(command)
        return self.check_tools(tools)

    def check_chained_commands(self, command: str) -> bool:
        """Check all tools in chained commands separated by && operators.

        Parses command strings with && chains to extract tool names from
        each step and validates their availability.

        Args:
            command: Command string containing &&-separated command chains.

        Returns:
            bool: True if all tools in all command steps are available, False otherwise.

        Examples:
            >>> validator = ToolValidator()
            >>> chained = "ffmpeg -i input.mp4 temp.mp3 && lame temp.mp3 output.mp3"
            >>> valid = validator.check_chained_commands(chained)
            >>> print(f"Chained command tools available: {valid}")
        """
        steps = CommandParser.split_chained_commands(command)
        tools = []

        for step in steps:
            step_tool = step.strip().split()[0] if step.strip() else None
            if step_tool:
                tools.append(step_tool)

        return self.check_tools(tools)
