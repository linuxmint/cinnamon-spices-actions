#!/usr/bin/python3
"""
Format validation utilities for batch operations.

This module provides format validation and intersection logic
for batch file conversion operations.
"""

from pathlib import Path
from typing import List, Set, Tuple

from config import format_config
from utils.logging import logger
from utils.validation import FileValidator


class FormatValidator:
    """Validates and manages format compatibility for batch operations.

    Provides utilities for checking format groups, finding common formats,
    and validating batch conversion compatibility. Handles both single-format
    and mixed-format batch operations with special conversion rules.

    This class contains only static methods and should not be instantiated.

    Examples:
        >>> # Validate files for batch conversion
        >>> files = [Path("/tmp/video1.mp4"), Path("/tmp/video2.mp4")]
        >>> valid_files, groups, errors = FormatValidator.validate_batch_files(files)
        >>> print(f"Valid files: {len(valid_files)}, Groups: {groups}")

        >>> # Find common target formats
        >>> formats = ["MP4", "AVI"]
        >>> common = FormatValidator.get_common_formats(formats)
        >>> print(f"Common formats: {common}")
    """

    @staticmethod
    def validate_batch_files(
        file_paths: List[Path],
    ) -> Tuple[List[Path], Set[str], List[str]]:
        """Validate files for batch conversion.

        Performs comprehensive validation on a list of files for batch processing.
        Checks file existence, format detection, and group compatibility.

        Args:
            file_paths: List of file paths to validate for batch conversion.

        Returns:
            Tuple[List[Path], Set[str], List[str]]: A tuple containing:
                - List[Path]: Valid file paths that can be processed.
                - Set[str]: Format groups detected (e.g., {"video", "audio"}).
                - List[str]: Error messages for invalid files.

        Examples:
            >>> files = [Path("/tmp/video.mp4"), Path("/tmp/audio.mp3")]
            >>> valid, groups, errors = FormatValidator.validate_batch_files(files)
            >>> print(f"Valid: {len(valid)}, Groups: {groups}, Errors: {len(errors)}")
        """
        logger.debug("Validating {} files for batch conversion", len(file_paths))
        result = FileValidator.validate_file_list(file_paths)
        valid_files, groups, errors = result
        logger.debug(
            "Batch validation result: {} valid files, {} groups, {} errors",
            len(valid_files),
            len(groups),
            len(errors),
        )
        return result

    @staticmethod
    def get_common_formats(source_formats: List[str]) -> Tuple[str, ...]:
        """Get formats that are available for conversion from ALL source formats.

        For mixed format batches, also include source formats that can be reached
        via special conversion rules from other source formats. This enables
        cross-format conversions like MP4→MP3 or AVI→JPEG.

        Args:
            source_formats: List of source format extensions (uppercase, e.g., ["MP4", "AVI"]).

        Returns:
            Tuple[str, ...]: Sorted tuple of target formats available for conversion
                            from all specified source formats.

        Examples:
            >>> # Single format batch
            >>> common = FormatValidator.get_common_formats(["MP4"])
            >>> print("MP3" in common)  # True (MP4 can convert to MP3)

            >>> # Mixed format batch
            >>> common = FormatValidator.get_common_formats(["MP4", "AVI"])
            >>> print("MP3" in common)  # True (both can convert to MP3)
        """
        logger.debug("Getting common formats for source formats: {}", source_formats)
        if not source_formats:
            logger.debug("No source formats provided")
            return ()

        all_available_formats = [
            set(format_config.get_available_formats(fmt)) for fmt in source_formats
        ]

        common_formats = (
            set.intersection(*all_available_formats) if all_available_formats else set()
        )

        if len(source_formats) > 1:
            cross_formats = FormatValidator._get_cross_format_conversions(
                source_formats
            )
            common_formats.update(cross_formats)
            logger.debug("Added {} cross-format conversions", len(cross_formats))

        result = tuple(sorted(common_formats))
        logger.debug("Common formats result: {}", result)
        return result

    @staticmethod
    def _get_cross_format_conversions(source_formats: List[str]) -> Set[str]:
        """Get source formats that can be converted to by other source formats.

        This handles special conversion rules where one source format can be
        converted to another source format (e.g., AVI -> MP3). Used internally
        by get_common_formats for mixed-format batch operations.

        Args:
            source_formats: List of source format extensions (uppercase).

        Returns:
            Set[str]: Set of formats that are both source formats and can be
                     produced by other source formats in the batch.

        Examples:
            >>> # If MP4 and AVI are both sources, and AVI can convert to MP4
            >>> cross = FormatValidator._get_cross_format_conversions(["MP4", "AVI"])
            >>> print("MP4" in cross)  # True if AVI can convert to MP4
        """
        if len(source_formats) <= 1:
            return set()

        source_set = set(source_formats)

        all_producible_formats = set()
        for fmt in source_formats:
            all_producible_formats.update(format_config.get_available_formats(fmt))

        return source_set & all_producible_formats

    @staticmethod
    def check_format_groups_compatibility(format_groups: Set[str]) -> bool:
        """Check if format groups are compatible for batch conversion.

        Validates whether the detected format groups can be processed together
        in a batch operation. Currently allows mixed groups, relying on the
        common formats logic to determine valid conversions.

        Args:
            format_groups: Set of format groups detected from files
                          (e.g., {"video", "audio", "image"}).

        Returns:
            bool: True if format groups are compatible for batch processing,
                  False otherwise.

        Examples:
            >>> groups = {"video", "audio"}
            >>> compatible = FormatValidator.check_format_groups_compatibility(groups)
            >>> print(f"Mixed groups compatible: {compatible}")  # True
        """

        return len(format_groups) > 0
