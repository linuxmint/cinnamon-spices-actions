#!/usr/bin/python3
"""
Type definitions for converter system.

This module defines enums and data classes used throughout
the converter system for type safety and clear interfaces.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set


class ConverterType(Enum):
    """Enumeration of converter template categories.
    
    These types determine which command template section to load from settings.json
    for the conversion. All conversions use the same Converter class but with
    different template-based commands.
    """

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OFFICE = "office"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    MARKUP = "markup"
    DATA = "data"
    ARCHIVE = "archive"
    SPECIAL = "special"


@dataclass
class ConversionRule:
    """
    Represents a specific conversion rule.

    Conversion rules define special cross-format conversions with custom
    command templates. All rules use the unified Converter class with
    template-based command building.

    Attributes:
        from_format: Source format (e.g., "GIF")
        to_format: Target format (e.g., "MP4")
        converter_type: Template category to use (determines which settings section)
        command_template: Custom command template (optional)
        temp_file_suffix: Extension for temporary files (optional)
    """

    from_format: str
    to_format: str
    converter_type: ConverterType
    command_template: Optional[str] = None
    temp_file_suffix: Optional[str] = None

    def __post_init__(self) -> None:
        """Normalize format names to uppercase."""
        self.from_format = self.from_format.upper()
        self.to_format = self.to_format.upper()


@dataclass
class FormatGroup:
    """
    Represents a group of related formats.

    Format groups define collections of file formats that can typically
    be converted between each other. All use the unified Converter class
    with templates determined by the default_converter type.

    Attributes:
        name: Group name (e.g., "IMAGE", "VIDEO")
        formats: Set of formats in this group
        default_converter: Template category for this group (determines which settings section)
        default_formats: List of the 3 most common target formats in priority order
        internal_conversions: Whether formats in this group can convert to each other
    """

    name: str
    formats: Set[str]
    default_converter: ConverterType
    default_formats: List[str]
    internal_conversions: bool = True

    def __post_init__(self) -> None:
        """Normalize format names to uppercase."""
        self.formats = {fmt.upper() for fmt in self.formats}
        self.default_formats = [fmt.upper() for fmt in self.default_formats]
