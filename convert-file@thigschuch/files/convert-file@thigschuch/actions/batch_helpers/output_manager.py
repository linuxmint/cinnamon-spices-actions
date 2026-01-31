#!/usr/bin/python3
"""
Output directory management for batch operations.

This module provides utilities for managing output directories
and file placement in batch conversion operations.
"""

import contextlib
from pathlib import Path
from typing import Optional

from config import settings_manager
from utils.logging import logger


class OutputManager:
    """Manages output directory creation and cleanup for batch operations.

    Provides utilities for creating unique output directories and cleaning up
    empty directories after batch operations. Handles automatic directory
    creation based on configurable thresholds and naming patterns.

    Attributes:
        base_directory: Base directory where output directories are created.
        output_directory: Currently active output directory, or None.

    Examples:
        >>> manager = OutputManager(Path("/tmp"))
        >>> output_dir = manager.create_output_directory(10)
        >>> if output_dir:
        ...     print(f"Output directory: {output_dir}")
        >>> manager.cleanup_empty_directory()  # Clean up if empty
    """

    def __init__(self, base_directory: Path) -> None:
        """Initialize the output manager.

        Args:
            base_directory: Base directory where output directories will be
                           created for batch operations.

        Examples:
            >>> manager = OutputManager(Path("/home/user/videos"))
            >>> print(f"Base dir: {manager.base_directory}")
        """
        self.base_directory = base_directory
        self.output_directory: Optional[Path] = None

    def create_output_directory(self, file_count: int) -> Optional[Path]:
        """Create an output directory for batch conversion if needed.

        Creates a unique output directory when the file count exceeds the
        configured threshold. Uses settings for directory naming and creation
        logic. Falls back to source directories for small batches.

        Args:
            file_count: Number of files being converted in the batch.

        Returns:
            Optional[Path]: Path to the created output directory, or None if
                           using source directories (for small batches).

        Examples:
            >>> manager = OutputManager(Path("/tmp"))
            >>> # Small batch - no separate directory
            >>> output = manager.create_output_directory(3)
            >>> print(f"Output dir: {output}")  # None

            >>> # Large batch - creates directory
            >>> output = manager.create_output_directory(10)
            >>> print(f"Output dir: {output}")  # /tmp/converted_files
        """
        logger.debug("Creating output directory for {} files", file_count)
        threshold = settings_manager.get("directory_creation_threshold", 5)
        logger.debug("Directory creation threshold: {}", threshold)
        if file_count <= threshold:
            logger.debug(
                "File count {} <= threshold {}, using source directories",
                file_count,
                threshold,
            )
            return None

        output_folder_name = settings_manager.get(
            "output_directory_name", "converted_files"
        )
        logger.debug("Output folder name: {}", output_folder_name)

        output_dir = self.base_directory / output_folder_name

        count = 1
        while output_dir.exists():
            output_dir = self.base_directory / f"{output_folder_name}_{count}"
            count += 1

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_directory = output_dir
            logger.info("Created output directory: {}", output_dir)
            return output_dir
        except OSError as e:
            logger.error("Failed to create output directory: {}", str(e))
            self.output_directory = None
            return None

    def cleanup_empty_directory(self) -> None:
        """Clean up the output directory if it's empty and no files were converted.

        Removes the output directory if it exists and contains no files.
        This prevents leaving behind empty directories after failed batch operations.

        Examples:
            >>> manager = OutputManager(Path("/tmp"))
            >>> manager.create_output_directory(10)
            >>> # ... batch operation fails, no files created ...
            >>> manager.cleanup_empty_directory()  # Removes empty directory
        """
        logger.debug("Checking for empty output directory cleanup")
        if not self.output_directory or not self.output_directory.exists():
            logger.debug("No output directory to clean up")
            return

        with contextlib.suppress(OSError):
            if not any(self.output_directory.iterdir()):
                logger.info(
                    "Removing empty output directory: {}", self.output_directory
                )
                self.output_directory.rmdir()
            else:
                logger.debug(
                    "Output directory not empty, keeping: {}", self.output_directory
                )

    def get_output_directory(self) -> Optional[Path]:
        """Get the current output directory.

        Returns the path to the currently active output directory, or None
        if no output directory has been created or is active.

        Returns:
            Optional[Path]: The current output directory path, or None if
                           no output directory is set.

        Examples:
            >>> manager = OutputManager(Path("/tmp"))
            >>> output = manager.create_output_directory(10)
            >>> current = manager.get_output_directory()
            >>> print(f"Current output: {current}")  # /tmp/converted_files
        """
        return self.output_directory
