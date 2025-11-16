#!/usr/bin/python3
"""
Enhanced format configuration system.

This module provides a comprehensive format management system that handles:
- Format groups and their relationships (IMAGE, VIDEO, AUDIO, DOCUMENT, ARCHIVE)
- Conversion rules and special cross-format conversions
- Default converter selection based on format compatibility
- Format alias resolution and canonical format handling
- Intelligent conversion path finding with restrictions
"""

import contextlib
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from utils.logging import logger

from .settings import settings_manager
from .types import ConversionRule, ConverterType, FormatGroup


class FormatConfiguration:
    """Enhanced format configuration system for file conversions.

    This class manages the complex relationships between file formats, conversion
    rules, and converter selection. It provides intelligent format detection,
    alias resolution, and conversion path finding while respecting output
    restrictions and user-defined special rules.

    The system organizes formats into groups (IMAGE, VIDEO, AUDIO, DOCUMENT, ARCHIVE)
    and handles both standard intra-group conversions and special cross-group
    conversions defined in settings.

    Attributes:
        _format_groups: Dictionary mapping group names to FormatGroup objects.
        _conversion_rules: List of special ConversionRule objects from settings.
        _format_to_group: Dictionary mapping format names to their group names.

    Examples:
        >>> config = FormatConfiguration()
        >>> config.get_format_group("JPEG")
        'IMAGE'
        >>> config.get_available_formats("JPEG")
        ('PNG', 'BMP', 'TIFF', 'WebP')
    """

    def __init__(self) -> None:
        """Initialize the format configuration system.

        Loads format groups, special conversion rules from settings, and builds
        internal mappings for efficient format lookups and conversions.

        Returns:
            None
        """
        logger.debug("Initializing format configuration system")
        self._format_groups = self._initialize_format_groups()
        self._conversion_rules = self._setup_special_rules()
        self._format_to_group = self._build_format_mapping()
        logger.debug(
            "Format configuration initialized with {} groups and {} special rules",
            len(self._format_groups),
            len(self._conversion_rules),
        )

    @staticmethod
    @lru_cache(maxsize=128)
    def get_canonical_format(format_name: str) -> str:
        """Get the canonical format name, resolving aliases.

        Converts format aliases to their canonical representations
        (e.g., "JPG" → "JPEG", "TIF" → "TIFF").

        Args:
            format_name: Format name to resolve (case-insensitive).

        Returns:
            str: Canonical format name in uppercase.

        Examples:
            >>> FormatConfiguration.get_canonical_format("jpg")
            'JPEG'
            >>> FormatConfiguration.get_canonical_format("tif")
            'TIFF'
        """
        format_upper = format_name.upper()
        canonical = settings_manager.get("format_aliases", {}).get(
            format_upper, format_upper
        )
        if canonical != format_upper:
            logger.debug("Resolved format alias: {} -> {}", format_upper, canonical)
        return canonical

    @staticmethod
    def normalize_format_set(formats: set) -> set:
        """Normalize a set of formats to use only canonical names.

        Removes format aliases and ensures all formats use their canonical
        representations, preventing duplicates like having both "JPG" and "JPEG".

        Args:
            formats: Set of format names to normalize.

        Returns:
            set: Set containing only canonical format names.

        Examples:
            >>> formats = {"JPG", "JPEG", "PNG"}
            >>> FormatConfiguration.normalize_format_set(formats)
            {'JPEG', 'PNG'}
        """
        return {FormatConfiguration.get_canonical_format(fmt) for fmt in formats}

    def _initialize_format_groups(self) -> Dict[str, FormatGroup]:
        """Initialize format groups with comprehensive format support.

        Creates FormatGroup objects for each media type (IMAGE, VIDEO, AUDIO,
        OFFICE, SPREADSHEET, PRESENTATION, MARKUP, DATA, ARCHIVE) with their
        supported formats, default converters, and recommended target formats.

        Returns:
            Dict[str, FormatGroup]: Dictionary mapping group names to FormatGroup objects.
        """
        return {
            "ARCHIVE": FormatGroup(
                name="ARCHIVE",
                formats={
                    "7Z",
                    "DEB",
                    "DMG",
                    "ISO",
                    "RAR",
                    "RPM",
                    "TAR",
                    "TAR.BZ2",
                    "TAR.GZ",
                    "TAR.LZMA",
                    "TAR.LZO",
                    "TAR.XZ",
                    "TGZ",
                    "ZIP",
                },
                default_converter=ConverterType.ARCHIVE,
                default_formats=settings_manager.get_default_formats("ARCHIVE"),
            ),
            "AUDIO": FormatGroup(
                name="AUDIO",
                formats={
                    "AAC",
                    "AC3",
                    "AIFF",
                    "ALAC",
                    "CAF",
                    "FLAC",
                    "M4A",
                    "MKA",
                    "MP3",
                    "OGG",
                    "OPUS",
                    "WAV",
                    "WMA",
                },
                default_converter=ConverterType.AUDIO,
                default_formats=settings_manager.get_default_formats("AUDIO"),
            ),
            "DATA": FormatGroup(
                name="DATA",
                formats={
                    "JSON",
                    "TXT",
                    "YAML",
                    "YML",
                },
                default_converter=ConverterType.DATA,
                default_formats=settings_manager.get_default_formats("DATA"),
            ),
            "IMAGE": FormatGroup(
                name="IMAGE",
                formats={
                    "AVIF",
                    "BMP",
                    "CR2",
                    "GIF",
                    "HEIC",
                    "HEIF",
                    "ICO",
                    "JPEG",
                    "JPG",
                    "PNG",
                    "RAW",
                    "SVG",
                    "TIF",
                    "TIFF",
                    "WEBP",
                },
                default_converter=ConverterType.IMAGE,
                default_formats=settings_manager.get_default_formats("IMAGE"),
            ),
            "MARKUP": FormatGroup(
                name="MARKUP",
                formats={
                    "HTM",
                    "HTML",
                    "MD",
                    "XML",
                },
                default_converter=ConverterType.MARKUP,
                default_formats=settings_manager.get_default_formats("MARKUP"),
            ),
            "OFFICE": FormatGroup(
                name="OFFICE",
                formats={
                    "DOC",
                    "DOCX",
                    "EPUB",
                    "MOBI",
                    "ODT",
                    "PDF",
                    "RTF",
                },
                default_converter=ConverterType.OFFICE,
                default_formats=settings_manager.get_default_formats("OFFICE"),
            ),
            "PRESENTATION": FormatGroup(
                name="PRESENTATION",
                formats={
                    "ODP",
                    "PPT",
                    "PPTX",
                },
                default_converter=ConverterType.PRESENTATION,
                default_formats=settings_manager.get_default_formats("PRESENTATION"),
            ),
            "SPREADSHEET": FormatGroup(
                name="SPREADSHEET",
                formats={
                    "CSV",
                    "ODS",
                    "XLS",
                    "XLSX",
                },
                default_converter=ConverterType.SPREADSHEET,
                default_formats=settings_manager.get_default_formats("SPREADSHEET"),
            ),
            "VIDEO": FormatGroup(
                name="VIDEO",
                formats={
                    "AVI",
                    "M4V",
                    "MKV",
                    "MOV",
                    "MP4",
                    "MPG",
                    "MPEG",
                    "MTS",
                    "TS",
                    "WEBM",
                    "WMV",
                },
                default_converter=ConverterType.VIDEO,
                default_formats=settings_manager.get_default_formats("VIDEO"),
            ),
        }

    def _setup_special_rules(self) -> List[ConversionRule]:
        """Load special conversion rules from settings.

        Reads special conversion rules from the user's settings.json file and
        converts them to ConversionRule objects. Special rules handle cross-format
        conversions that don't follow standard converter patterns.

        Returns:
            List[ConversionRule]: List of special conversion rules.

        Note:
            Falls back to empty list if settings cannot be loaded.
            Handles both string and list command templates.
        """
        try:
            special_rules_data = settings_manager.get_special_rules()

            conversion_rules = []

            for rule_data in special_rules_data:
                from_format = rule_data.get("from", "").upper()
                to_format = rule_data.get("to", "").upper()
                command_template = rule_data.get("command")
                temp_file_suffix = rule_data.get("temp_file_suffix")

                if not from_format or not to_format or not command_template:
                    continue

                if isinstance(command_template, list):
                    command_template = " && ".join(command_template)

                rule = ConversionRule(
                    from_format=from_format,
                    to_format=to_format,
                    converter_type=ConverterType.SPECIAL,
                    command_template=command_template,
                    temp_file_suffix=temp_file_suffix,
                )

                conversion_rules.append(rule)

            return conversion_rules

        except Exception:
            return []

    def _build_format_mapping(self) -> Dict[str, str]:
        """Build mapping from format names to their group names.

        Creates a lookup dictionary that maps each format to its group
        for efficient format group detection.

        Returns:
            Dict[str, str]: Dictionary mapping uppercase format names to group names.
        """
        mapping = {}
        for group_name, group in self._format_groups.items():
            for format_name in group.formats:
                mapping[format_name.upper()] = group_name
        return mapping

    @lru_cache(maxsize=256)
    def get_format_group(self, file_format: str) -> Optional[str]:
        """Get the group name for a given file format.

        Args:
            file_format: File format name (case-insensitive).

        Returns:
            Optional[str]: Group name ('IMAGE', 'VIDEO', 'AUDIO', 'DOCUMENT', 'ARCHIVE')
                          or None if format is not recognized.

        Examples:
            >>> config.get_format_group("JPEG")
            'IMAGE'
            >>> config.get_format_group("MP4")
            'VIDEO'
        """
        group = self._format_to_group.get(file_format.upper())
        logger.debug("Format group for {}: {}", file_format, group)
        return group

    @lru_cache(maxsize=256)
    def get_available_formats(self, source_format: str) -> Tuple[str, ...]:
        """Get all available target formats for a source format.

        Determines which formats the source format can be converted to,
        including same-group formats and special cross-format conversions.
        Respects output restrictions and user-defined special rules.

        Args:
            source_format: Source file format (case-insensitive).

        Returns:
            Tuple[str, ...]: Sorted tuple of available target format names.

        Note:
            - Excludes output-restricted formats unless user has special rules
            - Returns canonical formats by default (configurable)
            - Excludes the source format itself from results
        """
        logger.debug("Getting available formats for source: {}", source_format)
        source_format = source_format.upper()
        available_formats = set()

        source_group_name = self.get_format_group(source_format)
        if source_group_name:
            source_group = self._format_groups[source_group_name]
            if source_group.internal_conversions:
                available_formats.update(source_group.formats)
                available_formats.discard(source_format)

        for rule in self._conversion_rules:
            if rule.from_format.upper() == source_format:
                available_formats.add(rule.to_format.upper())

        output_restricted_formats = settings_manager.get_output_restricted_formats()

        user_special_rules = settings_manager.get_special_rules()
        user_allowed_targets = {
            rule["to"].upper()
            for rule in user_special_rules
            if rule.get("from", "").upper() == source_format
        }

        formats_to_exclude = output_restricted_formats - user_allowed_targets
        available_formats -= formats_to_exclude

        conversion_exclusions = settings_manager.get("conversion_exclusions", [])
        for exclusion in conversion_exclusions:
            if exclusion.get("from", "").upper() == source_format:
                excluded_target = exclusion.get("to", "").upper()
                if excluded_target not in user_allowed_targets:
                    available_formats.discard(excluded_target)
                    logger.debug(
                        "Excluded conversion: {} -> {} (reason: {})",
                        source_format,
                        excluded_target,
                        exclusion.get("reason", "Not specified"),
                    )

        use_canonical: bool = settings_manager.get("use_canonical_formats", True)
        if not use_canonical:
            result = tuple(sorted(available_formats))
            logger.debug("Available formats (non-canonical): {} formats", len(result))
            return result

        canonical_formats = self.normalize_format_set(available_formats)

        canonical_source = self.get_canonical_format(source_format)
        canonical_formats.discard(canonical_source)

        result = tuple(sorted(canonical_formats))
        logger.debug("Available formats (canonical): {} formats", len(result))
        return result

    def get_conversion_rule(
        self, from_format: str, to_format: str
    ) -> Optional[ConversionRule]:
        """Get a specific conversion rule if it exists.

        Searches for conversion rules between the specified formats,
        checking both user-defined special rules and built-in rules.
        Handles format aliases transparently.

        Args:
            from_format: Source format (case-insensitive).
            to_format: Target format (case-insensitive).

        Returns:
            Optional[ConversionRule]: Conversion rule if found, None otherwise.

        Note:
            Checks user settings first, then built-in rules, then tries
            canonical format aliases if no exact match is found.
        """
        from_format = from_format.upper()
        to_format = to_format.upper()

        with contextlib.suppress(ImportError):
            user_rule = settings_manager.find_special_rule(from_format, to_format)
            if user_rule:
                command_template = user_rule.get("command")
                if isinstance(command_template, list):
                    command_template = " && ".join(command_template)

                return ConversionRule(
                    from_format=from_format,
                    to_format=to_format,
                    converter_type=ConverterType.SPECIAL,
                    command_template=command_template,
                    temp_file_suffix=user_rule.get("temp_file_suffix"),
                )

        exact_rule = next(
            (
                rule
                for rule in self._conversion_rules
                if (
                    rule.from_format.upper() == from_format
                    and rule.to_format.upper() == to_format
                )
            ),
            None,
        )
        if exact_rule:
            return exact_rule

        canonical_from = self.get_canonical_format(from_format)
        canonical_to = self.get_canonical_format(to_format)

        if canonical_from != from_format or canonical_to != to_format:
            with contextlib.suppress(ImportError):
                user_rule = settings_manager.find_special_rule(
                    canonical_from, canonical_to
                )
                if user_rule:
                    command_template = user_rule.get("command")
                    if isinstance(command_template, list):
                        command_template = " && ".join(command_template)

                    return ConversionRule(
                        from_format=from_format,  # Keep original format
                        to_format=to_format,  # Keep original format
                        converter_type=ConverterType.SPECIAL,
                        command_template=command_template,
                        temp_file_suffix=user_rule.get("temp_file_suffix"),
                    )

            canonical_rule = next(
                (
                    rule
                    for rule in self._conversion_rules
                    if (
                        rule.from_format.upper() == canonical_from
                        and rule.to_format.upper() == canonical_to
                    )
                ),
                None,
            )
            if canonical_rule:
                return ConversionRule(
                    from_format=from_format,
                    to_format=to_format,
                    converter_type=canonical_rule.converter_type,
                    command_template=canonical_rule.command_template,
                    temp_file_suffix=canonical_rule.temp_file_suffix,
                )

        return None

    def get_default_converter_type(
        self, from_format: str, to_format: str
    ) -> Optional[ConverterType]:
        """Get the appropriate converter type for a format conversion.

        Determines which converter should handle the conversion based on
        format relationships and available conversion rules.

        Args:
            from_format: Source format (case-insensitive).
            to_format: Target format (case-insensitive).

        Returns:
            Optional[ConverterType]: The appropriate converter type for the conversion,
                                    or None if no suitable converter is found.

        Note:
            Priority: special rule → target format group → source format group → None
        """
        rule = self.get_conversion_rule(from_format, to_format)
        if rule:
            return rule.converter_type

        target_group_name = self.get_format_group(to_format)
        if target_group_name:
            return self._format_groups[target_group_name].default_converter

        source_group_name = self.get_format_group(from_format)
        if source_group_name:
            return self._format_groups[source_group_name].default_converter

        return None

    @lru_cache(maxsize=256)
    def get_default_format(self, source_format: str) -> str:
        """Get the default target format for a source format.

        Returns the recommended target format for conversions from the
        given source format, choosing from the group's default formats.

        Args:
            source_format: Source format (case-insensitive).

        Returns:
            str: Default target format, or empty string if no group found.

        Examples:
            >>> config.get_default_format("JPEG")
            'PNG'
            >>> config.get_default_format("MP4")
            'MKV'
        """
        logger.debug("Getting default format for source: {}", source_format)
        group_name = self.get_format_group(source_format)
        if not group_name:
            logger.debug("No group found for format: {}", source_format)
            return ""

        default_formats = self._format_groups[group_name].default_formats
        source_upper = source_format.upper()

        for fmt in default_formats:
            if fmt != source_upper:
                logger.debug("Default format found: {}", fmt)
                return fmt

        result = default_formats[0] if default_formats else ""
        logger.debug("Default format result: {}", result)
        return result


format_config = FormatConfiguration()
