#!/usr/bin/python3
"""
File management utilities for converters.

This module provides common file management functionality used across
different converter implementations.
"""

import contextlib
import time
from pathlib import Path
from typing import Optional

from converters.helpers.temp_file import TempFileManager
from utils.validation import FileValidator


class FileManager:
    """Handles file operations and management for converters.

    Provides utilities for target file naming, temporary file management,
    and file cleanup operations. Manages the lifecycle of output files
    and ensures proper cleanup of temporary resources.

    Attributes:
        source_file: The original file being converted.
        target_format: The target format extension (uppercase).
        output_dir: Optional directory for output files.
        temp_manager: Optional temporary file manager instance.

    Examples:
        >>> source = Path("/tmp/video.mp4")
        >>> manager = FileManager(source, "MP3", Path("/tmp/output"))
        >>> target = manager.get_target_file()
        >>> print(target)
        /tmp/output/video.mp3
    """

    def __init__(
        self, source_file: Path, target_format: str, output_dir: Optional[Path] = None
    ):
        """Initialize the file manager.

        Args:
            source_file: Path to the source file being converted.
            target_format: Target format extension (will be converted to uppercase).
            output_dir: Optional directory where output files should be placed.
                       If None, files are placed in the source file's directory.
        """
        self.source_file = source_file
        self.target_format = target_format.upper()
        self.output_dir = output_dir
        self.temp_manager: Optional[TempFileManager] = None

    def get_target_file(self) -> Path:
        """Generate the target file path based on source file and output directory.

        Creates a target filename by replacing the source file's extension
        with the target format. Properly handles compound extensions like .tar.bz2.
        Places the file in the specified output directory or the source file's
        directory if no output directory is set.

        Returns:
            Path: Complete path to the target output file.

        Examples:
            >>> source = Path("/home/user/document.docx")
            >>> manager = FileManager(source, "PDF", Path("/tmp/converted"))
            >>> target = manager.get_target_file()
            >>> print(target)
            /tmp/converted/document.pdf

            >>> source = Path("/home/user/archive.tar.bz2")
            >>> manager = FileManager(source, "TAR.XZ", Path("/tmp/converted"))
            >>> target = manager.get_target_file()
            >>> print(target)
            /tmp/converted/archive.tar.xz
        """
        base_name, _ = FileValidator.get_base_name_and_extension(self.source_file)
        target_name = f"{base_name}.{self.target_format.lower()}"

        if self.output_dir:
            return self.output_dir / target_name
        else:
            return self.source_file.parent / target_name

    def ensure_unique_filename(self, target_file: Path) -> Path:
        """Ensure the target file has a unique name by appending numbers if needed.

        Checks if the target file already exists and generates a unique filename
        by appending a counter in parentheses if conflicts are found.
        Properly handles compound extensions like .tar.xz.

        Args:
            target_file: The initial target file path to check for uniqueness.

        Returns:
            Path: A unique target file path that doesn't conflict with existing files.

        Examples:
            >>> existing_file = Path("/tmp/test.mp3")
            >>> # Assume /tmp/test.mp3 already exists
            >>> manager = FileManager(Path("/tmp/source.wav"), "MP3")
            >>> unique = manager.ensure_unique_filename(existing_file)
            >>> print(unique)
            /tmp/test (1).mp3

            >>> existing_file = Path("/tmp/archive.tar.xz")
            >>> # Assume /tmp/archive.tar.xz already exists
            >>> manager = FileManager(Path("/tmp/source.tar.bz2"), "TAR.XZ")
            >>> unique = manager.ensure_unique_filename(existing_file)
            >>> print(unique)
            /tmp/archive (1).tar.xz
        """
        if not target_file.exists():
            return target_file

        base_name, extension = FileValidator.get_base_name_and_extension(target_file)

        parent_dir = target_file.parent
        counter = 1

        while target_file.exists():
            new_name = f"{base_name} ({counter}){extension}"
            target_file = parent_dir / new_name
            counter += 1

        return target_file

    def delete_target_file(
        self, target_file: Path, output_dir: Optional[Path] = None
    ) -> None:
        """Delete the target file with retries for stubborn files.

        Attempts to delete the target file with multiple retries and permission
        fixes for files that may be locked or have permission issues. Also
        attempts fallback deletion from the source directory if specified.

        Args:
            target_file: The file to delete.
            output_dir: Optional output directory for fallback deletion attempts.

        Examples:
            >>> target = Path("/tmp/converted.mp3")
            >>> manager.delete_target_file(target)
            # File is deleted with retries if needed
        """
        target_deleted = False
        for attempt in range(5):
            try:
                if target_file.exists():
                    target_file.chmod(0o666)
                    target_file.unlink()
                    target_deleted = True
                    break
            except OSError:
                if attempt < 4:
                    time.sleep(0.2)

        if not target_deleted and output_dir:
            with contextlib.suppress(Exception):
                source_file = self.source_file.parent / target_file.name
                for attempt in range(5):
                    try:
                        if source_file.exists():
                            source_file.chmod(0o666)
                            source_file.unlink()
                            break
                    except OSError:
                        if attempt < 4:
                            time.sleep(0.2)

    def cleanup_temp_files(self) -> None:
        """Clean up any temporary files created during conversion.

        Safely cleans up temporary files managed by the TempFileManager,
        suppressing any exceptions that might occur during cleanup.

        Examples:
            >>> manager = FileManager(Path("/tmp/input.mp4"), "MP3")
            >>> temp_mgr = TempFileManager()
            >>> manager.set_temp_manager(temp_mgr)
            >>> # ... conversion operations ...
            >>> manager.cleanup_temp_files()  # Temp files are cleaned up
        """
        if self.temp_manager:
            with contextlib.suppress(Exception):
                self.temp_manager.__exit__(None, None, None)

    def set_temp_manager(self, temp_manager: TempFileManager) -> None:
        """Set the temporary file manager for this file manager instance.

        Associates a TempFileManager instance with this FileManager for
        coordinated temporary file lifecycle management.

        Args:
            temp_manager: The TempFileManager instance to use for temporary
                         file operations.

        Examples:
            >>> manager = FileManager(Path("/tmp/input.mp4"), "MP3")
            >>> temp_mgr = TempFileManager()
            >>> manager.set_temp_manager(temp_mgr)
        """
        self.temp_manager = temp_manager
