#!/usr/bin/python3
"""
File validation utilities for convert-file action.

This module provides centralized file validation logic used across
single and batch conversion operations.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Set, Tuple

from config import format_config
from utils import text
from utils.logging import logger


class FileValidator:
    """Utility class for validating files and formats for conversion operations.

    Provides centralized validation logic to reduce duplication between
    single file and batch conversion actions. Handles file existence,
    format recognition, and conversion compatibility checks.

    All methods are static and can be called without instantiating the class.

    Examples:
        >>> from pathlib import Path
        >>> file_path = Path("/tmp/test.jpg")
        >>> is_valid, error = FileValidator.validate_single_file(file_path)
        >>> if not is_valid:
        ...     print(f"Error: {error}")
    """

    @staticmethod
    def validate_single_file(file_path: Path) -> Tuple[bool, Optional[str]]:
        """Validate that a single file exists and is convertible.

        Performs comprehensive validation including:
        - File existence check
        - File vs directory validation
        - Extension presence validation
        - Format group recognition (handles compound extensions like .tar.bz2)

        Args:
            file_path: Path to the file to validate.

        Returns:
            Tuple[bool, Optional[str]]: A tuple containing:
                - bool: True if file is valid for conversion, False otherwise
                - Optional[str]: Error message if validation failed, None if valid

        Examples:
            >>> file_path = Path("/tmp/test.jpg")
            >>> is_valid, error = FileValidator.validate_single_file(file_path)
            >>> if not is_valid:
            ...     print(f"Validation failed: {error}")
        """
        logger.debug("Validating single file: {}", file_path)
        if not file_path.exists():
            logger.debug("File does not exist: {}", file_path)
            return False, text.Validation.FILE_NOT_FOUND_MESSAGE.format(path=file_path)

        if not file_path.is_file():
            logger.debug("Path is not a file: {}", file_path)
            return False, text.Validation.INVALID_FILE_MESSAGE.format(path=file_path)

        if not file_path.suffix:
            logger.debug("File has no extension: {}", file_path)
            return False, text.Validation.MISSING_EXTENSION_MESSAGE.format(
                path=file_path
            )

        file_format = FileValidator.get_file_format(file_path)
        
        format_group = format_config.get_format_group(file_format)
        if not format_group:
            logger.debug("Unsupported format: {}", file_format)
            return False, text.Validation.UNSUPPORTED_FORMAT_ERROR_MESSAGE.format(
                extension=file_format
            )

        logger.debug(
            "File validation successful: {} (group: {})", file_path, format_group
        )
        return True, None

    @staticmethod
    @lru_cache(maxsize=512)
    def get_file_format(file_path: Path) -> str:
        """Get the format of a file based on its extension.

        Extracts the file extension and validates it against known format groups.
        Dynamically handles compound extensions (like .tar.bz2) by checking all
        registered formats in the configuration. Falls back to simple extension
        if no registered format matches.

        Args:
            file_path: Path to the file to analyze.

        Returns:
            str: The uppercase file format extension (without the dot).
                 Returns empty string if file has no extension.

        Examples:
            >>> file_path = Path("/tmp/photo.jpg")
            >>> fmt = FileValidator.get_file_format(file_path)
            >>> print(fmt)
            'JPG'
            >>> file_path = Path("/tmp/archive.tar.bz2")
            >>> fmt = FileValidator.get_file_format(file_path)
            >>> print(fmt)
            'TAR.BZ2'
            >>> file_path = Path("/tmp/noext")
            >>> fmt = FileValidator.get_file_format(file_path)
            >>> print(fmt)
            ''
        """
        logger.debug("Getting file format for: {}", file_path)
        if not file_path.suffix:
            logger.debug("File has no extension")
            return ""

        filename_lower = file_path.name.lower()
        
        all_formats = set()
        for group in format_config._format_groups.values():
            all_formats.update(group.formats)
        
        sorted_formats = sorted(all_formats, key=len, reverse=True)
                
        for format_name in sorted_formats:
            extension_pattern = "." + format_name.lower()
            if filename_lower.endswith(extension_pattern):
                logger.debug("Format recognized: {}", format_name)
                return format_name
        
        fallback_format = file_path.suffix[1:].upper()
        logger.debug("Using fallback format: {}", fallback_format)
        return fallback_format

    @staticmethod
    @lru_cache(maxsize=512)
    def get_base_name_and_extension(file_path: Path) -> tuple[str, str]:
        """Extract base name and extension from a file path.
        
        Handles both simple extensions (.pdf, .jpg) and compound extensions
        (.tar.bz2, .tar.gz, .tar.xz) by using the format configuration.
        
        Args:
            file_path: The file path to analyze.
            
        Returns:
            tuple[str, str]: A tuple of (base_name, extension) where:
                - base_name is the filename without any extension
                - extension is the full extension including the dot (e.g., ".tar.xz")
        
        Examples:
            >>> FileValidator.get_base_name_and_extension(Path("archive.tar.bz2"))
            ('archive', '.tar.bz2')
            >>> FileValidator.get_base_name_and_extension(Path("document.pdf"))
            ('document', '.pdf')
            >>> FileValidator.get_base_name_and_extension(Path("noext"))
            ('noext', '')
        """
        file_format = FileValidator.get_file_format(file_path)
        
        if file_format:
            extension = "." + file_format.lower()
            filename_lower = file_path.name.lower()
            
            if filename_lower.endswith(extension):
                base_name = file_path.name[:-len(extension)]
                return base_name, extension
        
        return file_path.stem, file_path.suffix

    @staticmethod
    def validate_file_list(
        file_paths: List[Path],
    ) -> Tuple[List[Path], Set[str], List[str]]:
        """Validate a list of files and categorize them by format group.

        Processes multiple files, validating each one and collecting results.
        Groups valid files by their format groups and collects all error messages.
        Handles compound extensions like .tar.bz2 properly.

        Args:
            file_paths: List of file paths to validate.

        Returns:
            Tuple[List[Path], Set[str], List[str]]: A tuple containing:
                - List[Path]: Valid files that can be converted
                - Set[str]: Format groups detected among valid files
                - List[str]: Error messages for invalid files

        Examples:
            >>> files = [Path("/tmp/photo.jpg"), Path("/tmp/video.mp4")]
            >>> valid, groups, errors = FileValidator.validate_file_list(files)
            >>> print(f"Valid files: {len(valid)}, Groups: {groups}")
        """
        logger.debug("Validating file list with {} files", len(file_paths))
        valid_files = []
        detected_groups = set()
        error_messages = []

        for file_path in file_paths:
            is_valid, error_msg = FileValidator.validate_single_file(file_path)
            if not is_valid:
                error_messages.append(error_msg)
                continue

            file_format = FileValidator.get_file_format(file_path)
            format_group = format_config.get_format_group(file_format)
            if format_group:
                valid_files.append(file_path)
                detected_groups.add(format_group)

        logger.debug(
            "File list validation complete: {} valid files, {} groups, {} errors",
            len(valid_files),
            len(detected_groups),
            len(error_messages),
        )
        return valid_files, detected_groups, error_messages

    @staticmethod
    def get_available_formats(source_format: str) -> Tuple[str, ...]:
        """Get available target formats for a source format.

        Retrieves all possible target formats that the given source format
        can be converted to, respecting format restrictions and special rules.

        Args:
            source_format: The source file format (case-insensitive).

        Returns:
            Tuple[str, ...]: Sorted tuple of available target format names.

        Examples:
            >>> formats = FileValidator.get_available_formats("JPEG")
            >>> print(formats[:3])  # Show first 3 formats
            ('BMP', 'PNG', 'TIFF')
        """
        formats = (
            format_config.get_available_formats(source_format) if source_format else ()
        )
        logger.debug(
            "Available formats for {}: {} formats", source_format, len(formats)
        )
        return formats

    @staticmethod
    def get_default_format(source_format: str) -> Optional[str]:
        """Get the default target format for a source format.

        Returns the recommended default target format for conversions
        from the specified source format.

        Args:
            source_format: The source file format (case-insensitive).

        Returns:
            Optional[str]: Default target format name, or None if not available.

        Examples:
            >>> default = FileValidator.get_default_format("JPEG")
            >>> print(default)
            'PNG'
        """
        default_format = format_config.get_default_format(source_format)
        logger.debug("Default format for {}: {}", source_format, default_format)
        return default_format
