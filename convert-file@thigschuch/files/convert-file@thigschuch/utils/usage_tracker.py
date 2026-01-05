#!/usr/bin/python3
"""
Usage tracking for format conversions.

This module tracks which format conversions users perform most frequently,
enabling intelligent pre-selection of target formats based on historical usage.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from utils.logging import logger


class UsageTracker:
    """Tracks usage statistics for format conversions.

    Maintains a persistent record of conversion history to enable intelligent
    pre-selection of target formats based on user preferences and habits.

    The tracking data is stored as a JSON file in the user's config directory
    with the structure:
    {
        "SOURCE_FORMAT": {
            "TARGET_FORMAT": usage_count,
            ...
        },
        ...
    }

    Attributes:
        _usage_file: Path to the usage tracking JSON file.
        _usage_data: In-memory cache of usage statistics.

    Examples:
        >>> tracker = UsageTracker()
        >>> tracker.record_conversion("JPEG", "PNG")
        >>> most_used = tracker.get_most_used_format("JPEG")
        >>> print(most_used)
        'PNG'
    """

    def __init__(self) -> None:
        """Initialize the usage tracker.

        Sets up the usage tracking file path and loads existing usage data.

        Returns:
            None
        """
        self._usage_file = (
            Path.home() / ".config" / "convert-file@thigschuch" / "usage_stats.json"
        )
        self._usage_data: Dict[str, Dict[str, int]] = {}
        self._load_usage_data()

    def _load_usage_data(self) -> None:
        """Load usage statistics from the tracking file.

        Reads the usage tracking file and loads data into memory.
        Creates an empty tracking file if it doesn't exist.

        Returns:
            None
        """
        logger.debug("Loading usage statistics from: {}", self._usage_file)
        if not self._usage_file.exists():
            logger.debug("Usage file does not exist, creating new tracking file")
            self._usage_data = {}
            self._save_usage_data()
            return

        try:
            with open(self._usage_file, "r", encoding="utf-8") as file:
                self._usage_data = json.load(file)
            logger.debug(
                "Usage statistics loaded successfully: {} source formats tracked",
                len(self._usage_data),
            )
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load usage statistics: {}", str(e))
            self._usage_data = {}

    def _save_usage_data(self) -> None:
        """Save usage statistics to the tracking file.

        Writes the current usage data to disk, creating directories if needed.

        Returns:
            None
        """
        logger.debug("Saving usage statistics to: {}", self._usage_file)
        try:
            self._usage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._usage_file, "w", encoding="utf-8") as file:
                json.dump(self._usage_data, file, indent=2)
            logger.debug("Usage statistics saved successfully")
        except IOError as e:
            logger.error("Failed to save usage statistics: {}", str(e))

    def record_conversion(self, source_format: str, target_format: str) -> None:
        """Record a conversion in the usage statistics.

        Increments the usage count for the given source→target conversion pair.

        Args:
            source_format: Source format of the conversion (case-insensitive).
            target_format: Target format of the conversion (case-insensitive).

        Returns:
            None

        Examples:
            >>> tracker.record_conversion("JPEG", "PNG")
            >>> tracker.record_conversion("JPEG", "PNG")  # Second conversion
        """
        source_upper = source_format.upper()
        target_upper = target_format.upper()

        logger.debug("Recording conversion: {} -> {}", source_upper, target_upper)

        if source_upper not in self._usage_data:
            self._usage_data[source_upper] = {}

        current_count = self._usage_data[source_upper].get(target_upper, 0)
        self._usage_data[source_upper][target_upper] = current_count + 1

        logger.debug(
            "Conversion count updated: {} -> {} = {}",
            source_upper,
            target_upper,
            current_count + 1,
        )

        self._save_usage_data()

    def get_most_used_format(self, source_format: str) -> Optional[str]:
        """Get the most frequently used target format for a source format.

        Analyzes usage history to determine which target format is most
        commonly used when converting from the given source format.

        Args:
            source_format: Source format to look up (case-insensitive).

        Returns:
            Optional[str]: Most frequently used target format, or None if
                          no usage history exists for the source format.

        Examples:
            >>> tracker.record_conversion("JPEG", "PNG")
            >>> tracker.record_conversion("JPEG", "PNG")
            >>> tracker.record_conversion("JPEG", "WEBP")
            >>> tracker.get_most_used_format("JPEG")
            'PNG'
        """
        source_upper = source_format.upper()
        logger.debug("Looking up most used format for source: {}", source_upper)

        if source_upper not in self._usage_data:
            logger.debug("No usage history found for format: {}", source_upper)
            return None

        target_stats = self._usage_data[source_upper]
        if not target_stats:
            logger.debug("Empty usage history for format: {}", source_upper)
            return None

        most_used = max(target_stats.items(), key=lambda x: x[1])[0]
        logger.debug(
            "Most used format for {}: {} ({} conversions)",
            source_upper,
            most_used,
            target_stats[most_used],
        )
        return most_used

    def get_usage_count(self, source_format: str, target_format: str) -> int:
        """Get the usage count for a specific conversion pair.

        Returns how many times the given source→target conversion has been
        performed according to tracked usage history.

        Args:
            source_format: Source format (case-insensitive).
            target_format: Target format (case-insensitive).

        Returns:
            int: Number of times this conversion has been performed (0 if never).

        Examples:
            >>> tracker.record_conversion("JPEG", "PNG")
            >>> count = tracker.get_usage_count("JPEG", "PNG")
            >>> print(count)
            1
        """
        source_upper = source_format.upper()
        target_upper = target_format.upper()

        count = self._usage_data.get(source_upper, {}).get(target_upper, 0)
        logger.debug("Usage count for {} -> {}: {}", source_upper, target_upper, count)
        return count


usage_tracker = UsageTracker()
