#!/usr/bin/python3
"""
Temporary file management utilities for converters.

This module provides context manager for temporary file/directory creation
and cleanup, ensuring proper resource management during conversions.
"""

import contextlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from config import settings_manager


class TempFileManager:
    """Context manager for temporary file/directory creation and cleanup.

    Ensures proper cleanup of temporary files and directories even when errors occur.
    Provides configurable temporary file management with fallback to system defaults.

    Class Attributes:
        settings: Configuration settings for temporary files from settings manager.
        TEMP_DIR: Default temporary directory path.
        TEMP_SUFFIX: Default suffix for temporary files.
        TEMP_PREFIX: Default prefix for temporary files.

    Attributes:
        is_dir: Whether to create a temporary directory instead of a file.
        suffix: File suffix for temporary files.
        prefix: File prefix for temporary files.
        directory: Directory where temporary files should be created.
        path: The created temporary file/directory path (set during __enter__).

    Examples:
        >>> # Create a temporary file
        >>> with TempFileManager() as temp_file:
        ...     # Use temp_file for operations
        ...     pass
        >>> # File is automatically cleaned up

        >>> # Create a temporary directory
        >>> with TempFileManager(is_dir=True) as temp_dir:
        ...     # Use temp_dir for operations
        ...     pass
        >>> # Directory is automatically cleaned up
    """

    settings = settings_manager.get("temporary", {})
    TEMP_DIR: Path = Path(settings.get("directory", "/tmp"))
    TEMP_SUFFIX: str = settings.get("file_suffix", ".tmp")
    TEMP_PREFIX: str = settings.get("file_prefix", "convert_file_")

    def __init__(
        self,
        is_dir: bool = False,
        suffix: str = "",
        prefix: str = "",
        directory: Optional[Path] = None,
    ):
        """Initialize the temporary file manager.

        Args:
            is_dir: If True, create a temporary directory instead of a file.
            suffix: File extension for temporary files (uses default if empty).
            prefix: Prefix for temporary file/directory names (uses default if empty).
            directory: Directory to create temporary files in (uses default if None).
        """
        self.is_dir = is_dir
        self.suffix = suffix or self.TEMP_SUFFIX
        self.prefix = prefix or self.TEMP_PREFIX
        self.directory = directory or self.TEMP_DIR
        self.path: Optional[Path] = None

        if not self.directory.exists():
            self.directory.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> Path:
        """Create and return temporary file or directory path.

        Creates either a temporary file or directory based on the is_dir setting.
        The path is stored internally and returned for use.

        Returns:
            Path: Path to the created temporary file or directory.

        Raises:
            OSError: If temporary file/directory creation fails.
        """
        if self.is_dir:
            self.path = Path(tempfile.mkdtemp(prefix=self.prefix, dir=self.directory))
        else:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=self.suffix, prefix=self.prefix, dir=self.directory
            )
            self.path = Path(temp_file.name)
            temp_file.close()
        return self.path

    def __exit__(self, *_) -> None:
        """Clean up temporary file or directory.

        Removes the temporary file or directory created during __enter__.
        Suppresses OSError exceptions to ensure cleanup doesn't raise errors.

        Args:
            *_: Exception information (ignored, cleanup always attempted).
        """
        if self.path and self.path.exists():
            with contextlib.suppress(OSError):
                if self.is_dir:
                    shutil.rmtree(self.path)
                else:
                    self.path.unlink()
