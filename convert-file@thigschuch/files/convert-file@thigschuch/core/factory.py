#!/usr/bin/python3
"""
Converter factory for creating appropriate converter instances.

This module provides a factory pattern implementation for creating
converter instances based on file formats and conversion rules.

The factory uses a single Converter class with template-based
command building for all conversion types.
"""

from pathlib import Path
from typing import Optional

from config import format_config
from converters import Converter
from utils.logging import logger
from utils.validation import FileValidator


class ConverterFactory:
    """Factory class for creating converters based on format and rules.

    This factory creates converter instances using a single Converter class
    with template-based command building for all conversion types.

    The factory checks format compatibility and creates appropriate converter
    instances that will use command templates from settings.

    Examples:
        >>> # Create a converter for any supported conversion
        >>> converter = ConverterFactory.create_converter(Path("photo.jpg"), "PNG")
        >>> isinstance(converter, Converter)
        True

        >>> # Create a converter for cross-format conversion
        >>> converter = ConverterFactory.create_converter(Path("document.pdf"), "JPEG")
        >>> isinstance(converter, Converter)
        True
    """

    @staticmethod
    def create_converter(
        file: Path,
        target_format: str,
        batch_mode: bool = False,
        output_dir: Optional[Path] = None,
        **kwargs,
    ) -> Optional[Converter]:
        """Create the appropriate converter for the given file and target format.

        Factory method that creates a converter instance based on the
        source file format and target format. Handles compound extensions
        like .tar.bz2 properly.

        Args:
            file: Path to the source file to be converted.
            target_format: Target format string (case-insensitive).
            batch_mode: Whether the converter will be used in batch mode,
                       which suppresses individual progress dialogs.
            output_dir: Optional output directory for converted files in batch mode.
            **kwargs: Additional arguments passed to the converter constructor.

        Returns:
            Optional[Converter]: Converter instance for the conversion,
                               or None if the conversion is not supported.

        Note:
            All conversions use the same Converter class with template-based
            command building from settings.

        Examples:
            >>> converter = ConverterFactory.create_converter(Path("video.mp4"), "AVI")
            >>> converter is not None
            True
        """
        source_format = FileValidator.get_file_format(file)
        target_format = target_format.upper()

        logger.debug(
            "Creating converter for {} -> {} (batch_mode={}, output_dir={})",
            f"{source_format} file",
            target_format,
            batch_mode,
            output_dir,
        )

        if not format_config.get_conversion_rule(
            source_format, target_format
        ) and not format_config.get_default_converter_type(
            source_format, target_format
        ):
            logger.debug(
                "No conversion available for {} -> {}", source_format, target_format
            )
            return None

        logger.debug("Using Converter for {} -> {}", source_format, target_format)
        return Converter(
            file,
            target_format,
            batch_mode=batch_mode,
            output_dir=output_dir,
            **kwargs,
        )
